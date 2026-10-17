"""Rotte di base dell'API (neartech.api.rotte.base): salute, ambiente, utente corrente, organizzazioni."""

from supporto_api import _entra


def test_salute(client):
    assert client.get("/api/salute").json() == {"stato": "ok"}


def test_ambiente_rivela_solo_il_necessario(client):
    assert client.get("/api/ambiente").json() == {"sso": False, "accesso_sviluppo": True}


def test_senza_accesso_401(client):
    assert client.get("/api/io").status_code == 401


def test_accesso_di_sviluppo_e_ruoli(client):
    _entra(client)
    io = client.get("/api/io").json()
    assert io["soggetto"] == "sso|comitato" and io["ruoli"][0]["ruolo"] == "comitato_guida"


def test_organizzazioni_visibili(client):
    _entra(client)
    assert client.get("/api/organizzazioni").json() == [{"codice": "sintetica", "nome": "Org sintetica"}]
    _entra(client, "sso|estraneo")
    assert client.get("/api/organizzazioni").json() == []


def test_organizzazione_sconosciuta_come_non_consentita(client):
    _entra(client)
    r = client.get("/api/organizzazioni/nessuna/panoramica")
    assert r.status_code == 403 and "nessuna" not in r.text
