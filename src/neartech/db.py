"""Connessione a PostgreSQL. Il DSN arriva dall'ambiente, mai dal codice.

Di default si usa la connessione diretta (porta 5432). Se la rete dell'ambiente
blocca quella porta, impostare NEARTECH_DB_VIA=https: il collegamento passa
dall'endpoint SQL HTTPS di Neon (vedi db_https.py).
"""

import os

import psycopg

from neartech.db_https import HttpConnection


def connect(dsn: str | None = None):
    url = dsn or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL non configurata")
    if os.environ.get("NEARTECH_DB_VIA", "").lower() == "https":
        return HttpConnection(url)
    return psycopg.connect(url)
