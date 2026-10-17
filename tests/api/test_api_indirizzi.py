"""Rotte degli indirizzi (neartech.api.rotte.indirizzi)."""

from supporto_api import _entra


def test_indirizzi_senza_questionario_approvato(client):
    _entra(client)
    corpo = client.get("/api/organizzazioni/sintetica/indirizzi").json()
    assert corpo["questionario"] is None and corpo["profilo"] is None
    assert corpo["pesi_in_uso"]["profilo"] == "profilo-prova"
