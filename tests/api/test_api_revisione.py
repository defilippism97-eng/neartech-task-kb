"""Rotte della revisione sulla rubrica (neartech.api.rotte.revisione)."""

from supporto_api import _entra


def test_la_coda_del_revisore_e_solo_per_chi_giudica(client):
    _entra(client)
    assert client.get("/api/organizzazioni/sintetica/revisione").status_code == 403
