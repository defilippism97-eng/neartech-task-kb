"""Indirizzi del comitato: questionario, profilo di pesi, approvazione e verifica dell'auditor (fase 6, fetta 3)."""

import json
from pathlib import Path

import psycopg
import pytest

from neartech.governance import DecisioneGiaPresa, approva_parametro, proponi_parametro
from neartech.indirizzi_pesi import (PARAMETRO_QUESTIONARIO, QuestionarioNonApprovato, approva_profilo,
                                     pesi_dalle_risposte, proponi_profilo, stato_indirizzi, verifica_profilo)
from neartech.percorso import stato_percorso
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente
from test_calcolo import mondo  # noqa: F401

BOZZA = json.loads((Path(__file__).resolve().parents[1] / "docs" / "governance" /
                    "questionario-indirizzi-bozza-1.json").read_text(encoding="utf-8"))
BASE = {"d1": 0.25, "d2": 0.25, "d3": 0.25, "d4": 0.25}
NEUTRE = {d["codice"]: 2 for d in BOZZA["domande"]}


@pytest.fixture
def attori(conn, mondo):  # noqa: F811
    p = proponi_parametro(conn, mondo["admin"], codice=PARAMETRO_QUESTIONARIO, valore=BOZZA,
                          descrizione="questionario degli indirizzi", motivazione="prova", org_id=None)
    approva_parametro(conn, mondo["admin"], p, motivazione="prova")
    comitato, auditor, revisore = (crea_utente(conn, f"sso|{x}") for x in ("comitato", "auditor", "revisore"))
    assegna_ruolo(conn, comitato, "comitato_guida", mondo["org"], assegnata_da=mondo["admin"])
    assegna_ruolo(conn, auditor, "auditor", assegnata_da=mondo["admin"])
    assegna_ruolo(conn, revisore, "revisore", mondo["org"], assegnata_da=mondo["admin"])
    return mondo | {"comitato": comitato, "auditor": auditor, "revisore": revisore}


def test_risposte_neutre_lasciano_i_pesi():
    assert pesi_dalle_risposte(BASE, BOZZA, NEUTRE) == BASE


def test_la_relazione_pesa_di_piu_restando_nei_limiti():
    risposte = NEUTRE | {"d1a": 4, "d1b": 0, "d3a": 0, "d3b": 4}
    pesi = pesi_dalle_risposte(BASE, BOZZA, risposte)
    assert pesi["d1"] > 0.25 > pesi["d3"] and abs(sum(pesi.values()) - 1) < 1e-9
    assert all(BOZZA["limiti"]["min"] <= p <= BOZZA["limiti"]["max"] for p in pesi.values())


def test_il_flusso_completo_attiva_il_profilo(conn, attori):
    risposte = NEUTRE | {"d1a": 4, "d4a": 4}
    profilo = proponi_profilo(conn, attori["comitato"], attori["org"], risposte, nota="seduta del 20 ottobre")
    stato = stato_indirizzi(conn, attori["comitato"], attori["org"])
    assert stato["profilo"]["profile_id"] == profilo and stato["profilo"]["attivo"] is False
    assert stato["profilo"]["pesi"]["d1"] > 0.25 and stato["profilo"]["effetto"]["occorrenze"] == 2
    approva_profilo(conn, attori["comitato"], attori["org"], profilo, motivazione="approvato in seduta")
    assert stato_indirizzi(conn, attori["comitato"], attori["org"])["profilo"]["attivo"] is False
    verifica_profilo(conn, attori["auditor"], attori["org"], profilo, motivazione="controlli superati")
    assert stato_indirizzi(conn, attori["comitato"], attori["org"])["profilo"]["attivo"] is True
    fasi = {f["codice"]: f["stato"] for f in stato_percorso(conn, attori["comitato"], attori["org"])["fasi"]}
    assert fasi["indirizzi"] == "fatta"


def test_l_auditor_verifica_solo_dopo_il_comitato(conn, attori):
    profilo = proponi_profilo(conn, attori["comitato"], attori["org"], NEUTRE, nota="prova")
    with pytest.raises(DecisioneGiaPresa, match="comitato"):
        verifica_profilo(conn, attori["auditor"], attori["org"], profilo, motivazione="troppo presto")


def test_solo_il_comitato_approva_e_solo_l_auditor_verifica(conn, attori):
    profilo = proponi_profilo(conn, attori["comitato"], attori["org"], NEUTRE, nota="prova")
    with pytest.raises(PermessoNegato):
        approva_profilo(conn, attori["revisore"], attori["org"], profilo, motivazione="x")
    approva_profilo(conn, attori["comitato"], attori["org"], profilo, motivazione="ok")
    with pytest.raises(PermessoNegato):
        verifica_profilo(conn, attori["comitato"], attori["org"], profilo, motivazione="x")


def test_risposte_incomplete_rifiutate(conn, attori):
    with pytest.raises(ValueError, match="ogni domanda"):
        proponi_profilo(conn, attori["comitato"], attori["org"], {"d1a": 3}, nota="prova")


def test_senza_questionario_approvato(conn, mondo):  # noqa: F811
    comitato = crea_utente(conn, "sso|comitato")
    assegna_ruolo(conn, comitato, "comitato_guida", mondo["org"], assegnata_da=mondo["admin"])
    assert stato_indirizzi(conn, comitato, mondo["org"])["questionario"] is None
    with pytest.raises(QuestionarioNonApprovato):
        proponi_profilo(conn, comitato, mondo["org"], NEUTRE, nota="prova")


def test_il_database_non_attiva_un_profilo_senza_i_due_atti(conn, attori):
    profilo = proponi_profilo(conn, attori["comitato"], attori["org"], NEUTRE, nota="prova")
    conn.execute("SET LOCAL ROLE neartech_app")
    with pytest.raises(psycopg.errors.RaiseException, match="approvazione del comitato e la verifica"):
        with conn.transaction():
            conn.execute("UPDATE weight_profiles SET is_active = true WHERE profile_id = %s", (profilo,))
