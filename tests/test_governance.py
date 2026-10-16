"""Registro delle decisioni, parametri di governance e indirizzi del comitato guida.

Il registro è append-only con catena di hash. Parametri e indirizzi sono versionati:
lo stato di ogni versione si ricava dagli atti nel registro, non da colonne aggiornate.
"""

import psycopg
import pytest

from neartech.governance import (
    DecisioneGiaPresa,
    ParametroAssente,
    approva_indirizzo,
    approva_parametro,
    indirizzi_vigenti,
    parametro_vigente,
    proponi_indirizzo,
    proponi_parametro,
    rifiuta_parametro,
    ritira_parametro,
    segnala,
)
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente
from neartech.registro import registra, verifica_catena


@pytest.fixture
def org(conn):
    org_id = str(conn.execute(
        "INSERT INTO organizations (name) VALUES ('Org sintetica') RETURNING org_id"
    ).fetchone()[0])
    comitato = crea_utente(conn, "sso|comitato")
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, comitato, "comitato_guida", org_id)
    assegna_ruolo(conn, revisore, "revisore", org_id)
    return {"id": org_id, "comitato": comitato, "revisore": revisore}


# --- registro --------------------------------------------------------------

def _atto(conn, org, **kw):
    base = {"autore_id": org["comitato"], "tipo_oggetto": "prova", "oggetto_id": "x",
            "atto": "proposta", "motivazione": "motivazione sintetica", "org_id": org["id"]}
    return registra(conn, **{**base, **kw})


def test_registro_assegna_posizioni_crescenti_e_catena_valida(conn, org):
    primo = _atto(conn, org)
    secondo = _atto(conn, org, oggetto_id="y")
    posizioni = [r[0] for r in conn.execute(
        "SELECT posizione FROM registro_decisioni WHERE decisione_id IN (%s, %s) ORDER BY decisione_id",
        (primo, secondo),
    ).fetchall()]
    assert posizioni[1] == posizioni[0] + 1
    assert verifica_catena(conn) is None


@pytest.mark.parametrize("comando", [
    "UPDATE registro_decisioni SET motivazione = 'altro'",
    "DELETE FROM registro_decisioni",
])
def test_registro_non_si_modifica(conn, org, comando):
    _atto(conn, org)
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute(comando)


def test_motivazione_obbligatoria(conn, org):
    with pytest.raises(psycopg.errors.CheckViolation):
        _atto(conn, org, motivazione="   ")


def test_manomissione_rilevata_dalla_verifica(conn, org):
    _atto(conn, org)
    manomessa = _atto(conn, org, oggetto_id="y")
    _atto(conn, org, oggetto_id="z")
    conn.execute("ALTER TABLE registro_decisioni DISABLE TRIGGER registro_append_only")
    conn.execute("UPDATE registro_decisioni SET motivazione = 'riscritta' WHERE decisione_id = %s", (manomessa,))
    attesa = conn.execute(
        "SELECT posizione FROM registro_decisioni WHERE decisione_id = %s", (manomessa,)
    ).fetchone()[0]
    assert verifica_catena(conn) == attesa


def test_correzione_e_una_riga_nuova(conn, org):
    originale = _atto(conn, org)
    correzione = _atto(conn, org, atto="correzione", corregge_id=originale, motivazione="corregge un errore")
    righe = dict(conn.execute(
        "SELECT decisione_id, motivazione FROM registro_decisioni WHERE decisione_id IN (%s, %s)",
        (originale, correzione),
    ).fetchall())
    assert righe == {originale: "motivazione sintetica", correzione: "corregge un errore"}


# --- parametri --------------------------------------------------------------

def _proponi(conn, org, valore, codice="soglia_prova"):
    return proponi_parametro(
        conn, org["comitato"], codice=codice, valore=valore,
        descrizione="parametro sintetico", motivazione="proposta sintetica", org_id=org["id"],
    )


def test_parametro_approvato_diventa_vigente_con_le_sue_chiavi(conn, org):
    parametro = _proponi(conn, org, {"valore": 0.9})
    approva_parametro(conn, org["comitato"], parametro, motivazione="approvato")
    vigente = parametro_vigente(conn, "soglia_prova", org["id"])
    assert vigente.valore == {"valore": 0.9}
    assert vigente.versione == 1
    assert vigente.parametro_id == parametro
    assert vigente.approvazione_id is not None


def test_parametro_solo_proposto_non_e_vigente(conn, org):
    _proponi(conn, org, {"valore": 0.9})
    with pytest.raises(ParametroAssente):
        parametro_vigente(conn, "soglia_prova", org["id"])


