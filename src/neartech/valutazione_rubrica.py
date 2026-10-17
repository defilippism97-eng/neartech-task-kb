"""Valutazione dei task sulla rubrica da parte dei revisori (fase 6, fetta 4; registro di metodo, sezione 27).

Il revisore è anche il valutatore della rubrica (nessun ruolo "esperto" separato). La coda presenta i task
dell'organizzazione dal risultato meno certo: è il controllo a campione delle classificazioni. Ogni giudizio è un
record di persona in assessment_runs (rater_kind 'expert', rater_ref = identificativo interno del revisore) che nel
calcolo prevale sulle stime del modello; vale per il task in tutte le sue occorrenze, anche di altre organizzazioni
(dataset condiviso). Ogni giudizio ha il suo atto nel registro; la nota resta nello spazio dell'organizzazione.

Le voci giudicabili qui sono k1, k2, k3, r, d1, d2; d3 e d4 vengono dai questionari a lavoratori e beneficiari.
I testi dei livelli sono quelli della rubrica corrente (src/neartech/dati/rubrica-<versione>.json).
"""

import json
import uuid
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql

from neartech.calcolo import VALUTATORI_PERSONE
from neartech.permessi import richiedi
from neartech.registro import registra, spazio

VOCI_RUBRICA = ("k1", "k2", "k3", "r", "d1", "d2")
CARTELLA_RUBRICHE = Path(__file__).resolve().parent / "dati"


def rubrica_corrente(conn: psycopg.Connection) -> dict[str, Any]:
    riga = conn.execute("SELECT version FROM rubric_versions WHERE is_current AND approved_by IS NOT NULL").fetchone()
    if riga is None:
        raise LookupError("nessuna rubrica corrente approvata")
    file = CARTELLA_RUBRICHE / f"rubrica-{riga[0]}.json"
    testi = json.loads(file.read_text(encoding="utf-8")) if file.is_file() else {"voci": []}
    return {"versione": riga[0], "voci": testi["voci"]}


def coda_valutazione(conn: psycopg.Connection, utente_id: str, org_id: str, *, limite: int = 40) -> list[dict[str, Any]]:
    """Task dell'organizzazione dal risultato meno certo, con le stime del modello e i giudizi già dati."""
    org_id = str(uuid.UUID(str(org_id)))
    richiedi(conn, utente_id, "giudicare_task", org_id, risorsa=f"valutazione:{org_id}")
    schema = spazio(conn, org_id)
    if schema is None:
        raise LookupError(f"l'organizzazione {org_id} non ha uno spazio")
    rubrica = rubrica_corrente(conn)["versione"]
    righe = conn.execute(sql.SQL(
        """SELECT v.task_id, t.title_it, string_agg(DISTINCT n.nome, ', ' ORDER BY n.nome) AS ruoli,
                  min(GREATEST(v.p_q1, v.p_q2, v.p_q3, v.p_q4)) AS certezza
           FROM v_risultati_vigenti v
           JOIN canonical_tasks t ON t.task_id = v.task_id
           LEFT JOIN {}.ruoli_organizzativi n ON n.ruolo_id = v.role_id
           WHERE v.org_id = %s
           GROUP BY v.task_id, t.title_it
           ORDER BY certezza, t.title_it LIMIT %s""").format(schema), (org_id, limite)).fetchall()
    task = [str(r[0]) for r in righe]
    stime = conn.execute(
        """SELECT target_id, item, round(avg(value), 1), persona, mio FROM (
             SELECT target_id, item, value, rater_kind = ANY(%s) AS persona, rater_ref = %s AS mio
             FROM assessment_runs
             WHERE target_kind = 'task' AND target_id = ANY(%s::uuid[]) AND rubric_version = %s) giudizi
           GROUP BY target_id, item, persona, mio""",
        (list(VALUTATORI_PERSONE), str(utente_id), task, rubrica)).fetchall()
    per_task: dict[str, dict[str, Any]] = {t: {"modello": {}, "miei": {}, "persone": set()} for t in task}
    for target, voce, valore, persona, mio in stime:
        dati = per_task[str(target)]
        if not persona:
            dati["modello"][voce] = float(valore)
        else:
            dati["persone"].add(voce)
            if mio:
                dati["miei"][voce] = float(valore)
    return [{"task_id": str(r[0]), "task": r[1], "ruoli": r[2], "certezza": float(r[3]),
             "stime_modello": per_task[str(r[0])]["modello"], "miei_giudizi": per_task[str(r[0])]["miei"],
             "voci_con_giudizi_di_persona": sorted(per_task[str(r[0])]["persone"], key=VOCI_RUBRICA.index)}
            for r in righe]


def registra_giudizio_rubrica(conn: psycopg.Connection, utente_id: str, org_id: str, task_id: str, voce: str,
                              valore: int, *, nota: str = "") -> int:
    """Giudizio del revisore su una voce della rubrica, per un task dell'organizzazione. Ritorna l'atto."""
    org_id, task_id = str(uuid.UUID(str(org_id))), str(uuid.UUID(str(task_id)))
    if voce not in VOCI_RUBRICA:
        raise ValueError(f"voce non giudicabile qui: {voce!r}")
    if isinstance(valore, bool) or not isinstance(valore, int) or not 0 <= valore <= 4:
        raise ValueError("il livello va da 0 a 4")
    with conn.transaction():
        richiedi(conn, utente_id, "giudicare_task", org_id, risorsa=f"task:{task_id}")
        presente = conn.execute(
            """SELECT 1 FROM task_occurrences o JOIN roles r USING (role_id)
               WHERE o.task_id = %s AND r.org_id = %s LIMIT 1""", (task_id, org_id)).fetchone()
        if presente is None:
            raise LookupError("task non presente nell'organizzazione")
        rubrica = rubrica_corrente(conn)["versione"]
        run = str(conn.execute(
            """INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind, rater_ref, rubric_version)
               VALUES ('task', %s, %s, %s, 'expert', %s, %s) RETURNING run_id""",
            (task_id, voce, valore, str(uuid.UUID(str(utente_id))), rubrica)).fetchone()[0])
        return registra(conn, autore_id=utente_id, tipo_oggetto="giudizio_rubrica", oggetto_id=run, atto="proposta",
                        motivazione=nota.strip() or "giudizio sulla rubrica", org_id=org_id,
                        dettagli={"task": task_id, "voce": voce, "valore": valore, "rubrica": rubrica})
