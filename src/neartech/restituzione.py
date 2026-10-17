"""Restituzione dei risultati a un'organizzazione (fase 5; registro di metodo, sezione 24).

Una lettura per organizzazione e per ruolo dei risultati vigenti (v_risultati_vigenti, v_role_metrics):
- le chiavi dei risultati (rubrica, profilo di pesi e sue soglie, snapshot e metodo, versione del calcolo,
  componenti di D, modelli dei giudizi usati);
- le ragioni per cui i risultati sono provvisori (avvertenze);
- la distribuzione per quadrante più probabile, per l'organizzazione e per ruolo;
- la coda delle occorrenze da rivedere, dalla meno certa, se la soglia di stabilità è approvata;
- (dalla v2) ogni occorrenza con il suo risultato, per la mappa dei quadranti della piattaforma: il comitato
  approva esattamente ciò che vede.

La soglia di stabilità non sta nel codice: è il parametro di governance soglia_stabilita_quadrante. Senza un
valore approvato la coda non si calcola e la restituzione lo dice.
Il comitato guida approva una restituzione con un atto del registro che ne cita l'impronta; una restituzione
superata (i risultati sono cambiati dopo la lettura) non si approva.

La lettura prende lo stesso lock del calcolo (BLOCCO): non vede mai un calcolo a metà, e un calcolo non
cambia i risultati fra il controllo e l'atto di approvazione.

Nessun output riguarda una persona: i risultati sono per task e per ruolo, e i valutatori persona non vi
compaiono. La restituzione contiene testo dell'organizzazione (nomi dei ruoli) e si conserva fuori dal
repository.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg import sql

from neartech.calcolo import VALUTATORI_PERSONE
from neartech.governance import DecisioneGiaPresa, ParametroAssente, parametro_vigente
from neartech.permessi import richiedi
from neartech.registro import registra, spazio

VERSIONE_RESTITUZIONE = "restituzione-v2"  # v2: elenco delle occorrenze (fase 6)
PARAMETRO_STABILITA = "soglia_stabilita_quadrante"
QUADRANTI = ("q1", "q2", "q3", "q4")
BLOCCO = "risultati:{org}"  # lock condiviso con neartech.calcolo.calcola_organizzazione
_INDICE_APPROVAZIONE = "registro_una_approvazione_restituzione"  # migrazione 0036

NOTA = ("Nessun output riguarda una persona: i risultati sono per task e per ruolo, e non valutano chi "
        "svolge il ruolo.")

# Codice dell'avvertenza -> spiegazione. L'ordine è quello di stampa.
AVVERTENZE = {
    "nessun_risultato": "Nessuna occorrenza ha un risultato con la configurazione vigente.",
    "occorrenze_senza_risultato": "Alcune occorrenze non hanno un risultato con N e D (giudizi o copertura "
                                  "mancanti, o task non più attivo): non entrano nei conteggi.",
    "capacita_di_riserva": "La capacità dell'IA è la copertura di riserva, stimata senza test sul campo: "
                           "N è provvisorio.",
    "d_provvisorio": "D è calcolato senza tutte le sue componenti (vedi le chiavi): i pesi delle componenti "
                     "presenti sono riportati a somma uno.",
    "pesi_uguali": "Senza le quote di tempo, ogni task di un ruolo pesa uguale nel baricentro.",
    "soglia_di_stabilita_non_approvata": "La soglia di stabilità del quadrante non è approvata: la coda "
                                          "delle occorrenze da rivedere non si calcola.",
    "soglia_comune_non_adottata": "La soglia di stabilità è il valore comune, non ancora adottato dal "
                                  "comitato guida dell'organizzazione.",
    "modelli_dedotti": "Per i risultati calcolati prima della registrazione dei giudizi usati, i modelli "
                       "sono quelli con giudizi registrati prima del calcolo.",
    "ruoli_senza_nome": "Alcuni ruoli non hanno il nome nello spazio dell'organizzazione.",
}


class RestituzioneSuperata(RuntimeError):
    """I risultati o la configurazione sono cambiati dopo la lettura della restituzione."""


def _numero(valore: Any) -> float | None:
    return None if valore is None else float(valore)


def _quadrante(riga: dict[str, Any]) -> tuple[str, float, bool]:
    """Quadrante più probabile, la sua probabilità e se un altro quadrante è a pari probabilità.
    A pari probabilità vale l'ordine q1, q2, q3, q4 (come GREATEST nella stabilità del ruolo)."""
    probabilita = {q: float(riga[f"p_{q}"]) for q in QUADRANTI}
    migliore = max(QUADRANTI, key=lambda q: (probabilita[q], -QUADRANTI.index(q)))
    pari = sum(p == probabilita[migliore] for p in probabilita.values()) > 1
    return migliore, probabilita[migliore], pari