def test_revisore_non_propone_parametri(conn, org):
    with pytest.raises(PermessoNegato):
        proponi_parametro(conn, org["revisore"], codice="soglia_prova", valore={"valore": 1},
                          descrizione="x", motivazione="x", org_id=org["id"])


def test_versione_nuova_approvata_sostituisce_la_precedente(conn, org):
    approva_parametro(conn, org["comitato"], _proponi(conn, org, {"valore": 0.9}), motivazione="ok")
    seconda = _proponi(conn, org, {"valore": 0.85})
    approva_parametro(conn, org["comitato"], seconda, motivazione="ok")
    vigente = parametro_vigente(conn, "soglia_prova", org["id"])
    assert (vigente.versione, vigente.valore) == (2, {"valore": 0.85})


def test_versione_rifiutata_non_diventa_vigente(conn, org):
    approva_parametro(conn, org["comitato"], _proponi(conn, org, {"valore": 0.9}), motivazione="ok")
    rifiuta_parametro(conn, org["comitato"], _proponi(conn, org, {"valore": 0.5}), motivazione="troppo bassa")
    assert parametro_vigente(conn, "soglia_prova", org["id"]).valore == {"valore": 0.9}


def test_ritiro_non_riattiva_la_versione_precedente(conn, org):
    approva_parametro(conn, org["comitato"], _proponi(conn, org, {"valore": 0.9}), motivazione="ok")
    seconda = _proponi(conn, org, {"valore": 0.85})
    approva_parametro(conn, org["comitato"], seconda, motivazione="ok")
    ritira_parametro(conn, org["comitato"], seconda, motivazione="ritirata")
    with pytest.raises(ParametroAssente):
        parametro_vigente(conn, "soglia_prova", org["id"])


def test_una_versione_si_decide_una_volta(conn, org):
    parametro = _proponi(conn, org, {"valore": 0.9})
    rifiuta_parametro(conn, org["comitato"], parametro, motivazione="no")
    with pytest.raises(DecisioneGiaPresa):
        approva_parametro(conn, org["comitato"], parametro, motivazione="ripensamento")


def test_parametro_globale_non_proponibile_dal_comitato(conn, org):
    """Chi approva i parametri NEARTECH comuni a tutte le organizzazioni non è ancora deciso."""
    with pytest.raises(PermessoNegato):
        proponi_parametro(conn, org["comitato"], codice="soglia_prova", valore={"valore": 0.9},
                          descrizione="x", motivazione="x", org_id=None)


def test_parametri_non_si_modificano(conn, org):
    _proponi(conn, org, {"valore": 0.9})
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("UPDATE parametri_governance SET valore = '{\"valore\": 0.1}'")


# --- indirizzi del comitato ------------------------------------------------------

def test_indirizzo_approvato_e_vigente(conn, org):
    indirizzo = proponi_indirizzo(
        conn, org["comitato"], org_id=org["id"], codice="relazione_utenti_fragili",
        testo="Tutelare la relazione diretta con gli utenti fragili",
        ambito="Task di accoglienza e assistenza diretta", motivazione="valore dell'organizzazione",
    )
    approva_indirizzo(conn, org["comitato"], indirizzo, motivazione="approvato in seduta")
    vigenti = indirizzi_vigenti(conn, org["id"])
    assert [(i.codice, i.versione) for i in vigenti] == [("relazione_utenti_fragili", 1)]


def test_revisore_non_propone_indirizzi(conn, org):
    with pytest.raises(PermessoNegato):
        proponi_indirizzo(conn, org["revisore"], org_id=org["id"], codice="x", testo="x",
                          ambito="x", motivazione="x")


def test_revisore_segnala_una_ricaduta_anomala(conn, org):
    indirizzo = proponi_indirizzo(conn, org["comitato"], org_id=org["id"], codice="x", testo="x",
                                  ambito="x", motivazione="x")
    decisione = segnala(conn, org["revisore"], org_id=org["id"], tipo_oggetto="indirizzo",
                        oggetto_id=indirizzo, motivazione="ricade su un solo task")
    atto = conn.execute(
        "SELECT atto, tipo_oggetto FROM registro_decisioni WHERE decisione_id = %s", (decisione,)
    ).fetchone()
    assert atto == ("segnalazione", "indirizzo")


def test_comitato_non_segnala(conn, org):
    with pytest.raises(PermessoNegato):
        segnala(conn, org["comitato"], org_id=org["id"], tipo_oggetto="indirizzo",
                oggetto_id="x", motivazione="x")
