"""Indirizzi del comitato e profilo di pesi dell'organizzazione (fase 6, fetta 3; registro di metodo, sezione 27).

Il comitato guida risponde a un questionario sulla visione dell'innovazione dell'impresa; le risposte calibrano i
pesi di D (w_d1-w_d4) partendo dal profilo in uso. Domande, voce che ogni domanda sposta, verso, intensità e limiti
dei pesi non stanno nel codice: sono il parametro di governance `questionario_indirizzi`, versionato e approvato.

Regola (dal parametro): per ogni voce j di D, s_j è la media di verso·(risposta − centro)/centro sulle domande di
quella voce (in [−1, 1]); il peso diventa w_j·(1 + intensità·s_j), poi si porta dentro i limiti e si riporta a
somma uno. I pesi di N, λ e le soglie dei quadranti restano quelli del profilo di partenza.

Il profilo nasce come bozza con l'atto di proposta (risposte nel registro, nota nello spazio dell'organizzazione);
lo approva il comitato, lo verifica l'auditor (atto "verifica"); con entrambi gli atti diventa il profilo attivo
dell'organizzazione. Il database lo impone (migrazione 0037). Gli indirizzi danno enfasi, non toccano il pavimento
legale: oggi nessun pavimento è registrato, e la verifica lo dichiara.
"""

import hashlib
import uuid
from typing import Any

import psycopg

from neartech.calcolo import (D_ITEMS, K_ITEMS, Profilo, _configurazione, _giudizi, simula)
from neartech.governance import DecisioneGiaPresa, ParametroAssente, parametro_vigente
from neartech.permessi import richiedi
from neartech.registro import registra

PARAMETRO_QUESTIONARIO = "questionario_indirizzi"
ESTRAZIONI_EFFETTO = 300
QUADRANTI = ("q1", "q2", "q3", "q4")


class QuestionarioNonApprovato(LookupError):
    """Il questionario degli indirizzi non ha una versione approvata."""


def _blocca(conn: psycopg.Connection, org_id: str) -> None:
    conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"profilo:{org_id}",))


def questionario(conn: psycopg.Connection, org_id: str) -> dict[str, Any]:
    """Questionario vigente (proprio dell'organizzazione o comune), controllato nella struttura."""
    try:
        parametro = parametro_vigente(conn, PARAMETRO_QUESTIONARIO, org_id)
    except ParametroAssente:
        raise QuestionarioNonApprovato("il questionario degli indirizzi non è ancora approvato") from None
    q = parametro.valore
    domande = q.get("domande") if isinstance(q, dict) else None
    risposte = q.get("risposte") if isinstance(q, dict) else None
    if not domande or not risposte or not all(d.get("voce") in D_ITEMS and d.get("verso") in (-1, 1) for d in domande):
        raise ValueError(f"questionario {parametro.parametro_id} non valido")
    if not (0 < q["limiti"]["min"] < q["limiti"]["max"] < 1) or not (0 <= q["intensita"] <= 1):
        raise ValueError(f"limiti o intensità non validi nel questionario {parametro.parametro_id}")
    return {**q, "parametro_id": parametro.parametro_id, "versione_parametro": parametro.versione}


def pesi_dalle_risposte(base: dict[str, float], q: dict[str, Any], risposte: dict[str, int]) -> dict[str, float]:
    """Pesi di D calcolati dalle risposte con la regola del questionario. Funzione pura e deterministica."""
    centro = (len(q["risposte"]) - 1) / 2
    pesi = {}
    for voce in D_ITEMS:
        scarti = [d["verso"] * (risposte[d["codice"]] - centro) / centro for d in q["domande"] if d["voce"] == voce]
        spinta = sum(scarti) / len(scarti) if scarti else 0.0
        pesi[voce] = base[voce] * (1 + q["intensita"] * spinta)
    minimo, massimo = q["limiti"]["min"], q["limiti"]["max"]
    for _ in range(20):  # dentro i limiti e a somma uno: si alternano le due condizioni fino a stabilità
        pesi = {v: min(massimo, max(minimo, p)) for v, p in pesi.items()}
        totale = sum(pesi.values())
        pesi = {v: p / totale for v, p in pesi.items()}
        if all(minimo - 1e-9 <= p <= massimo + 1e-9 for p in pesi.values()):
            break
    arrotondati = {v: round(p, 3) for v, p in pesi.items()}
    scarto = round(1 - sum(arrotondati.values()), 3)
    maggiore = max(arrotondati, key=lambda v: (arrotondati[v], v))
    arrotondati[maggiore] = round(arrotondati[maggiore] + scarto, 3)
    return arrotondati


