"""Fixture di test: database PostgreSQL dedicato, schema applicato una volta,
ogni test in una transazione annullata a fine test."""

import os
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "db" / "schema.sql"


@pytest.fixture(scope="session")
def dsn() -> str:
    url = os.environ.get("NEARTECH_TEST_DSN")
    if not url:
        pytest.skip("imposta NEARTECH_TEST_DSN (database PostgreSQL dedicato ai test)")
    dbname = url.rsplit("/", 1)[-1].split("?")[0]
    if "test" not in dbname:
        raise RuntimeError("NEARTECH_TEST_DSN deve puntare a un database il cui nome contiene 'test'")
    # Il database viene ripulito e ricreato dallo schema reale a ogni sessione di test.
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        conn.execute(SCHEMA.read_text(encoding="utf-8"))
        # Le migrazioni si applicano nell'ordine del nome, dopo lo schema (come in produzione).
        for migration in sorted((ROOT / "db" / "migrations").glob("*.sql")):
            conn.execute(migration.read_text(encoding="utf-8"))
    return url


@pytest.fixture
def conn(dsn):
    with psycopg.connect(dsn) as c:
        yield c
        c.rollback()
