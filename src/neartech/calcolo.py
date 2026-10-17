"""Calcolo deterministico di N e D (fase 4; piano, "Come si calcolano i risultati"; metodo, sezione 17).

Formule del piano:
  g_k = max(0, d_k - c_k) / 4                         divario per dimensione (k1, k2, k3)
  N   = min(1, Σ w_k g_k (1 + λ r/4))                 pesi e λ del profilo approvato
  D   = Σ w_j d_j / 4 sulle componenti disponibili, con i pesi riportati a somma 1 (oggi d1 e d2: provvisorio)
  quadrante: N alto se N ≥ θ_N, D alto se D ≥ θ_D; Q1 alto/alto, Q2 N alto D basso, Q3 N basso D alto, Q4 basso/basso

Simulazione: per ogni occorrenza, estrazioni ripetute dai giudizi registrati (quelli di persone al posto di quelli
del modello, quelli sull'occorrenza al posto di quelli sul task) e dalla copertura, uniforme fra c_low e c_high.
Ogni voce si estrae a sé (metodo, sezione 17). Seme fisso derivato dal seme del calcolo e dall'occorrenza:
stesso input, stesso risultato. I giudizi su task poi fusi valgono per il superstite (metodo, sezione 8); di una
persona conta l'ultimo giudizio su ogni voce (una correzione non si somma alla precedente).
Con la copertura uniforme fra c_low e c_high, la media pesata dello snapshot (c_mean) è informativa: non entra in N.
L'aritmetica la fa solo questo codice; pesi, λ e soglie vengono dal profilo, mai da qui.
"""

import hashlib
import json
import random
import statistics
import uuid
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from neartech.permessi import richiedi

VERSIONE_CALCOLO = "calcolo-nd-v1"
ESTRAZIONI = 2000  # dal piano: numero di simulazioni, non una soglia
K_ITEMS = ("k1", "k2", "k3")
D_ITEMS = ("d1", "d2", "d3", "d4")
VALUTATORI_PERSONE = ("expert", "worker", "beneficiary")


@dataclass(frozen=True)
class Profilo:
    profilo_id: str
    w_k: dict[str, float]
    lambda_r: float
    w_d: dict[str, float]
    theta_n: float
    theta_d: float


@dataclass(frozen=True)
class Risultato:
    n_media: float | None
    n_dev: float | None
    d_media: float | None
    d_dev: float | None
    p_quadranti: dict[str, float] | None
    componenti_d: tuple[str, ...]
    provvisorio: bool


# --- formule -------------------------------------------------------------------------

def n_puntuale(domanda: dict[str, float], copertura: dict[str, float], r: float, profilo: Profilo) -> float:
    divario = sum(profilo.w_k[k] * max(0.0, domanda[k] - copertura[k]) / 4 for k in K_ITEMS)
    return min(1.0, divario * (1 + profilo.lambda_r * r / 4))


def d_puntuale(componenti: dict[str, float], profilo: Profilo) -> tuple[float | None, tuple[str, ...]]:
    usate = tuple(j for j in D_ITEMS if j in componenti)
    peso = sum(profilo.w_d[j] for j in usate)
    if not usate or peso == 0:
        return None, ()
    return sum(profilo.w_d[j] / peso * componenti[j] for j in usate) / 4, usate


def quadrante(n: float, d: float, theta_n: float, theta_d: float) -> str:
    # Arrotondamento a 9 decimali prima del confronto: un errore di virgola mobile non sposta il quadrante.
    n_alto, d_alto = round(n, 9) >= round(theta_n, 9), round(d, 9) >= round(theta_d, 9)
    if n_alto:
        return "q1" if d_alto else "q2"
    return "q3" if d_alto else "q4"


def simula(
    giudizi: dict[str, list[float]], copertura: dict[str, tuple[float, float]] | None, profilo: Profilo, *,
    estrazioni: int, seme: int,
) -> Risultato:
    """Monte Carlo deterministico. giudizi: valori registrati per voce; copertura: (c_low, c_high) per dimensione,
    o None se lo snapshot non copre il task. Senza copertura o senza k1, k2, k3, r: N vuoto."""
    if estrazioni < 1:
        raise ValueError("servono estrazioni positive")
    rng = random.Random(seme)
    con_n = copertura is not None and all(k in copertura for k in K_ITEMS) and all(
        giudizi.get(v) for v in (*K_ITEMS, "r"))
    voci_d = [j for j in D_ITEMS if giudizi.get(j)]
    valori_n, valori_d, conteggi = [], [], {"q1": 0, "q2": 0, "q3": 0, "q4": 0}
    componenti: tuple[str, ...] = ()
    for _ in range(estrazioni):
        estratti = {voce: rng.choice(giudizi[voce]) for voce in sorted(giudizi) if giudizi[voce]}
        n = None
        if con_n:
            c = {k: rng.uniform(*copertura[k]) for k in K_ITEMS}
            n = n_puntuale({k: estratti[k] for k in K_ITEMS}, c, estratti["r"], profilo)
            valori_n.append(n)
        d, componenti = d_puntuale({j: estratti[j] for j in voci_d}, profilo)
        if d is not None:
            valori_d.append(d)
        if n is not None and d is not None:
            conteggi[quadrante(n, d, profilo.theta_n, profilo.theta_d)] += 1
    return Risultato(
        n_media=statistics.fmean(valori_n) if valori_n else None,
        n_dev=statistics.pstdev(valori_n) if valori_n else None,
        d_media=statistics.fmean(valori_d) if valori_d else None,
        d_dev=statistics.pstdev(valori_d) if valori_d else None,
        p_quadranti={q: c / estrazioni for q, c in conteggi.items()} if valori_n and valori_d else None,
        componenti_d=componenti,
        provvisorio=componenti != D_ITEMS,
    )


