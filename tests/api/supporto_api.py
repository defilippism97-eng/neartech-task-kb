"""Aiuti condivisi dai test dell'API (tests/api): intestazione delle scritture, impostazioni di sviluppo, connessione
del test vista dall'applicazione, accesso di sviluppo. La fixture `client` sta in tests/api/conftest.py.

Il nome del modulo è unico in tutta la cartella dei test: i test lo importano direttamente (from supporto_api ...).
"""

from neartech.api.app import INTESTAZIONE_RICHIESTA
from neartech.api.config import Impostazioni, Oidc

SCRIVE = {INTESTAZIONE_RICHIESTA: "1"}
OIDC = Oidc("entra", "https://login.example/.well-known/openid-configuration", "id", "segreto")


class _Connessione:
    """La connessione del test vista dall'API: commit, rollback e chiusura spettano al test (force_rollback)."""

    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, nome):
        return getattr(self._conn, nome)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def _impostazioni(**altre):
    valori = {"ambiente": "sviluppo", "chiave_sessione": "", "accesso_sviluppo": True,
              "client_sviluppo": ("testclient",), "host_consentiti": ("testserver",)} | altre
    return Impostazioni(**valori)


def _entra(client, soggetto="sso|comitato"):
    r = client.post("/accesso/sviluppo", json={"soggetto": soggetto}, headers=SCRIVE)
    assert r.status_code == 200, r.text
