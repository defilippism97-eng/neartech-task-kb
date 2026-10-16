"""Coda dei job su PostgreSQL, senza piattaforma di orchestrazione.

Un lavoratore prende un job con FOR UPDATE SKIP LOCKED: due lavoratori non prendono
mai lo stesso job, e solo chi lo ha preso può chiuderlo. Un job fallito torna in coda
finché restano tentativi; un job rimasto in corso troppo a lungo (lavoratore caduto)
si recupera con recupera_bloccati, che lo chiude come fallito se i tentativi sono finiti.
Il payload contiene solo riferimenti (identificativi), mai testo del cliente: la tabella
jobs sta nello schema condiviso (ADR 0001).
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


@dataclass(frozen=True)
class Job:
    job_id: str
    tipo: str
    payload: Any
    org_id: str | None
    tentativo: int


def accoda(
    conn: psycopg.Connection,
    tipo: str,
    payload: Any,
    *,
    org_id: str | None = None,
    esegui_dopo: timedelta = timedelta(0),
    tentativi_massimi: int = 1,
) -> str:
    return str(conn.execute(
        """INSERT INTO jobs (kind, payload, org_id, tentativi_massimi, run_after)
           VALUES (%s, %s, %s, %s, now() + %s) RETURNING job_id""",
        (tipo, Jsonb(payload), org_id, tentativi_massimi, esegui_dopo),
    ).fetchone()[0])


def prendi(conn: psycopg.Connection, lavoratore: str, *, tipi: list[str]) -> Job | None:
    """Prende il primo job pronto fra i tipi indicati. Una lista vuota non prende nulla."""
    if not tipi:
        return None
    riga = conn.execute(
        """WITH scelto AS MATERIALIZED (
             SELECT job_id FROM jobs
             WHERE status = 'queued' AND run_after <= now() AND kind = ANY(%(tipi)s::text[])
             ORDER BY run_after, created_at
             FOR UPDATE SKIP LOCKED
             LIMIT 1)
           UPDATE jobs SET status = 'running', attempts = attempts + 1,
                           preso_da = %(lavoratore)s, preso_il = now()
           FROM scelto WHERE jobs.job_id = scelto.job_id
           RETURNING jobs.job_id, jobs.kind, jobs.payload, jobs.org_id, jobs.attempts""",
        {"lavoratore": lavoratore, "tipi": tipi},
    ).fetchone()
    if riga is None:
        return None
    return Job(str(riga[0]), riga[1], riga[2], str(riga[3]) if riga[3] else None, riga[4])


def completa(conn: psycopg.Connection, job_id: str, lavoratore: str) -> bool:
    """Chiude il job. False se il job non è più in mano a questo lavoratore."""
    return conn.execute(
        """UPDATE jobs SET status = 'done', completato_il = now()
           WHERE job_id = %s AND status = 'running' AND preso_da = %s""",
        (job_id, lavoratore),
    ).rowcount == 1


def fallisci(
    conn: psycopg.Connection, job_id: str, lavoratore: str, errore: str, *, riprova_tra: timedelta
) -> bool:
    """Rimette in coda o chiude come fallito. False se il job non è più in mano a questo lavoratore."""
    return conn.execute(
        """UPDATE jobs SET
             status = CASE WHEN attempts < tentativi_massimi THEN 'queued' ELSE 'failed' END,
             run_after = CASE WHEN attempts < tentativi_massimi THEN now() + %s ELSE run_after END,
             ultimo_errore = %s, preso_da = NULL, preso_il = NULL
           WHERE job_id = %s AND status = 'running' AND preso_da = %s""",
        (riprova_tra, errore, job_id, lavoratore),
    ).rowcount == 1


def recupera_bloccati(conn: psycopg.Connection, *, piu_vecchi_di: timedelta) -> int:
    """Job in corso da troppo: tornano in coda, o falliscono se i tentativi sono finiti."""
    return conn.execute(
        """UPDATE jobs SET
             status = CASE WHEN attempts < tentativi_massimi THEN 'queued' ELSE 'failed' END,
             ultimo_errore = CASE WHEN attempts < tentativi_massimi THEN ultimo_errore
                                  ELSE 'lavoratore non più attivo, tentativi esauriti' END,
             preso_da = NULL, preso_il = NULL
           WHERE status = 'running' AND preso_il < now() - %s""",
        (piu_vecchi_di,),
    ).rowcount
