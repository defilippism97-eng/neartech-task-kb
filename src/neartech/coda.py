"""Coda dei job su PostgreSQL, senza piattaforma di orchestrazione.

Un lavoratore prende un job con FOR UPDATE SKIP LOCKED: due lavoratori non prendono
mai lo stesso job. Un job fallito torna in coda finché restano tentativi; un job
rimasto in corso troppo a lungo (lavoratore caduto) si recupera con recupera_bloccati.
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


def prendi(conn: psycopg.Connection, lavoratore: str, *, tipi: list[str] | None = None) -> Job | None:
    riga = conn.execute(
        """UPDATE jobs SET status = 'running', attempts = attempts + 1, preso_da = %(lavoratore)s, preso_il = now()
           WHERE job_id = (
             SELECT job_id FROM jobs
             WHERE status = 'queued' AND run_after <= now()
               AND (%(tipi)s::text[] IS NULL OR kind = ANY(%(tipi)s::text[]))
             ORDER BY run_after, created_at
             FOR UPDATE SKIP LOCKED
             LIMIT 1)
           RETURNING job_id, kind, payload, org_id, attempts""",
        {"lavoratore": lavoratore, "tipi": tipi},
    ).fetchone()
    if riga is None:
        return None
    return Job(str(riga[0]), riga[1], riga[2], str(riga[3]) if riga[3] else None, riga[4])


def completa(conn: psycopg.Connection, job_id: str) -> None:
    conn.execute(
        "UPDATE jobs SET status = 'done', completato_il = now() WHERE job_id = %s AND status = 'running'",
        (job_id,),
    )


def fallisci(conn: psycopg.Connection, job_id: str, errore: str, *, riprova_tra: timedelta) -> None:
    conn.execute(
        """UPDATE jobs SET
             status = CASE WHEN attempts < tentativi_massimi THEN 'queued' ELSE 'failed' END,
             run_after = CASE WHEN attempts < tentativi_massimi THEN now() + %s ELSE run_after END,
             ultimo_errore = %s, preso_da = NULL, preso_il = NULL
           WHERE job_id = %s AND status = 'running'""",
        (riprova_tra, errore, job_id),
    )


def recupera_bloccati(conn: psycopg.Connection, *, piu_vecchi_di: timedelta) -> int:
    return conn.execute(
        """UPDATE jobs SET status = 'queued', preso_da = NULL, preso_il = NULL
           WHERE status = 'running' AND preso_il < now() - %s""",
        (piu_vecchi_di,),
    ).rowcount
