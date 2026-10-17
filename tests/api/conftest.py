"""Fixture dei test dell'API (fase 6, ADR 0007), condivise da tutti i file tests/api/test_api_<area>.py.

`client`: applicazione con l'organizzazione sintetica di test_calcolo già calcolata, un membro del comitato guida
(sso|comitato) e un utente senza ruoli (sso|estraneo). Gli aiuti (SCRIVE, _entra, ...) stanno in supporto_api.
Una corsia che ha bisogno di una fixture sua la aggiunge in fondo, in un blocco separato con il suo nome.
"""

import pytest
from fastapi.testclient import TestClient

from neartech.api.app import crea_app
from neartech.calcolo import calcola_organizzazione
from neartech.permessi import assegna_ruolo, crea_utente
from supporto_api import _Connessione, _impostazioni
from test_calcolo import mondo  # noqa: F401


@pytest.fixture
def client(conn, mondo):  # noqa: F811
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=200)
    comitato = crea_utente(conn, "sso|comitato")
    assegna_ruolo(conn, comitato, "comitato_guida", mondo["org"], assegnata_da=mondo["admin"])
    crea_utente(conn, "sso|estraneo")
    app = crea_app(_impostazioni(), connetti=lambda: _Connessione(conn), log_dedicato=False)
    with TestClient(app) as c:
        yield c