# --- calcolo per un'organizzazione ---------------------------------------------

def _configurazione(conn: psycopg.Connection, org_id: str) -> tuple[str, Profilo, str, str]:
    rubrica = conn.execute(
        "SELECT version FROM rubric_versions WHERE is_current AND approved_by IS NOT NULL").fetchone()
    if rubrica is None:
        raise LookupError("nessuna rubrica corrente approvata")
    riga = conn.execute(
        """SELECT profile_id, w_k1, w_k2, w_k3, lambda_r, w_d1, w_d2, w_d3, w_d4, theta_n, theta_d
           FROM weight_profiles WHERE is_active AND approved_by IS NOT NULL
             AND (org_id = %(org)s OR (org_id IS NULL AND NOT EXISTS (
                  SELECT 1 FROM weight_profiles w WHERE w.org_id = %(org)s AND w.is_active)))""",
        {"org": org_id},
    ).fetchone()
    if riga is None:
        raise LookupError("nessun profilo di pesi attivo e approvato per l'organizzazione")
    v = [float(x) for x in riga[1:]]
    profilo = Profilo(riga[0], w_k=dict(zip(K_ITEMS, v[0:3])), lambda_r=v[3], w_d=dict(zip(D_ITEMS, v[4:8])),
                      theta_n=v[8], theta_d=v[9])
    snapshot = conn.execute(
        "SELECT snapshot_id, tipo_capacita FROM capability_snapshots WHERE status = 'published' "
        "AND approved_by IS NOT NULL FOR SHARE").fetchone()
    if snapshot is None:
        raise LookupError("nessuno snapshot di capacità pubblicato e approvato")
    return rubrica[0], profilo, str(snapshot[0]), snapshot[1]


def _giudizi(conn: psycopg.Connection, rubrica: str, task_id: str, occorrenza_id: str
             ) -> tuple[dict[str, list[float]], dict[str, list[str]], list[str]]:
    """Per ogni voce il gruppo di giudizi che vale: persone sull'occorrenza, persone sul task, modello
    sull'occorrenza, modello sul task. Sul task contano anche i giudizi dei task fusi in esso. Di ogni persona
    conta l'ultimo giudizio sulla voce. Ritorna valori, valutatori e identificativi usati."""
    righe = conn.execute(
        """WITH RECURSIVE fusi(task_id) AS (
             SELECT %(task)s::uuid
             UNION SELECT t.task_id FROM canonical_tasks t JOIN fusi f ON t.merged_into = f.task_id)
           SELECT run_id, target_kind, item, value, rater_kind, rater_ref, created_at FROM assessment_runs
           WHERE rubric_version = %(rubrica)s
             AND ((target_kind = 'task' AND target_id IN (SELECT task_id FROM fusi))
                  OR (target_kind = 'occurrence' AND target_id = %(occorrenza)s))
           ORDER BY run_id""",
        {"rubrica": rubrica, "task": task_id, "occorrenza": occorrenza_id},
    ).fetchall()
    valori: dict[str, list[float]] = {}
    valutatori: dict[str, list[str]] = {}
    usati: list[str] = []
    for voce in (*K_ITEMS, "r", *D_ITEMS):
        for persone, bersaglio in ((True, "occurrence"), (True, "task"), (False, "occurrence"), (False, "task")):
            gruppo = [r for r in righe if r[2] == voce and r[1] == bersaglio
                      and (r[4] in VALUTATORI_PERSONE) == persone]
            if persone:  # una persona che corregge un giudizio lo sostituisce
                ultimi: dict[str, tuple] = {}
                for r in sorted(gruppo, key=lambda r: (r[6], str(r[0]))):
                    ultimi[r[5]] = r
                gruppo = sorted(ultimi.values(), key=lambda r: str(r[0]))
            if gruppo:
                valori[voce] = [float(r[3]) for r in gruppo]
                valutatori[voce] = [r[4] for r in gruppo]
                usati += [str(r[0]) for r in gruppo]
                break
    return valori, valutatori, usati


