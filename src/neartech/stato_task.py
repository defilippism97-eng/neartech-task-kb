"""Stato di validazione dei task del dataset condiviso.

validato: rivisto da persone. stima_modello: provvisorio. da_integrare: non rivisto.
Ogni cambio è un atto nel registro e una riga nella storia; un task non validato
non può fondare un'analisi definitiva.
"""

import psycopg

from neartech.permessi import richiedi
from neartech.registro import registra

STATI = ("validato", "stima_modello", "da_integrare")


def imposta_stato(
    conn: psycopg.Connection, utente_id: str, task_id: str, stato: str, *, org_id: str, motivazione: str
) -> int:
    if stato not in STATI:
        raise ValueError(f"stato sconosciuto: {stato!r}")
    richiedi(conn, utente_id, "giudicare_task", org_id, risorsa=f"task:{task_id}")
    decisione = registra(
        conn, autore_id=utente_id, tipo_oggetto="stato_task", oggetto_id=str(task_id),
        atto="approvazione", motivazione=motivazione, org_id=org_id, dettagli={"stato": stato},
    )
    conn.execute(
        "INSERT INTO stati_validazione_task (task_id, stato, decisione_id) VALUES (%s, %s, %s)",
        (task_id, stato, decisione),
    )
    return decisione


def stato_corrente(conn: psycopg.Connection, task_id: str) -> str:
    riga = conn.execute(
        "SELECT stato FROM stato_validazione_corrente WHERE task_id = %s", (task_id,)
    ).fetchone()
    if riga is None:
        raise LookupError(f"task {task_id} inesistente")
    return riga[0]