def controlli(q: dict[str, Any], pesi: dict[str, float]) -> list[dict[str, Any]]:
    """Controlli automatici che l'auditor vede prima di dare l'ok."""
    return [
        {"codice": "somma_uno", "esito": abs(sum(pesi.values()) - 1) < 0.0015,
         "descrizione": "I pesi di D sommano a uno."},
        {"codice": "dentro_i_limiti", "esito": all(q["limiti"]["min"] - 1e-9 <= p <= q["limiti"]["max"] + 1e-9
                                                    for p in pesi.values()),
         "descrizione": f"Ogni peso sta fra {q['limiti']['min']} e {q['limiti']['max']}, i limiti del questionario."},
        {"codice": "pavimento_legale", "esito": True,
         "descrizione": "Nessun pavimento legale registrato: gli indirizzi non possono scendere sotto un minimo di legge."},
    ]


def _profilo(conn: psycopg.Connection, profile_id: str) -> Profilo | None:
    riga = conn.execute(
        """SELECT profile_id, w_k1, w_k2, w_k3, lambda_r, w_d1, w_d2, w_d3, w_d4, theta_n, theta_d
           FROM weight_profiles WHERE profile_id = %s""", (profile_id,)).fetchone()
    if riga is None:
        return None
    v = [float(x) for x in riga[1:]]
    return Profilo(riga[0], w_k=dict(zip(K_ITEMS, v[0:3])), lambda_r=v[3], w_d=dict(zip(D_ITEMS, v[4:8])),
                   theta_n=v[8], theta_d=v[9])


def effetto(conn: psycopg.Connection, org_id: str, nuovo: Profilo, *, estrazioni: int = ESTRAZIONI_EFFETTO) -> dict[str, Any]:
    """Quadranti più probabili con il profilo nuovo, confrontati con i risultati vigenti. Simulazione deterministica
    che non scrive nulla."""
    rubrica, _, snapshot, tipo = _configurazione(conn, org_id)
    vigenti = {str(r[0]): r[1:] for r in conn.execute(
        "SELECT occurrence_id, p_q1, p_q2, p_q3, p_q4 FROM v_risultati_vigenti WHERE org_id = %s", (org_id,)).fetchall()}
    occorrenze = conn.execute(
        """SELECT o.occurrence_id, o.task_id FROM task_occurrences o JOIN roles r USING (role_id)
           WHERE r.org_id = %s ORDER BY o.occurrence_id""", (org_id,)).fetchall()
    cambiano, conteggi = 0, dict.fromkeys(QUADRANTI, 0)
    for occorrenza, task in occorrenze:
        valori, _, _ = _giudizi(conn, rubrica, str(task), str(occorrenza))
        righe = conn.execute("SELECT dimension, c_low, c_high FROM task_capability WHERE snapshot_id = %s AND task_id = %s",
                             (snapshot, str(task))).fetchall()
        copertura = {r[0]: (float(r[1]), float(r[2])) for r in righe}
        copertura = copertura if all(k in copertura for k in K_ITEMS) else None
        seme = int(hashlib.sha256(f"effetto:{occorrenza}".encode()).hexdigest()[:15], 16)
        r = simula(valori, copertura, nuovo, estrazioni=estrazioni, seme=seme, riserva=tipo == "riserva")
        if not r.p_quadranti:
            continue
        q_nuovo = max(QUADRANTI, key=lambda q: (r.p_quadranti[q], -QUADRANTI.index(q)))
        conteggi[q_nuovo] += 1
        prima = vigenti.get(str(occorrenza))
        if prima is not None:
            p = dict(zip(QUADRANTI, (float(x) for x in prima)))
            if max(QUADRANTI, key=lambda q: (p[q], -QUADRANTI.index(q))) != q_nuovo:
                cambiano += 1
    return {"quadranti": conteggi, "cambiano_quadrante": cambiano, "occorrenze": len(occorrenze)}


