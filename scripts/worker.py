"""Lavoratore della coda dei job, da avviare con un pianificatore (Utilità di pianificazione, cron).

Uso:
  DATABASE_URL=... python scripts/worker.py [--nome lavoratore-1] [--massimo 50]

Prende i job in coda uno alla volta, ciascuno nella propria transazione, finché la coda
è vuota o si raggiunge --massimo. Sul job si registra solo il tipo di errore e la prima riga
del messaggio, troncata: il traceback va nel log locale.

Gestori della pipeline dei documenti (neartech.pipeline, fase 6):
- scomposizione dei mansionari caricati dalla piattaforma: solo con NEARTECH_ANTHROPIC_API_KEY.
  Ogni job è una chiamata a pagamento già confermata da un atto con la stima dei costi;
- proposta di abbinamento e applicazione dei lotti: solo con --embedding (bge-m3 in locale,
  da eseguire con .venv-embedding, docs/sviluppo.md).
I job di un tipo senza gestore restano in coda.
"""

import argparse
import logging
import os
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
from neartech.pipeline import gestori, incorpora_bge_m3  # noqa: E402

# Tipo di job -> funzione(conn, payload). Si riempie in main() secondo chiave e ambiente disponibili.
GESTORI: dict[str, Callable[[psycopg.Connection, Any], None]] = {}

RIPROVA_TRA = timedelta(minutes=5)
BLOCCATO_DOPO = timedelta(hours=1)
LUNGHEZZA_ERRORE = 300

log = logging.getLogger("neartech.worker")


class JobNonPiuNostro(RuntimeError):
    """Il job è stato recuperato da un altro lavoratore mentre questo lo eseguiva."""


def _errore_breve(errore: BaseException) -> str:
    righe = str(errore).splitlines()
    return f"{type(errore).__name__}: {righe[0] if righe else ''}"[:LUNGHEZZA_ERRORE]


def esegui_uno(conn: psycopg.Connection, lavoratore: str) -> bool:
    with conn.transaction():
        job = prendi(conn, lavoratore, tipi=list(GESTORI))
    if job is None:
        return False
    try:
        with conn.transaction():
            GESTORI[job.tipo](conn, job.payload)
            if not completa(conn, job.job_id, lavoratore):
                raise JobNonPiuNostro(job.job_id)
        log.info("completato %s %s", job.tipo, job.job_id)
    except Exception as errore:  # noqa: BLE001 - ogni errore del gestore va registrato sul job
        log.exception("fallito %s %s", job.tipo, job.job_id)
        with conn.transaction():
            fallisci(conn, job.job_id, lavoratore, _errore_breve(errore), riprova_tra=RIPROVA_TRA)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nome", default=f"{socket.gethostname()}-worker")
    parser.add_argument("--massimo", type=int, default=50)
    parser.add_argument("--embedding", action="store_true", help="registra proposta e applicazione dei lotti")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    chiave = os.environ.get("NEARTECH_ANTHROPIC_API_KEY")
    client = None
    if chiave:
        import anthropic
        client = anthropic.Anthropic(api_key=chiave)
    GESTORI.update(gestori(client=client, incorpora=incorpora_bge_m3() if args.embedding else None))
    if not GESTORI:
        log.info("nessun gestore registrato: nessun job da prendere")
        return

    with connect() as conn:
        conn.autocommit = True
        with conn.transaction():
            recuperati = recupera_bloccati(conn, piu_vecchi_di=BLOCCATO_DOPO)
        if recuperati:
            log.info("recuperati %d job bloccati", recuperati)
        eseguiti = 0
        while eseguiti < args.massimo and esegui_uno(conn, args.nome):
            eseguiti += 1


if __name__ == "__main__":
    main()