def _soglia(conn: psycopg.Connection, org_id: str) -> dict[str, Any] | None:
    try:
        parametro = parametro_vigente(conn, PARAMETRO_STABILITA, org_id)
    except ParametroAssente:  # anche ritirato e non sostituito
        return None
    valore = parametro.valore.get("valore") if isinstance(parametro.valore, dict) else None
    if isinstance(valore, bool) or not isinstance(valore, (int, float)) or not 0 < valore <= 1:
        raise ValueError(f"valore non ammesso per {PARAMETRO_STABILITA} (parametro {parametro.parametro_id}, "
                         f"versione {parametro.versione}): {valore!r}")
    return {"valore": float(valore), "parametro_id": parametro.parametro_id, "versione": parametro.versione,
            "comune": parametro.org_id is None, "adozione_id": parametro.adozione_id}


def _righe(conn: psycopg.Connection, query: sql.Composable | str, parametri: Any) -> list[dict[str, Any]]:
    cursore = conn.execute(query, parametri)
    nomi = [c.name for c in cursore.description]
    return [dict(zip(nomi, r)) for r in cursore.fetchall()]


def _contenuto(restituzione: dict[str, Any]) -> dict[str, Any]:
    """La parte della restituzione coperta dall'impronta: tutto tranne impronta, data e approvazione."""
    return {k: v for k, v in restituzione.items() if k not in ("impronta", "generato_il", "approvazione")}