def _atti(conn: psycopg.Connection, org_id: str, profile_id: str) -> dict[str, int]:
    return {atto: decisione for decisione, atto in conn.execute(
        """SELECT decisione_id, atto FROM registro_decisioni
           WHERE tipo_oggetto = 'profilo_pesi' AND org_id = %s AND oggetto_id = %s ORDER BY posizione""",
        (org_id, profile_id)).fetchall()}


def proponi_profilo(conn: psycopg.Connection, utente_id: str, org_id: str, risposte: dict[str, int], *,
                    nota: str) -> str:
    """Il comitato risponde al questionario: nasce la bozza del profilo, con l'atto di proposta. Ritorna l'id."""
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "proporre_parametro", org_id, risorsa=f"profilo_pesi:{org_id}")
        _blocca(conn, org_id)
        q = questionario(conn, org_id)
        codici = {d["codice"] for d in q["domande"]}
        if set(risposte) != codici or not all(isinstance(v, int) and 0 <= v < len(q["risposte"]) for v in risposte.values()):
            raise ValueError("serve una risposta valida per ogni domanda del questionario")
        _, base, _, _ = _configurazione(conn, org_id)
        pesi = pesi_dalle_risposte(base.w_d, q, risposte)
        codice = conn.execute("SELECT codice FROM organizations WHERE org_id = %s", (org_id,)).fetchone()[0]
        numero = conn.execute("SELECT count(*) + 1 FROM weight_profiles WHERE org_id = %s", (org_id,)).fetchone()[0]
        profile_id = f"{codice}-indirizzi-{numero}"
        conn.execute(
            """INSERT INTO weight_profiles (profile_id, org_id, w_k1, w_k2, w_k3, lambda_r, w_d1, w_d2, w_d3, w_d4,
                                            theta_n, theta_d, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false)""",
            (profile_id, org_id, base.w_k["k1"], base.w_k["k2"], base.w_k["k3"], base.lambda_r,
             pesi["d1"], pesi["d2"], pesi["d3"], pesi["d4"], base.theta_n, base.theta_d))
        registra(conn, autore_id=utente_id, tipo_oggetto="profilo_pesi", oggetto_id=profile_id, atto="proposta",
                 motivazione=nota or "risposte al questionario degli indirizzi", org_id=org_id,
                 dettagli={"questionario": q["parametro_id"], "profilo_di_partenza": base.profilo_id,
                           "risposte": dict(sorted(risposte.items()))})
        return profile_id


def stato_indirizzi(conn: psycopg.Connection, utente_id: str, org_id: str) -> dict[str, Any]:
    """Questionario vigente, ultimo profilo proposto con pesi, atti, controlli ed effetto sui task."""
    org_id = str(uuid.UUID(str(org_id)))
    richiedi(conn, utente_id, "leggere", org_id, risorsa=f"indirizzi:{org_id}")
    try:
        q = questionario(conn, org_id)
    except QuestionarioNonApprovato:
        q = None
    _, base, _, _ = _configurazione(conn, org_id)
    ultimo = conn.execute(
        """SELECT p.profile_id, p.is_active FROM weight_profiles p
           JOIN registro_decisioni r ON r.tipo_oggetto = 'profilo_pesi' AND r.oggetto_id = p.profile_id
                                    AND r.atto = 'proposta' AND r.org_id = p.org_id
           WHERE p.org_id = %s ORDER BY r.posizione DESC LIMIT 1""", (org_id,)).fetchone()
    profilo = None
    if ultimo is not None:
        nuovo = _profilo(conn, ultimo[0])
        atti = _atti(conn, org_id, ultimo[0])
        profilo = {
            "profile_id": ultimo[0], "attivo": ultimo[1], "pesi": nuovo.w_d,
            "approvato": atti.get("approvazione"), "verificato": atti.get("verifica"),
            "controlli": controlli(q, nuovo.w_d) if q else [],
            "effetto": effetto(conn, org_id, nuovo) if not ultimo[1] else None,
        }
    return {"questionario": q, "pesi_in_uso": {"profilo": base.profilo_id, "pesi": base.w_d}, "profilo": profilo}


