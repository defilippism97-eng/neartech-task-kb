"""Percorso del pilota: le fasi si calcolano dai dati (fase 6)."""

import pytest

from neartech.calcolo import calcola_organizzazione
from neartech.governance import approva_parametro, proponi_parametro
from neartech.percorso import stato_percorso
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente
from neartech.restituzione import PARAMETRO_STABILITA, approva_restituzione, restituzione_organizzazione
from test_calcolo import mondo  # noqa: F401


def _fasi(p):
    return {f["codice"]: f["stato"] for f in p["fasi"]}


def test_prima_del_calcolo_siamo_agli_indirizzi(conn, mondo):  # noqa: F811
    p = stato_percorso(conn, mondo["admin"], mondo["org"])
    assert _fasi(p) == {"avvio": "fatta", "indirizzi": "in_corso", "verifica": "da_fare", "esito": "da_fare"}
    assert p["fase_corrente"] == "indirizzi" and p["fasi"][0]["fatti"]["occorrenze"] == 2


def test_risultati_con_il_profilo_comune_restano_provvisori(conn, mondo):  # noqa: F811
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    p = stato_percorso(conn, mondo["admin"], mondo["org"])
    assert _fasi(p)["verifica"] == "in_corso" and p["fase_corrente"] == "indirizzi"
    assert p["fasi"][1]["fatti"] == {"profilo_proprio": None, "profilo_in_uso": "profilo-prova", "proposta": None}


def test_con_profilo_proprio_e_restituzione_approvata_il_percorso_e_concluso(conn, mondo):  # noqa: F811
    conn.execute("UPDATE weight_profiles SET is_active = false")
    conn.execute("""INSERT INTO weight_profiles (profile_id, org_id, w_k1, w_k2, w_k3, lambda_r, w_d1, w_d2, w_d3, w_d4,
                                                 theta_n, theta_d, is_active, approved_by, approved_at)
                    VALUES ('profilo-org', %s, 0.4, 0.4, 0.2, 0.5, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5, true,
                            'comitato', now())""", (mondo["org"],))
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    p = proponi_parametro(conn, mondo["admin"], codice=PARAMETRO_STABILITA, valore={"valore": 0.8},
                          descrizione="soglia", motivazione="prova", org_id=None)
    approva_parametro(conn, mondo["admin"], p, motivazione="prova")
    percorso = stato_percorso(conn, mondo["admin"], mondo["org"])
    assert _fasi(percorso) == {"avvio": "fatta", "indirizzi": "fatta", "verifica": "fatta", "esito": "in_corso"}
    comitato = crea_utente(conn, "sso|comitato")
    assegna_ruolo(conn, comitato, "comitato_guida", mondo["org"], assegnata_da=mondo["admin"])
    approva_restituzione(conn, comitato, mondo["org"], restituzione_organizzazione(conn, comitato, mondo["org"]),
                         motivazione="letta")
    finale = stato_percorso(conn, comitato, mondo["org"])
    assert _fasi(finale)["esito"] == "fatta" and finale["fase_corrente"] == "esito"


def test_il_percorso_richiede_di_poter_leggere(conn, mondo):  # noqa: F811
    with pytest.raises(PermessoNegato):
        stato_percorso(conn, crea_utente(conn, "sso|estraneo"), mondo["org"])
