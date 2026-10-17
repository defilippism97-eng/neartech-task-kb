"""Accesso, sessione, impostazioni e protezioni dell'applicazione (fase 6, ADR 0007)."""

import time

import pytest
from fastapi.testclient import TestClient

from neartech.api.app import LogResiliente, crea_app, reindirizza_accesso_fallito
from neartech.api.config import Impostazioni
from supporto_api import OIDC, SCRIVE, _Connessione, _entra, _impostazioni


def test_accesso_di_sviluppo_richiede_l_intestazione(client):
    assert client.post("/accesso/sviluppo", json={"soggetto": "sso|comitato"}).status_code == 403


def test_soggetto_sconosciuto_non_entra(client):
    r = client.post("/accesso/sviluppo", json={"soggetto": "sso|nessuno"}, headers=SCRIVE)
    assert r.status_code == 403


def test_accesso_di_sviluppo_solo_dai_client_locali(conn, mondo):  # noqa: F811
    app = crea_app(_impostazioni(client_sviluppo=("127.0.0.1",)), connetti=lambda: _Connessione(conn),
                   log_dedicato=False)
    with TestClient(app) as c:
        assert c.post("/accesso/sviluppo", json={"soggetto": "sso|admin"}, headers=SCRIVE).status_code == 404


def test_host_non_ammesso(conn, mondo):  # noqa: F811
    app = crea_app(_impostazioni(host_consentiti=("localhost",)), connetti=lambda: _Connessione(conn),
                   log_dedicato=False)
    with TestClient(app) as c:
        assert c.get("/api/salute").status_code == 400


def test_sessione_scaduta(client):
    _entra(client)
    client.app.state.impostazioni = _impostazioni(durata_sessione_ore=0)
    time.sleep(0.01)
    assert client.get("/api/io").status_code == 401


def test_uscita(client):
    _entra(client)
    assert client.post("/accesso/esci").status_code == 403  # senza intestazione
    assert client.post("/accesso/esci", headers=SCRIVE).status_code == 200
    assert client.get("/api/io").status_code == 401


def test_impostazioni_fuori_dallo_sviluppo():
    with pytest.raises(ValueError, match="SSO"):
        Impostazioni(ambiente="produzione", chiave_sessione="x" * 40, url_pubblica="https://neartech.example")
    with pytest.raises(ValueError, match="32"):
        Impostazioni(ambiente="prova", chiave_sessione="corta", oidc=OIDC, url_pubblica="https://x.example")
    with pytest.raises(ValueError, match="sviluppo"):
        Impostazioni(ambiente="produzione", chiave_sessione="x" * 40, oidc=OIDC, url_pubblica="https://x.example",
                     accesso_sviluppo=True)
    with pytest.raises(ValueError, match="URL_PUBBLICA"):
        Impostazioni(ambiente="produzione", chiave_sessione="x" * 40, oidc=OIDC)
    produzione = Impostazioni(ambiente="produzione", chiave_sessione="x" * 40, oidc=OIDC,
                              url_pubblica="https://neartech.example")
    assert produzione.host == ("neartech.example",) and produzione.nome_cookie.startswith("__Host-")
    assert "segreto" not in repr(OIDC) and "x" * 40 not in repr(produzione)


def test_dopo_l_accesso_si_torna_all_applicazione():
    """L'applicazione autenticata sta sotto /app: anche l'accesso non riuscito riporta lì, con il motivo."""
    risposta = reindirizza_accesso_fallito()
    assert risposta.status_code == 303 and risposta.headers["location"] == "/app?accesso=non-riuscito"


def test_l_ambiente_va_dichiarato(monkeypatch):
    monkeypatch.delenv("NEARTECH_AMBIENTE", raising=False)
    with pytest.raises(ValueError, match="NEARTECH_AMBIENTE"):
        Impostazioni.da_ambiente()


def test_intestazioni_di_sicurezza(client):
    r = client.get("/api/salute")
    assert r.headers["x-frame-options"] == "DENY" and "default-src 'self'" in r.headers["content-security-policy"]
    assert "base-uri 'self'" in r.headers["content-security-policy"]
    bloccata = client.post("/api/organizzazioni/sintetica/restituzione/approvazione", json={})
    assert bloccata.status_code == 403 and bloccata.headers["x-frame-options"] == "DENY"


def test_frontend_statico(conn, mondo, tmp_path):  # noqa: F811
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (tmp_path / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path / ".env").write_text("SEGRETO=1", encoding="utf-8")
    (tmp_path / "assets" / "app.js.map").write_text("{}", encoding="utf-8")
    app = crea_app(_impostazioni(cartella_web=tmp_path), connetti=lambda: _Connessione(conn), log_dedicato=False)
    with TestClient(app) as c:
        assert c.get("/favicon.svg").text == "<svg/>"
        assert c.get("/org/aurora/panoramica").text == "<html>app</html>"  # pagina dell'applicazione
        # Sito pubblico alla radice, applicazione autenticata sotto /app: la stessa pagina, che sceglie la vista.
        for percorso in ("/", "/app", "/app/org/aurora/panoramica"):
            assert c.get(percorso).text == "<html>app</html>"
        assert "SEGRETO" not in c.get("/.env").text
        assert c.get("/assets/../../pyproject.toml").text == "<html>app</html>"
        assert c.get("/api/inesistente").status_code == 404


class _Rotta:
    """Connessione che si rompe alla prima scrittura del log."""

    def __init__(self, guasta):
        self.guasta = guasta
        self.closed = False
        self.broken = False
        self.autocommit = False
        self.eseguite = 0

    def execute(self, *_):
        import psycopg
        if self.guasta:
            self.broken = True
            raise psycopg.OperationalError("connessione chiusa dal server")
        self.eseguite += 1

    def close(self):
        self.closed = True


def test_il_log_si_riapre_dopo_una_connessione_persa():
    connessioni = [_Rotta(guasta=True), _Rotta(guasta=False)]
    log = LogResiliente(lambda: connessioni.pop(0))
    log.execute("INSERT ...")
    assert connessioni == [] and log._conn.eseguite == 1 and log._conn.autocommit is True
