"""Fixture di test: database PostgreSQL dedicato, schema applicato una volta,
ogni test in una transazione annullata a fine test."""

import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

from neartech.migrazioni import CARTELLA_CONDIVISA, applica
from pg_locale import cartella_binari, controlla_dsn_di_test, postgres_temporaneo

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "db" / "schema.sql"


def _prepara(url: str) -> None:
    controlla_dsn_di_test(url)
    # Il database viene ripulito e ricreato dallo schema reale a ogni sessione di test.
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        conn.execute(SCHEMA.read_text(encoding="utf-8"))
        # Le migrazioni si applicano con lo stesso registro usato in produzione.
        applica(conn, CARTELLA_CONDIVISA)


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
    # Transazione esterna sempre annullata: le conn.transaction() del codice diventano
    # savepoint e niente di un test resta nel database della sessione.
    with psycopg.connect(dsn) as c, c.transaction(force_rollback=True):
        yield c
