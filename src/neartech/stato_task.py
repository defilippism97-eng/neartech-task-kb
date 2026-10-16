"""Stato di validazione dei task del dataset condiviso.

validato: rivisto da persone. stima_modello: provvisorio. da_integrare: non rivisto.
Ogni cambio è un atto nel registro e una riga nella storia; un task non validato
non può fondare un'analisi definitiva.

Il task è condiviso fra organizzazioni: un revisore può cambiarne lo stato solo se il
task compare nello spazio della propria organizzazione. Chi valida i task comuni a più
organizzazioni resta una decisione di governance aperta (docs/HANDOVER.md).
"""

import psycopg
from psycopg import sql

from neartech.organizzazioni import schema_organizzazione
from neartech.permessi import richiedi
from neartech.registro import registra

STATI = ("validato", "stima_modello", "da_integrare")


class TaskNonCollegato(LookupError):
    """Il task non compare nello spazio dell'organizzazione del revisore."""


def _collegato(conn: psycopg.Connection, task_id: str, org_id: str) -> bool:
    riga = conn.execute("SELECT codice FROM organizations WHERE org_id = %s", (org_id,)).fetchone()
    if riga is None or riga[0] is None:
        return False
    return conn.execute(
        sql.SQL("SELECT EXISTS (SELECT 1 FROM {}.occorrenze WHERE task_id = %s)")
        .format(sql.Identifier(schema_organizzazione(riga[0]))),
        (task_id,),
    ).fetchone()[0]


def imposta_stato(
    conn: psycopg.Connection, utente_id: str, task_id: str, stato: str, *, org_id: str, motivazione: str
) -> int:
    if stato not in STATI:
        raise ValueError(f"stato sconosciuto: {stato!r}")
    with conn.transaction():
        richiedi(conn, utente_id, "giudicare_task", org_id, risorsa=f"task:{task_id}")
        if not _collegato(conn, task_id, org_id):
            raise TaskNonCollegato(f"il task {task_id} non compare nello spazio dell'organizzazione")
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
