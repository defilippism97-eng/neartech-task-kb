"""Rotte della panoramica (neartech.api.rotte.panoramica): home del comitato, ricalcolo, approvazione della
restituzione."""

from supporto_api import SCRIVE, _entra


def test_panoramica_del_comitato(client):
    _entra(client)
    r = client.get("/api/organizzazioni/sintetica/panoramica")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    corpo = r.json()
    assert corpo["restituzione"]["versione"] == "restituzione-v2"
    assert len(corpo["restituzione"]["occorrenze"]) == 1 and corpo["avanzamento"]["totale"] == 1
    assert corpo["percorso"]["fase_corrente"] == "indirizzi"


def test_solo_l_amministratore_ricalcola(client):
    _entra(client)
    assert client.post("/api/organizzazioni/sintetica/calcolo", headers=SCRIVE).status_code == 403


def test_panoramica_negata_a_chi_non_legge(client):
    _entra(client, "sso|estraneo")
    r = client.get("/api/organizzazioni/sintetica/panoramica")
    assert r.status_code == 403 and r.json() == {"detail": "operazione non consentita"}


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
