"""Lavoratore della coda dei job, da avviare con un pianificatore (Utilità di pianificazione, cron).

Uso:
  DATABASE_URL=... python scripts/worker.py [--nome lavoratore-1] [--massimo 50]

Prende i job in coda uno alla volta, ciascuno nella propria transazione, finché la coda
è vuota o si raggiunge --massimo. I gestori per tipo di job si registrano in GESTORI:
oggi non ce ne sono, quindi un job di tipo sconosciuto fallisce con un errore esplicito.
"""

import argparse
import socket
import sys
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.coda import completa, fallisci, prendi, recupera_bloccati  # noqa: E402
from neartech.db import connect  # noqa: E402

# Tipo di job -> funzione(conn, payload). Ogni fase aggiunge qui i propri gestori.
GESTORI: dict[str, Callable[[psycopg.Connection, Any], None]] = {}

RIPROVA_TRA = timedelta(minutes=5)
BLOCCATO_DOPO = timedelta(hours=1)


def esegui_uno(conn: psycopg.Connection, lavoratore: str) -> bool:
    with conn.transaction():
        job = prendi(conn, lavoratore, tipi=list(GESTORI) or None)
    if job is None:
        return False
    try:
        gestore = GESTORI.get(job.tipo)
        if gestore is None:
            raise LookupError(f"nessun gestore per il tipo '{job.tipo}'")
        with conn.transaction():
            gestore(conn, job.payload)
            completa(conn, job.job_id)
        print(f"completato {job.tipo} {job.job_id}", flush=True)
    except Exception as errore:  # noqa: BLE001 - ogni errore del gestore va registrato sul job
        with conn.transaction():
            fallisci(conn, job.job_id, f"{type(errore).__name__}: {errore}"[:2000], riprova_tra=RIPROVA_TRA)
        print(f"fallito {job.tipo} {job.job_id}: {type(errore).__name__}", flush=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nome", default=f"{socket.gethostname()}-worker")
    parser.add_argument("--massimo", type=int, default=50)
    args = parser.parse_args()

    with connect() as conn:
        conn.autocommit = True
        with conn.transaction():
            recuperati = recupera_bloccati(conn, piu_vecchi_di=BLOCCATO_DOPO)
        if recuperati:
            print(f"rimessi in coda {recuperati} job bloccati", flush=True)
        eseguiti = 0
        while eseguiti < args.massimo and esegui_uno(conn, args.nome):
            eseguiti += 1


if __name__ == "__main__":
    main()
