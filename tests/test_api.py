"""API della piattaforma (fase 6, ADR 0007): accesso, protezioni, panoramica e approvazione del comitato."""

import time

import pytest
from fastapi.testclient import TestClient

from neartech.api.app import INTESTAZIONE_RICHIESTA, LogResiliente, crea_app
from neartech.api.config import Impostazioni, Oidc
from neartech.calcolo import calcola_organizzazione
from neartech.permessi import assegna_ruolo, crea_utente
from test_calcolo import mondo  # noqa: F401

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


@pytest.fixture
def client(conn, mondo):  # noqa: F811
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=200)
    comitato = crea_utente(conn, "sso|comitato")
    assegna_ruolo(conn, comitato, "comitato_guida", mondo["org"], assegnata_da=mondo["admin"])
    crea_utente(conn, "sso|estraneo")
    app = crea_app(_impostazioni(), connetti=lambda: _Connessione(conn), log_dedicato=False)
    with TestClient(app) as c:
        yield c


def _entra(client, soggetto="sso|comitato"):
    r = client.post("/accesso/sviluppo", json={"soggetto": soggetto}, headers=SCRIVE)
    assert r.status_code == 200, r.text


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


def test_l_ambiente_va_dichiarato(monkeypatch):
    monkeypatch.delenv("NEARTECH_AMBIENTE", raising=False)
    with pytest.raises(ValueError, match="NEARTECH_AMBIENTE"):
        Impostazioni.da_ambiente()


def test_panoramica_del_comitato(client):
    _entra(client)
    r = client.get("/api/organizzazioni/sintetica/panoramica")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    corpo = r.json()
    assert corpo["restituzione"]["versione"] == "restituzione-v2"
    assert len(corpo["restituzione"]["occorrenze"]) == 1 and corpo["avanzamento"]["totale"] == 1
    assert corpo["percorso"]["fase_corrente"] == "indirizzi"


def test_indirizzi_senza_questionario_approvato(client):
    _entra(client)
    corpo = client.get("/api/organizzazioni/sintetica/indirizzi").json()
    assert corpo["questionario"] is None and corpo["profilo"] is None
    assert corpo["pesi_in_uso"]["profilo"] == "profilo-prova"


def test_solo_l_amministratore_ricalcola(client):
    _entra(client)
    assert client.post("/api/organizzazioni/sintetica/calcolo", headers=SCRIVE).status_code == 403


def test_organizzazioni_visibili(client):
    _entra(client)
    assert client.get("/api/organizzazioni").json() == [{"codice": "sintetica", "nome": "Org sintetica"}]
    _entra(client, "sso|estraneo")
    assert client.get("/api/organizzazioni").json() == []


def test_panoramica_negata_a_chi_non_legge(client):
    _entra(client, "sso|estraneo")
    r = client.get("/api/organizzazioni/sintetica/panoramica")
    assert r.status_code == 403 and r.json() == {"detail": "operazione non consentita"}


def test_organizzazione_sconosciuta_come_non_consentita(client):
    _entra(client)
    r = client.get("/api/organizzazioni/nessuna/panoramica")
    assert r.status_code == 403 and "nessuna" not in r.text


def test_approvazione_della_restituzione(client):
    _entra(client)
    impronta = client.get("/api/organizzazioni/sintetica/panoramica").json()["restituzione"]["impronta"]
    corpo = {"impronta": impronta, "motivazione": "letta in seduta"}
    assert client.post("/api/organizzazioni/sintetica/restituzione/approvazione", json=corpo).status_code == 403
    r = client.post("/api/organizzazioni/sintetica/restituzione/approvazione", json=corpo, headers=SCRIVE)
    assert r.status_code == 200 and r.json()["impronta"] == impronta
    seconda = client.post("/api/organizzazioni/sintetica/restituzione/approvazione", json=corpo, headers=SCRIVE)
    assert seconda.status_code == 409 and seconda.json() == {"detail": "decisione già presa"}
    assert client.get("/api/organizzazioni/sintetica/panoramica").json()["restituzione"]["approvazione"] == \
        r.json()["atto"]


def test_approvazione_di_una_restituzione_superata(client):
    _entra(client)
    corpo = {"impronta": "0" * 64, "motivazione": "letta in seduta"}
    r = client.post("/api/organizzazioni/sintetica/restituzione/approvazione", json=corpo, headers=SCRIVE)
    assert r.status_code == 409 and r.json() == {"detail": "i risultati sono cambiati dopo la lettura"}


def test_approvazione_con_corpo_non_valido(client):
    _entra(client)
    r = client.post("/api/organizzazioni/sintetica/restituzione/approvazione",
                    json={"impronta": "non-esadecimale", "motivazione": "x"}, headers=SCRIVE)
    assert r.status_code == 422


def test_solo_il_comitato_approva(client):
    _entra(client, "sso|estraneo")
    corpo = {"impronta": "0" * 64, "motivazione": "tentativo"}
    r = client.post("/api/organizzazioni/sintetica/restituzione/approvazione", json=corpo, headers=SCRIVE)
    assert r.status_code == 403


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
