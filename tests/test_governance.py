"""Registro delle decisioni, parametri di governance e indirizzi del comitato guida.

Il registro è append-only con catena di hash. Parametri e indirizzi sono versionati:
lo stato di ogni versione si ricava dagli atti nel registro, non da colonne aggiornate.
"""

import psycopg
import pytest

from neartech.governance import (
    DecisioneGiaPresa,
    ParametroAssente,
    ParametroRitirato,
    approva_indirizzo,
    approva_parametro,
    indirizzi_vigenti,
    parametro_vigente,
    proponi_indirizzo,
    proponi_parametro,
    rifiuta_parametro,
    ritira_parametro,
    segnala,
    verifica_contenuti,
)
from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore
from neartech.registro import ancora_catena, registra, verifica_catena


@pytest.fixture
def org(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    org_id = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    comitato = crea_utente(conn, "sso|comitato")
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, comitato, "comitato_guida", org_id, assegnata_da=admin)
    assegna_ruolo(conn, revisore, "revisore", org_id, assegnata_da=admin)
    return {"id": org_id, "comitato": comitato, "revisore": revisore, "admin": admin}


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
    with pytest.raises(ValueError, match="motivazione"):
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
    # Le motivazioni di un'organizzazione stanno nel suo spazio (ADR 0004).
    righe = dict(conn.execute(
        "SELECT decisione_id, motivazione FROM org_sintetica.testi_atti WHERE decisione_id IN (%s, %s)",
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


# --- rafforzamenti dopo la revisione ---------------------------------------------

def test_coda_cancellata_rilevata_con_l_ancora(conn, org):
    _atto(conn, org, org_id=None)
    ancora = ancora_catena(conn)
    _atto(conn, org, oggetto_id="y", org_id=None)
    conn.execute("ALTER TABLE registro_decisioni DISABLE TRIGGER registro_append_only")
    conn.execute("DELETE FROM registro_decisioni WHERE posizione >= %s", (ancora[0],))
    assert verifica_catena(conn, ancora=ancora) == ancora[0]


def test_atto_decisivo_senza_oggetto_rifiutato(conn, org):
    with pytest.raises(psycopg.errors.RaiseException):
        _atto(conn, org, tipo_oggetto="parametro", oggetto_id="00000000-0000-0000-0000-000000000009",
              atto="approvazione")


def test_seconda_decisione_rifiutata_dal_database(conn, org):
    parametro = _proponi(conn, org, {"valore": 0.9})
    approva_parametro(conn, org["comitato"], parametro, motivazione="ok")
    with pytest.raises(psycopg.errors.UniqueViolation):
        _atto(conn, org, tipo_oggetto="parametro", oggetto_id=parametro, atto="rifiuto")


def test_ritiro_dell_organizzazione_non_ricade_sul_valore_comune(conn, org):
    comune = "00000000-0000-0000-0000-0000000000cc"
    proposta = registra(conn, autore_id=org["admin"], tipo_oggetto="parametro", oggetto_id=comune,
                        atto="proposta", motivazione="valore comune sintetico")
    conn.execute(
        """INSERT INTO parametri_governance (parametro_id, codice, org_id, versione, valore, descrizione, proposta_id)
           VALUES (%s, 'soglia_prova', NULL, 1, '{"valore": 0.8}', 'comune', %s)""",
        (comune, proposta),
    )
    registra(conn, autore_id=org["admin"], tipo_oggetto="parametro", oggetto_id=comune,
             atto="approvazione", motivazione="approvato")
    propria = _proponi(conn, org, {"valore": 0.9})
    approva_parametro(conn, org["comitato"], propria, motivazione="ok")
    ritira_parametro(conn, org["comitato"], propria, motivazione="ritirata")
    with pytest.raises(ParametroRitirato):
        parametro_vigente(conn, "soglia_prova", org["id"])


def test_contenuto_degli_indirizzi_verificato(conn, org):
    indirizzo = proponi_indirizzo(conn, org["comitato"], org_id=org["id"], codice="x", testo="testo originale",
                                  ambito="ambito", motivazione="x")
    assert verifica_contenuti(conn) == []
    conn.execute("ALTER TABLE org_sintetica.testi_indirizzi DISABLE TRIGGER testi_indirizzi_append_only")
    conn.execute("UPDATE org_sintetica.testi_indirizzi SET testo = 'testo cambiato' WHERE indirizzo_id = %s",
                 (indirizzo,))
    assert verifica_contenuti(conn) == [("indirizzo", indirizzo)]


@pytest.mark.parametrize("tabella", ["parametri_governance", "indirizzi_comitato", "stati_validazione_task"])
def test_truncate_vietato(conn, tabella):
    # Rifiutato dal trigger, o prima ancora dalle chiavi esterne che puntano alla tabella (es. misure_precisione).
    with pytest.raises((psycopg.errors.RaiseException, psycopg.errors.FeatureNotSupported)):
        conn.execute(f"TRUNCATE {tabella}")


# --- santa-loop, giro 1 -----------------------------------------------------------

def test_versione_superata_non_si_approva(conn, org):
    prima = _proponi(conn, org, {"valore": 0.9})
    seconda = _proponi(conn, org, {"valore": 0.85})
    approva_parametro(conn, org["comitato"], seconda, motivazione="ok")
    with pytest.raises(DecisioneGiaPresa):
        approva_parametro(conn, org["comitato"], prima, motivazione="tardiva")


def test_segnalazione_solo_su_oggetti_della_propria_organizzazione(conn, org):
    altra = crea_organizzazione(conn, org["admin"], nome="Altra", codice="altra")
    comitato_altra = crea_utente(conn, "sso|comitato-altra")
    assegna_ruolo(conn, comitato_altra, "comitato_guida", altra, assegnata_da=org["admin"])
    indirizzo = proponi_indirizzo(conn, comitato_altra, org_id=altra, codice="x", testo="x",
                                  ambito="x", motivazione="x")
    with pytest.raises(LookupError):
        segnala(conn, org["revisore"], org_id=org["id"], tipo_oggetto="indirizzo",
                oggetto_id=indirizzo, motivazione="x")


def test_contenuto_dei_parametri_verifica_l_organizzazione(conn, org):
    parametro = _proponi(conn, org, {"valore": 0.9})
    altra = str(conn.execute("INSERT INTO organizations (name) VALUES ('Altra') RETURNING org_id").fetchone()[0])
    conn.execute("ALTER TABLE parametri_governance DISABLE TRIGGER parametri_append_only")
    conn.execute("UPDATE parametri_governance SET org_id = %s WHERE parametro_id = %s", (altra, parametro))
    assert verifica_contenuti(conn) == [("parametro", parametro)]


# --- santa-loop, giro 2 -----------------------------------------------------------

def test_identificativi_in_maiuscolo_accettati(conn, org):
    parametro = _proponi(conn, org, {"valore": 0.9})
    approva_parametro(conn, org["comitato"], parametro.upper(), motivazione="ok")
    assert parametro_vigente(conn, "soglia_prova", org["id"]).parametro_id == parametro


# --- proponente e approvatore (metodologia, sezione 10, decisione e) ---------------

def _dettagli(conn, decisione_id):
    return conn.execute("SELECT dettagli FROM registro_decisioni WHERE decisione_id = %s", (decisione_id,)).fetchone()[0]


def test_approvazione_dello_stesso_proponente_ammessa_e_segnata(conn, org):
    atto = approva_parametro(conn, org["comitato"], _proponi(conn, org, {"valore": 0.9}), motivazione="ok")
    assert _dettagli(conn, atto)["stesso_proponente"] is True


def test_approvazione_di_un_altro_membro_segnata(conn, org):
    secondo = crea_utente(conn, "sso|comitato-2")
    assegna_ruolo(conn, secondo, "comitato_guida", org["id"], assegnata_da=org["admin"])
    atto = approva_parametro(conn, secondo, _proponi(conn, org, {"valore": 0.9}), motivazione="ok")
    assert _dettagli(conn, atto)["stesso_proponente"] is False


def test_rifiuto_e_ritiro_segnano_il_proponente(conn, org):
    rifiuto = rifiuta_parametro(conn, org["comitato"], _proponi(conn, org, {"valore": 0.5}), motivazione="no")
    assert _dettagli(conn, rifiuto)["stesso_proponente"] is True
    parametro = _proponi(conn, org, {"valore": 0.8}, codice="altra_prova")
    approva_parametro(conn, org["comitato"], parametro, motivazione="ok")
    ritiro = ritira_parametro(conn, org["comitato"], parametro, motivazione="ritirata")
    assert _dettagli(conn, ritiro)["stesso_proponente"] is True


def test_approvazione_di_un_indirizzo_segna_il_proponente(conn, org):
    indirizzo = proponi_indirizzo(conn, org["comitato"], org_id=org["id"], codice="prova", testo="t",
                                  ambito="a", motivazione="m")
    atto = approva_indirizzo(conn, org["comitato"], indirizzo, motivazione="ok")
    assert _dettagli(conn, atto)["stesso_proponente"] is True
