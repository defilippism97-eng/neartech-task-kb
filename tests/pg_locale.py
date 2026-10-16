"""Postgres locale usa-e-getta per i test.

Si usa quando NEARTECH_TEST_DSN non è impostata. I binari (PostgreSQL 16 con
pgvector) arrivano da NEARTECH_PG_BIN o, in mancanza, dalla cartella in cui sono
stati estratti dal pacchetto pgserver (vedi docs/sviluppo.md). Il cluster vive in
una cartella temporanea, ascolta solo su 127.0.0.1 e viene distrutto a fine sessione.
"""

import os
import shutil
import socket
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import psycopg

NOME_DB = "neartech_test"
_SUFFISSO = ".exe" if os.name == "nt" else ""


def cartella_binari() -> Path | None:
    candidati = []
    if os.environ.get("NEARTECH_PG_BIN"):
        candidati.append(Path(os.environ["NEARTECH_PG_BIN"]))
    if os.environ.get("LOCALAPPDATA"):
        candidati.append(
            Path(os.environ["LOCALAPPDATA"]) / "neartech" / "pgserver-0.1.4" / "pgserver" / "pginstall" / "bin"
        )
    for cartella in candidati:
        if (cartella / f"initdb{_SUFFISSO}").exists():
            return cartella
    return None


def _porta_libera() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _esegui(binari: Path, programma: str, *argomenti: str) -> None:
    # Niente pipe: su Windows il server avviato da pg_ctl le eredita e subprocess
    # resterebbe in attesa della loro chiusura. I messaggi del server vanno nel log (-l).
    subprocess.run(
        [str(binari / f"{programma}{_SUFFISSO}"), *argomenti],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@contextmanager
def postgres_temporaneo(binari: Path) -> Iterator[str]:
    """Avvia un cluster temporaneo e restituisce il DSN di un database il cui nome contiene 'test'."""
    radice = Path(tempfile.mkdtemp(prefix="neartech-pg-"))
    dati = radice / "dati"
    porta = _porta_libera()
    _esegui(binari, "initdb", "-D", str(dati), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--no-instructions")
    _esegui(
        binari, "pg_ctl", "-D", str(dati), "-l", str(radice / "log.txt"), "-w",
        "-o", f"-p {porta} -h 127.0.0.1", "start",
    )
    try:
        base = f"postgresql://postgres@127.0.0.1:{porta}"
        with psycopg.connect(f"{base}/postgres", autocommit=True) as conn:
            conn.execute(f"CREATE DATABASE {NOME_DB}")
        yield f"{base}/{NOME_DB}"
    finally:
        _esegui(binari, "pg_ctl", "-D", str(dati), "-m", "fast", "-w", "stop")
        shutil.rmtree(radice, ignore_errors=True)
