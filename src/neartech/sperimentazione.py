"""Avanzamento della sperimentazione (fase 6; registro di metodo, sezione 27).

Per ogni voce della rubrica, quante occorrenze con un risultato vigente hanno già almeno un giudizio di persona
(revisori, lavoratori, beneficiari) sul task, sui task fusi in esso o sull'occorrenza, con la rubrica del
risultato. Sono i giudizi che nel calcolo prevalgono su quelli del modello: la piattaforma li mostra come
avanzamento, non come blocco. Un giudizio raccolto dopo l'ultimo calcolo conta già qui; entra nei risultati con
il ricalcolo successivo.

Nessun output riguarda una persona: si contano giudizi, non chi li ha dati.
"""

import uuid
from typing import Any

import psycopg

from neartech.calcolo import D_ITEMS, K_ITEMS, VALUTATORI_PERSONE
from neartech.permessi import richiedi

VOCI = (*K_ITEMS, "r", *D_ITEMS)


def avanzamento_sperimentazione(conn: psycopg.Connection, utente_id: str, org_id: str) -> dict[str, Any]:
    """Giudizi di persona per voce sulle occorrenze con un risultato vigente. Serve il permesso leggere."""
    org_id = str(uuid.UUID(str(org_id)))
    richiedi(conn, utente_id, "leggere", org_id, risorsa=f"sperimentazione:{org_id}")
    totale = conn.execute("SELECT count(*) FROM v_risultati_vigenti WHERE org_id = %s", (org_id,)).fetchone()[0]
    righe = conn.execute(
        """WITH RECURSIVE base AS (
             SELECT occurrence_id, task_id, rubric_version FROM v_risultati_vigenti WHERE org_id = %(org)s),
           fusi(radice, task_id) AS (
             SELECT DISTINCT task_id, task_id FROM base
             UNION SELECT f.radice, t.task_id FROM canonical_tasks t JOIN fusi f ON t.merged_into = f.task_id)
           SELECT DISTINCT b.occurrence_id, a.item FROM base b
           JOIN assessment_runs a ON a.rubric_version = b.rubric_version AND a.rater_kind = ANY(%(persone)s)
             AND ((a.target_kind = 'task'
                   AND a.target_id IN (SELECT f.task_id FROM fusi f WHERE f.radice = b.task_id))
                  OR (a.target_kind = 'occurrence' AND a.target_id = b.occurrence_id))""",
        {"org": org_id, "persone": list(VALUTATORI_PERSONE)},
    ).fetchall()
    per_occorrenza: dict[str, list[str]] = {}
    for occorrenza, voce in righe:
        per_occorrenza.setdefault(str(occorrenza), []).append(voce)
    voci = {v: {"persone": sum(v in x for x in per_occorrenza.values()), "totale": totale} for v in VOCI}
    giudicate = sum(x["persone"] for x in voci.values())
    return {
        "totale": totale,
        "voci": voci,
        "quota": round(giudicate / (len(VOCI) * totale), 4) if totale else 0.0,
        "occorrenze": {k: sorted(v, key=VOCI.index) for k, v in sorted(per_occorrenza.items())},
    }
