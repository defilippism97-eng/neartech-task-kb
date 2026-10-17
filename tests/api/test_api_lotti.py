"""Rotte dei lotti di abbinamento (neartech.api.rotte.lotti, fetta 5)."""

from supporto_api import SCRIVE, _entra


def test_documenti_e_lotti_secondo_il_ruolo(client):
    _entra(client)  # comitato: legge i lotti, non la pipeline dei documenti
    assert client.get("/api/organizzazioni/sintetica/documenti").status_code == 403
    assert client.get("/api/organizzazioni/sintetica/lotti").json() == []
    assert client.post("/api/organizzazioni/sintetica/abbinamenti/proposta", json={"motivazione": "lotto"},
                       headers=SCRIVE).status_code == 403