def _attiva_se_completo(conn: psycopg.Connection, org_id: str, profile_id: str) -> bool:
    atti = _atti(conn, org_id, profile_id)
    if "approvazione" not in atti or "verifica" not in atti:
        return False
    conn.execute("UPDATE weight_profiles SET is_active = false WHERE org_id = %s AND is_active", (org_id,))
    conn.execute("""UPDATE weight_profiles SET approved_by = 'comitato guida e auditor', approved_at = now(),
                    is_active = true WHERE profile_id = %s""", (profile_id,))
    return True


def _proposto(conn: psycopg.Connection, org_id: str, profile_id: str) -> None:
    riga = conn.execute("SELECT approved_by FROM weight_profiles WHERE profile_id = %s AND org_id = %s",
                        (profile_id, org_id)).fetchone()
    if riga is None:
        raise LookupError(f"profilo {profile_id} non trovato nell'organizzazione")
    if riga[0] is not None:
        raise DecisioneGiaPresa(f"profilo {profile_id} già approvato e attivo")


def approva_profilo(conn: psycopg.Connection, utente_id: str, org_id: str, profile_id: str, *, motivazione: str) -> int:
    """Atto di approvazione del comitato guida. Il profilo diventa attivo solo dopo la verifica dell'auditor."""
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "approvare_parametro", org_id, risorsa=f"profilo_pesi:{profile_id}")
        _blocca(conn, org_id)
        _proposto(conn, org_id, profile_id)
        if "approvazione" in _atti(conn, org_id, profile_id):
            raise DecisioneGiaPresa(f"profilo {profile_id} già approvato dal comitato")
        atto = registra(conn, autore_id=utente_id, tipo_oggetto="profilo_pesi", oggetto_id=profile_id,
                        atto="approvazione", motivazione=motivazione, org_id=org_id)
        _attiva_se_completo(conn, org_id, profile_id)
        return atto


def verifica_profilo(conn: psycopg.Connection, utente_id: str, org_id: str, profile_id: str, *, motivazione: str) -> int:
    """Ok dell'auditor dopo l'approvazione del comitato e i controlli automatici; con entrambi gli atti il profilo
    diventa attivo."""
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "verificare_profilo", org_id, risorsa=f"profilo_pesi:{profile_id}")
        _blocca(conn, org_id)
        _proposto(conn, org_id, profile_id)
        atti = _atti(conn, org_id, profile_id)
        if "approvazione" not in atti:
            raise DecisioneGiaPresa("il profilo va prima approvato dal comitato guida")
        if "verifica" in atti:
            raise DecisioneGiaPresa(f"profilo {profile_id} già verificato")
        nuovo = _profilo(conn, profile_id)
        falliti = [c["codice"] for c in controlli(questionario(conn, org_id), nuovo.w_d) if not c["esito"]]
        if falliti:
            raise ValueError(f"controlli non superati: {', '.join(falliti)}")
        atto = registra(conn, autore_id=utente_id, tipo_oggetto="profilo_pesi", oggetto_id=profile_id,
                        atto="verifica", motivazione=motivazione, org_id=org_id)
        _attiva_se_completo(conn, org_id, profile_id)
        return atto