def _fonti_d(valutatori: dict[str, list[str]], componenti: tuple[str, ...], profilo: Profilo) -> dict[str, float]:
    peso = sum(profilo.w_d[j] for j in componenti)
    fonti: dict[str, float] = {}
    for j in componenti:
        for valutatore in valutatori[j]:
            fonti[valutatore] = fonti.get(valutatore, 0.0) + profilo.w_d[j] / peso / len(valutatori[j])
    return {k: round(v, 4) for k, v in sorted(fonti.items())}


def _arrotonda(x: float | None) -> float | None:
    return None if x is None else round(x, 3)


def calcola_organizzazione(
    conn: psycopg.Connection, utente_id: str, org_id: str, *, seme: int, estrazioni: int = ESTRAZIONI
) -> dict[str, int]:
    """Calcola N e D per tutte le occorrenze dell'organizzazione con la configurazione approvata vigente.
    Un risultato con lo stesso input esiste già: nessuna riga nuova. Ritorna i conteggi."""
    if not 0 <= seme < 2**63:
        raise ValueError("il seme deve stare fra 0 e 2^63 - 1")
    if estrazioni < 1:
        raise ValueError("servono estrazioni positive")
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_parametri_tecnici", org_id, risorsa=f"calcolo:{org_id}")
        rubrica, profilo, snapshot, tipo_capacita = _configurazione(conn, org_id)
        occorrenze = conn.execute(
            """SELECT o.occurrence_id, o.task_id, o.role_id FROM task_occurrences o JOIN roles r USING (role_id)
               WHERE r.org_id = %s ORDER BY o.occurrence_id""",
            (org_id,),
        ).fetchall()
        esito = {"occorrenze": len(occorrenze), "nuove": 0, "senza_n": 0, "senza_d": 0}
        for occorrenza_id, task_id, ruolo_id in occorrenze:
            occorrenza_id, task_id = str(occorrenza_id), str(task_id)
            valori, valutatori, usati = _giudizi(conn, rubrica, task_id, occorrenza_id)
            righe_c = conn.execute(
                "SELECT dimension, c_low, c_high FROM task_capability WHERE snapshot_id = %s AND task_id = %s",
                (snapshot, task_id),
            ).fetchall()
            copertura = {r[0]: (float(r[1]), float(r[2])) for r in righe_c}
            copertura = copertura if all(k in copertura for k in K_ITEMS) else None
            seme_occorrenza = int(hashlib.sha256(f"{seme}:{occorrenza_id}".encode()).hexdigest()[:15], 16)
            r = simula(valori, copertura, profilo, estrazioni=estrazioni, seme=seme_occorrenza)
            # L'impronta cambia con ogni input: giudizi usati, copertura, valori del profilo, snapshot, rubrica.
            impronta = hashlib.sha256(json.dumps(
                {"giudizi": sorted(usati), "copertura": sorted((k, v) for k, v in (copertura or {}).items()),
                 "profilo": [profilo.profilo_id, profilo.w_k, profilo.lambda_r, profilo.w_d, profilo.theta_n,
                             profilo.theta_d],
                 "snapshot": [snapshot, tipo_capacita], "rubrica": rubrica, "task": task_id, "ruolo": str(ruolo_id)},
                sort_keys=True).encode()).hexdigest()
            fonti: dict[str, Any] = {
                "fonti": _fonti_d(valutatori, r.componenti_d, profilo) if r.d_media is not None else {},
                "componenti": list(r.componenti_d),
                "mancanti": [j for j in D_ITEMS if j not in r.componenti_d],
                "provvisorio": r.provvisorio,
                "giudizi": {voce: len(v) for voce, v in sorted(valori.items())},  # quanti giudizi per voce
            }
            q = r.p_quadranti or {}
            esito["nuove"] += conn.execute(
                """INSERT INTO policy_estimates
                     (occurrence_id, task_id, role_id, profile_id, snapshot_id, rubric_version, n_mean, n_sd, d_mean,
                      d_sd, p_q1, p_q2, p_q3, p_q4, d_source_mix, versione_calcolo, seme, estrazioni, tipo_capacita,
                      componenti_d, d_provvisorio, impronta_input, calcolata_da)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                           %s)
                   ON CONFLICT DO NOTHING""",
                (occorrenza_id, task_id, ruolo_id, profilo.profilo_id, snapshot, rubrica, _arrotonda(r.n_media),
                 _arrotonda(r.n_dev),
                 _arrotonda(r.d_media), _arrotonda(r.d_dev), _arrotonda(q.get("q1")), _arrotonda(q.get("q2")),
                 _arrotonda(q.get("q3")), _arrotonda(q.get("q4")), Jsonb(fonti), VERSIONE_CALCOLO, seme, estrazioni,
                 tipo_capacita if r.n_media is not None else None, list(r.componenti_d), r.provvisorio, impronta,
                 utente_id),
            ).rowcount
            esito["senza_n"] += r.n_media is None
            esito["senza_d"] += r.d_media is None
        return esito
