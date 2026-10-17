"""Report di audit unico per organizzazione (ADR 0004).

Il report raccoglie in un solo documento verificabile: atti dell'organizzazione con i testi letti dal
suo spazio, parametri usati e loro adozione, indirizzi, ruoli, campioni e misure, controlli di integrità.
"""

import json

import pytest

from neartech.audit import VERSIONE_REPORT, report_in_markdown, report_organizzazione
from neartech.governance import (
    adotta_parametro_comune,
    approva_indirizzo,
    approva_parametro,
    proponi_indirizzo,
    proponi_parametro,
    segnala,
)
from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore
from neartech.registro import ancora_catena


@pytest.fixture
def org(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    org_id = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    comitato = crea_utente(conn, "sso|comitato")
    revisore = crea_utente(conn, "sso|revisore")
    auditor = crea_utente(conn, "sso|auditor")
    assegna_ruolo(conn, comitato, "comitato_guida", org_id, assegnata_da=admin)
    assegna_ruolo(conn, revisore, "revisore", org_id, assegnata_da=admin)
    assegna_ruolo(conn, auditor, "auditor", assegnata_da=admin)
    comune = proponi_parametro(conn, admin, codice="soglia_prova", valore={"valore": 0.9},
                               descrizione="soglia comune", motivazione="valore iniziale", org_id=None)
    approva_parametro(conn, admin, comune, motivazione="approvato")
    adotta_parametro_comune(conn, comitato, org_id=org_id, parametro_id=comune, motivazione="adatto a noi")
    indirizzo = proponi_indirizzo(conn, comitato, org_id=org_id, codice="relazione", testo="Tutelare la relazione",
                                  ambito="Accoglienza", motivazione="valore dell'organizzazione")
    approva_indirizzo(conn, comitato, indirizzo, motivazione="approvato in seduta")
    segnala(conn, revisore, org_id=org_id, tipo_oggetto="indirizzo", oggetto_id=indirizzo,
            motivazione="ricaduta da verificare")
    return {"id": org_id, "admin": admin, "comitato": comitato, "revisore": revisore, "auditor": auditor,
            "comune": comune, "indirizzo": indirizzo}


def test_report_contiene_i_testi_dallo_spazio(conn, org):
    report = report_organizzazione(conn, org["auditor"], org["id"])
    assert report["versione_report"] == VERSIONE_REPORT
    assert report["organizzazione"]["codice"] == "sintetica"
    motivazioni = [a["motivazione"] for a in report["atti"]]
    assert "adatto a noi" in motivazioni and "ricaduta da verificare" in motivazioni
    assert all(a["motivazione"] != "nello spazio dell'organizzazione" for a in report["atti"])
    assert [(i["codice"], i["testo"], i["stato"]) for i in report["indirizzi"]] == [
        ("relazione", "Tutelare la relazione", "approvazione")
    ]
    assert report["campioni"] == []


def test_report_dice_chi_ha_deciso_e_se_coincide_col_proponente(conn, org):
    report = report_organizzazione(conn, org["auditor"], org["id"])
    approvazione = next(a for a in report["atti"] if a["tipo_oggetto"] == "indirizzo" and a["atto"] == "approvazione")
    assert approvazione["autore"] == "sso|comitato"
    assert approvazione["dettagli"]["stesso_proponente"] is True


def test_report_riporta_i_parametri_comuni_e_la_loro_adozione(conn, org):
    report = report_organizzazione(conn, org["auditor"], org["id"])
    assert [(p["codice"], p["stato"], p["valore"]) for p in report["parametri_comuni"]] == [
        ("soglia_prova", "adottato", {"valore": 0.9})
    ]


def test_report_riporta_ruoli_e_integrita(conn, org):
    ancora = ancora_catena(conn)
    report = report_organizzazione(conn, org["auditor"], org["id"], ancora=ancora)
    assert sorted(r["ruolo"] for r in report["ruoli"]) == ["comitato_guida", "revisore"]
    assert report["integrita"] == {"catena": "integra", "ancora": list(ancora), "testi": [], "contenuti": []}


def test_report_segnala_un_testo_alterato(conn, org):
    conn.execute("ALTER TABLE org_sintetica.testi_atti DISABLE TRIGGER testi_atti_append_only")
    conn.execute("UPDATE org_sintetica.testi_atti SET motivazione = 'alterata' WHERE motivazione = 'adatto a noi'")
    report = report_organizzazione(conn, org["auditor"], org["id"])
    assert [p["problema"] for p in report["integrita"]["testi"]] == ["hash diverso"]


def test_report_non_include_altre_organizzazioni(conn, org):
    altra = crea_organizzazione(conn, org["admin"], nome="Altra", codice="altra")
    report = report_organizzazione(conn, org["auditor"], org["id"])
    assert all(a["oggetto_id"] != altra for a in report["atti"])


def test_report_riservato_all_audit(conn, org):
    with pytest.raises(PermessoNegato):
        report_organizzazione(conn, org["revisore"], org["id"])


def test_report_serializzabile_e_leggibile(conn, org):
    report = report_organizzazione(conn, org["auditor"], org["id"])
    json.dumps(report)
    testo = report_in_markdown(report)
    assert "# Report di audit" in testo and "Tutelare la relazione" in testo and "adottato" in testo
