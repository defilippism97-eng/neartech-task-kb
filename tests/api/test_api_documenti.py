"""Rotte della pipeline dei documenti (neartech.api.rotte.documenti, fetta 5)."""

import base64

from supporto_api import SCRIVE, _entra
from test_pipeline import RIGHE, docx


def test_caricamento_di_un_mansionario_dall_api(client):
    _entra(client, "sso|admin")
    contenuto = base64.b64encode(docx(RIGHE)).decode()
    r = client.post("/api/organizzazioni/sintetica/documenti", json={"nome_file": "m.docx", "contenuto": contenuto},
                    headers=SCRIVE)
    assert r.status_code == 200, r.text
    assert r.json()["nuovo"] and r.json()["ruolo"] == "Impiegato amministrativo"
    stato = client.get("/api/organizzazioni/sintetica/documenti").json()
    assert [d["stato"] for d in stato["documenti"]] == ["da_avviare"] and stato["prezzi"] is None
    # Senza parametro dei prezzi la scomposizione non parte: nessun job.
    r = client.post("/api/organizzazioni/sintetica/documenti/scomposizione",
                    json={"caricamenti": [r.json()["caricamento_id"]], "motivazione": "avvio"}, headers=SCRIVE)
    assert r.status_code == 422


def test_caricamento_non_valido(client):
    _entra(client, "sso|admin")
    r = client.post("/api/organizzazioni/sintetica/documenti", json={"nome_file": "m.docx", "contenuto": "%%%"},
                    headers=SCRIVE)
    assert r.status_code == 422 and r.json()["detail"] == "dati non validi"
