"""Fixture di test: database PostgreSQL dedicato, schema applicato una volta,
ogni test in una transazione annullata a fine test."""

import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

from pg_locale import cartella_binari, postgres_temporaneo

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "db" / "schema.sql"


def _prepara(url: str) -> None:
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


@pytest.fixture(scope="session")
def dsn() -> Iterator[str]:
    url = os.environ.get("NEARTECH_TEST_DSN")
    if url:
        _prepara(url)
        yield url
        return
    # Senza database dedicato si avvia un Postgres locale temporaneo, se i binari ci sono.
    binari = cartella_binari()
    if binari is None:
        pytest.skip("imposta NEARTECH_TEST_DSN o NEARTECH_PG_BIN (vedi docs/sviluppo.md)")
    with postgres_temporaneo(binari) as url:
        _prepara(url)
        yield url


@pytest.fixture
def conn(dsn):
    with psycopg.connect(dsn) as c:
        yield c
        c.rollback()
