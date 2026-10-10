"""Connessione a PostgreSQL. Il DSN arriva dall'ambiente, mai dal codice."""

import os

import psycopg


def connect(dsn: str | None = None) -> psycopg.Connection:
    url = dsn or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL non configurata")
    return psycopg.connect(url)