def impronta_restituzione(restituzione: dict[str, Any]) -> str:
    testo = json.dumps(_contenuto(restituzione), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(testo.encode("utf-8")).hexdigest()


def _approvazione(conn: psycopg.Connection, org_id: str, impronta: str) -> int | None:
    riga = conn.execute(
        """SELECT decisione_id FROM registro_decisioni
           WHERE tipo_oggetto = 'restituzione' AND atto = 'approvazione' AND org_id = %s AND oggetto_id = %s""",
        (org_id, impronta),
    ).fetchone()
    return None if riga is None else riga[0]


def _modelli(conn: psycopg.Connection, risultati: list[dict[str, Any]]) -> tuple[list[str], bool]:
    """Modelli dei giudizi usati dai risultati. Per i risultati senza giudizi registrati (calcolati prima della
    migrazione 0036) quelli con giudizi sul task (anche fuso) o sull'occorrenza registrati prima del calcolo.
    Ritorna i modelli e se una parte è dedotta."""
    persone = list(VALUTATORI_PERSONE)
    usati = sorted({str(g) for r in risultati for g in (r["giudizi_usati"] or [])})
    modelli = {m for (m,) in conn.execute(
        "SELECT DISTINCT rater_ref FROM assessment_runs WHERE run_id = ANY(%s::uuid[]) AND rater_kind <> ALL(%s)",
        (usati, persone)).fetchall()}
    senza = [r for r in risultati if r["giudizi_usati"] is None]
    if senza:
        modelli |= {m for (m,) in conn.execute(
            """WITH RECURSIVE base AS (
                 SELECT * FROM unnest(%s::uuid[], %s::uuid[], %s::timestamptz[], %s::text[])
                   AS b(occorrenza, task, quando, rubrica)),
               fusi(radice, task_id) AS (
                 SELECT DISTINCT task, task FROM base
                 UNION SELECT f.radice, t.task_id FROM canonical_tasks t JOIN fusi f ON t.merged_into = f.task_id)
               SELECT DISTINCT a.rater_ref FROM base b
               JOIN assessment_runs a ON a.rubric_version = b.rubrica AND a.created_at <= b.quando
                 AND a.rater_kind <> ALL(%s)
                 AND ((a.target_kind = 'task'
                       AND a.target_id IN (SELECT f.task_id FROM fusi f WHERE f.radice = b.task))
                      OR (a.target_kind = 'occurrence' AND a.target_id = b.occorrenza))""",
            ([r["occurrence_id"] for r in senza], [r["task_id"] for r in senza], [r["computed_at"] for r in senza],
             [r["rubric_version"] for r in senza], persone)).fetchall()}
    return sorted(modelli), bool(senza)


def _chiavi(conn: psycopg.Connection, risultati: list[dict[str, Any]]) -> tuple[dict[str, Any], bool]:
    snapshot = sorted({str(r["snapshot_id"]) for r in risultati})
    profili = sorted({r["profile_id"] for r in risultati})
    soglie = conn.execute(
        "SELECT profile_id, theta_n, theta_d FROM weight_profiles WHERE profile_id = ANY(%s)", (profili,)
    ).fetchall()
    modelli, dedotti = _modelli(conn, risultati)
    return {
        "rubriche": sorted({r["rubric_version"] for r in risultati}),
        "profili": profili,
        # Soglie dei quadranti dei profili: N alto se N >= theta_n, D alto se D >= theta_d.
        "soglie_quadranti": sorted(
            ({"profilo": p, "theta_n": float(n), "theta_d": float(d)} for p, n, d in soglie),
            key=lambda s: s["profilo"]),
        "snapshot": snapshot,
        "metodi_capacita": sorted({m for (m,) in conn.execute(
            "SELECT method_version FROM capability_snapshots WHERE snapshot_id = ANY(%s::uuid[])",
            (snapshot,)).fetchall()}),
        "versioni_calcolo": sorted({r["versione_calcolo"] for r in risultati}),
        "capacita": sorted({r["tipo_capacita"] for r in risultati}),
        "componenti_d": sorted({c for r in risultati for c in r["componenti_d"]}),
        "modelli_giudizi": modelli,
    }, dedotti


def _costruisci(conn: psycopg.Connection, org_id: str, *, esclusivo: bool = False) -> dict[str, Any]:
    """Restituzione senza controllo dei permessi: chi chiama li ha già controllati. Chi legge prende il lock in
    modo condiviso (più letture insieme, nessuna durante un calcolo); l'approvazione in modo esclusivo."""
    blocco = "pg_advisory_xact_lock" if esclusivo else "pg_advisory_xact_lock_shared"
    conn.execute(f"SELECT {blocco}(hashtext(%s))", (BLOCCO.format(org=org_id),))
    organizzazione = conn.execute("SELECT name, codice FROM organizations WHERE org_id = %s", (org_id,)).fetchone()
    if organizzazione is None:
        raise LookupError(f"organizzazione {org_id} inesistente")
    schema = spazio(conn, org_id)
    if schema is None:
        raise LookupError(f"l'organizzazione {org_id} non ha uno spazio: i nomi dei ruoli non hanno dove stare")
    soglia = _soglia(conn, org_id)

    risultati = _righe(conn, sql.SQL(
        """SELECT v.occurrence_id, v.task_id, v.role_id, v.profile_id, v.snapshot_id, v.rubric_version,
                  v.versione_calcolo, v.tipo_capacita, v.d_provvisorio, v.componenti_d, v.giudizi_usati,
                  v.computed_at, v.n_mean, v.n_sd, v.d_mean, v.d_sd, v.p_q1, v.p_q2, v.p_q3, v.p_q4,
                  t.title_it AS task, n.nome AS ruolo
           FROM v_risultati_vigenti v
           JOIN canonical_tasks t ON t.task_id = v.task_id
           LEFT JOIN {}.ruoli_organizzativi n ON n.ruolo_id = v.role_id
           WHERE v.org_id = %s""").format(schema), (org_id,))
    occorrenze = conn.execute(
        "SELECT count(*) FROM task_occurrences o JOIN roles r USING (role_id) WHERE r.org_id = %s", (org_id,)
    ).fetchone()[0]
    metriche = _righe(conn, sql.SQL(
        """SELECT m.role_id, n.nome AS ruolo, m.barycenter_n, m.barycenter_d, m.dispersion, m.stability,
                  m.n_tasks, m.pesi_tempo, m.provvisorio
           FROM v_role_metrics m
           JOIN roles r ON r.role_id = m.role_id
           LEFT JOIN {}.ruoli_organizzativi n ON n.ruolo_id = m.role_id
           WHERE r.org_id = %s""").format(schema), (org_id,))
    chiavi, dedotti = _chiavi(conn, risultati)
    senza_nome = any(r["ruolo"] is None for r in risultati) or any(m["ruolo"] is None for m in metriche)

    def nome(valore: str | None, ruolo_id: Any) -> str:
        return valore if valore is not None else f"ruolo senza nome {ruolo_id}"

    elementi = []
    for r in risultati:
        q, p, pari = _quadrante(r)
        elementi.append({
            "occorrenza_id": str(r["occurrence_id"]), "task_id": str(r["task_id"]), "task": r["task"],
            "ruolo_id": str(r["role_id"]), "ruolo": nome(r["ruolo"], r["role_id"]),
            "quadrante": q, "probabilita": p, "pari": pari,
            "n": _numero(r["n_mean"]), "n_dev": _numero(r["n_sd"]),
            "d": _numero(r["d_mean"]), "d_dev": _numero(r["d_sd"]),
            "instabile": None if soglia is None else p < soglia["valore"],
        })
    elementi.sort(key=lambda e: e["occorrenza_id"])

    def conteggi(gruppo: list[dict[str, Any]]) -> dict[str, int]:
        return {q: sum(e["quadrante"] == q for e in gruppo) for q in QUADRANTI}

    def instabili(gruppo: list[dict[str, Any]]) -> int | None:
        return None if soglia is None else sum(e["instabile"] for e in gruppo)

    ruoli = []
    for m in metriche:
        gruppo = [e for e in elementi if e["ruolo_id"] == str(m["role_id"])]
        ruoli.append({
            "ruolo_id": str(m["role_id"]), "ruolo": nome(m["ruolo"], m["role_id"]), "occorrenze": m["n_tasks"],
            "baricentro_n": _numero(m["barycenter_n"]), "baricentro_d": _numero(m["barycenter_d"]),
            "dispersione": _numero(m["dispersion"]), "stabilita": _numero(m["stability"]),
            "pesi_tempo": m["pesi_tempo"], "provvisorio": m["provvisorio"],
            "quadranti": conteggi(gruppo), "instabili": instabili(gruppo),
        })
    ruoli.sort(key=lambda x: (x["ruolo"], x["ruolo_id"]))  # ordine in Python: non dipende dalla collazione

    da_rivedere = None
    if soglia is not None:
        da_rivedere = sorted((e for e in elementi if e["instabile"]),
                             key=lambda e: (e["probabilita"], e["task"], e["ruolo"], e["occorrenza_id"]))

    avvertenze = [codice for codice, vale in (
        ("nessun_risultato", not risultati),
        ("occorrenze_senza_risultato", occorrenze > len(risultati)),
        ("capacita_di_riserva", any(r["tipo_capacita"] == "riserva" for r in risultati)),
        ("d_provvisorio", any(r["d_provvisorio"] for r in risultati)),
        ("pesi_uguali", any(m["pesi_tempo"] == "uguali" for m in metriche)),
        ("soglia_di_stabilita_non_approvata", soglia is None),
        ("soglia_comune_non_adottata", soglia is not None and soglia["comune"] and soglia["adozione_id"] is None),
        ("modelli_dedotti", dedotti),
        ("ruoli_senza_nome", senza_nome),
    ) if vale]

    restituzione: dict[str, Any] = {
        "versione": VERSIONE_RESTITUZIONE,
        "organizzazione": {"org_id": org_id, "nome": organizzazione[0], "codice": organizzazione[1]},
        "nota": NOTA,
        "chiavi": chiavi,
        "soglia_stabilita": soglia,
        "avvertenze": avvertenze,
        "riepilogo": {
            "occorrenze": occorrenze, "con_risultato": len(risultati), "senza_risultato": occorrenze - len(risultati),
            "quadranti": conteggi(elementi), "instabili": instabili(elementi),
            "pari": sum(e["pari"] for e in elementi),
        },
        "ruoli": ruoli,
        "da_rivedere": da_rivedere,
        "occorrenze": elementi,
    }
    restituzione["impronta"] = impronta_restituzione(restituzione)
    restituzione["generato_il"] = datetime.now(timezone.utc).isoformat()
    restituzione["approvazione"] = _approvazione(conn, org_id, restituzione["impronta"])
    return restituzione


def restituzione_organizzazione(conn: psycopg.Connection, utente_id: str, org_id: str) -> dict[str, Any]:
    """Restituzione dei risultati vigenti dell'organizzazione. Sola lettura; serve il permesso leggere.
    Il lock dura fino alla fine della transazione di chi chiama."""
    org_id = str(uuid.UUID(str(org_id)))
    richiedi(conn, utente_id, "leggere", org_id, risorsa=f"restituzione:{org_id}")
    return _costruisci(conn, org_id)


def approva_restituzione(
    conn: psycopg.Connection, utente_id: str, org_id: str, restituzione: dict[str, Any], *, motivazione: str
) -> int:
    """Atto di approvazione del comitato guida sulla restituzione letta. La restituzione si ricalcola: se i
    risultati sono cambiati dopo la lettura, è superata e non si approva. Ritorna l'identificativo dell'atto."""
    org_id = str(uuid.UUID(str(org_id)))
    richiedi(conn, utente_id, "approvare_restituzione", org_id, risorsa=f"restituzione:{org_id}")
    if not isinstance(restituzione, dict) or not isinstance(restituzione.get("organizzazione"), dict):
        raise ValueError("restituzione non valida")
    impronta = restituzione.get("impronta")
    if impronta != impronta_restituzione(restituzione):
        raise ValueError("l'impronta non corrisponde al contenuto della restituzione")
    if restituzione["organizzazione"].get("org_id") != org_id:
        raise ValueError("la restituzione riguarda un'altra organizzazione")
    try:
        with conn.transaction():
            attuale = _costruisci(conn, org_id, esclusivo=True)  # lock del calcolo fino alla fine della transazione
            if attuale["impronta"] != impronta:
                raise RestituzioneSuperata("i risultati o la configurazione sono cambiati dopo la lettura")
            if attuale["approvazione"] is not None:
                raise DecisioneGiaPresa(f"restituzione già approvata con l'atto {attuale['approvazione']}")
            return registra(
                conn, autore_id=utente_id, tipo_oggetto="restituzione", oggetto_id=impronta, atto="approvazione",
                motivazione=motivazione, org_id=org_id,
                dettagli={"versione": VERSIONE_RESTITUZIONE, "occorrenze": attuale["riepilogo"]["con_risultato"],
                          "avvertenze": attuale["avvertenze"]},
            )
    except psycopg.errors.UniqueViolation as errore:
        if errore.diag.constraint_name != _INDICE_APPROVAZIONE:
            raise
        raise DecisioneGiaPresa("restituzione già approvata") from errore


# --- versione leggibile ------------------------------------------------------------------

def _testo(valore: Any) -> str:
    """Testo su una riga, senza caratteri che cambiano la struttura del Markdown."""
    testo = str(valore).replace("\\", "\\\\").replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")
    testo = " ".join(testo.split())
    return "\\" + testo if testo[:1] in ("#", "-", "*", "+", ">") else testo


def _cella(valore: Any) -> str:
    if valore is None:
        return ""
    if isinstance(valore, float):
        return f"{valore:.3f}"
    return _testo(valore)


def _elenco(valori: list[Any]) -> str:
    return ", ".join(_testo(v) for v in valori) or "-"


def _tabella(intestazioni: list[str], righe: list[list[Any]]) -> list[str]:
    return (["| " + " | ".join(intestazioni) + " |", "|" + "---|" * len(intestazioni)]
            + ["| " + " | ".join(_cella(v) for v in r) + " |" for r in righe] + [""])


def restituzione_in_markdown(r: dict[str, Any]) -> str:
    """Versione leggibile della restituzione. Il JSON resta la fonte per la verifica e per l'approvazione."""
    o, c, s, q = r["organizzazione"], r["chiavi"], r["soglia_stabilita"], r["riepilogo"]
    soglie = "; ".join(f"{_testo(x['profilo'])}: N alto da {x['theta_n']}, D alto da {x['theta_d']}"
                       for x in c["soglie_quadranti"]) or "-"
    righe = [f"# Restituzione: {_testo(o['nome'])} ({_testo(o['codice'])})", "",
             f"Versione {r['versione']}, generata il {r['generato_il']}.", "",
             f"Impronta: `{r['impronta']}`. "
             + (f"Approvata dal comitato guida con l'atto {r['approvazione']}." if r["approvazione"] is not None
                else "Non ancora approvata dal comitato guida."), "",
             f"> {r['nota']}", "",
             "## Chiavi dei risultati", "",
             f"- Rubrica: {_elenco(c['rubriche'])}",
             f"- Profilo di pesi: {_elenco(c['profili'])} (soglie dei quadranti: {soglie})",
             f"- Snapshot di capacità: {_elenco(c['snapshot'])} (metodo {_elenco(c['metodi_capacita'])}, "
             f"capacità {_elenco(c['capacita'])})",
             f"- Versione del calcolo: {_elenco(c['versioni_calcolo'])}",
             f"- Componenti di D: {_elenco(c['componenti_d'])}",
             f"- Modelli dei giudizi: {_elenco(c['modelli_giudizi'])}",
             "- Soglia di stabilità: " + (f"{s['valore']} (parametro {s['parametro_id']}, versione {s['versione']}"
                                          f"{', comune' if s['comune'] else ''})" if s else "non approvata"), "",
             "## Perché i risultati sono provvisori", ""]
    righe += [f"- {AVVERTENZE[a]}" for a in r["avvertenze"]] or ["- Nessuna avvertenza."]
    righe += ["", "## Riepilogo", "",
              f"Occorrenze {q['occorrenze']}, con risultato {q['con_risultato']}, senza {q['senza_risultato']}"
              + (f", instabili {q['instabili']}" if q["instabili"] is not None else "")
              + f"; a pari probabilità fra due quadranti {q['pari']} (vale l'ordine Q1, Q2, Q3, Q4).", "",
              "Quadrante più probabile: Q1 N alto e D alto, Q2 N alto e D basso, Q3 N basso e D alto, "
              "Q4 N basso e D basso.", ""]
    righe += _tabella(["Q1", "Q2", "Q3", "Q4"], [[q["quadranti"][x] for x in QUADRANTI]])
    righe += ["## Ruoli", ""]
    righe += _tabella(["Ruolo", "Occorrenze", "Baricentro N", "Baricentro D", "Dispersione", "Stabilità", "Pesi",
                       "Provvisorio", "Q1", "Q2", "Q3", "Q4", "Instabili"],
                      [[x["ruolo"], x["occorrenze"], x["baricentro_n"], x["baricentro_d"], x["dispersione"],
                        x["stabilita"], x["pesi_tempo"], "sì" if x["provvisorio"] else "no",
                        *[x["quadranti"][y] for y in QUADRANTI], x["instabili"]] for x in r["ruoli"]])
    righe += ["## Occorrenze da rivedere", ""]
    if r["da_rivedere"] is None:
        righe += ["Non calcolata: manca la soglia di stabilità approvata.", ""]
    elif not r["da_rivedere"]:
        righe += ["Nessuna: ogni occorrenza ha un quadrante stabile.", ""]
    else:
        righe += ["Dalla meno certa.", ""]
        righe += _tabella(["Task", "Ruolo", "Quadrante", "Probabilità", "N", "D", "Occorrenza"],
                          [[e["task"], e["ruolo"], e["quadrante"].upper(), e["probabilita"], e["n"], e["d"],
                            e["occorrenza_id"]] for e in r["da_rivedere"]])
    return "\n".join(righe)
