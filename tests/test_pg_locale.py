"""Guardia sul database dei test: la preparazione cancella lo schema public."""

import pytest

from pg_locale import DsnNonSicuro, controlla_dsn_di_test


@pytest.mark.parametrize("dsn", [
    "postgresql://u@127.0.0.1:5432/neartech_test",
    "postgresql://u@localhost/neartech_test",
    "host=::1 dbname=neartech_test user=u",
])
def test_dsn_locale_con_test_nel_nome_accettato(dsn, monkeypatch):
    monkeypatch.delenv("NEARTECH_TEST_DSN_REMOTO_CONSENTITO", raising=False)
    controlla_dsn_di_test(dsn)


@pytest.mark.parametrize("dsn", [
    "postgresql://u@db.esempio.eu/neartech_test",
    "host=prod-test.esempio.eu dbname=neartech user=u",
    "postgresql://u@127.0.0.1/contest",
    "postgresql://u@127.0.0.1/neartech",
])
def test_dsn_remoto_o_senza_test_rifiutato(dsn, monkeypatch):
    monkeypatch.delenv("NEARTECH_TEST_DSN_REMOTO_CONSENTITO", raising=False)
    with pytest.raises(DsnNonSicuro):
        controlla_dsn_di_test(dsn)


def test_dsn_remoto_ammesso_solo_con_consenso_esplicito(monkeypatch):
    monkeypatch.setenv("NEARTECH_TEST_DSN_REMOTO_CONSENTITO", "1")
    controlla_dsn_di_test("postgresql://u@db.esempio.eu/neartech_test")
