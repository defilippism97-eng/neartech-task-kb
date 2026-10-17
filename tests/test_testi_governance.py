"""Testi di governance nello spazio dell'organizzazione (ADR 0004) e parametri comuni visti dal comitato.

Decisioni del 2026-10-16 (metodologia, sezione 10): i testi degli atti di un'organizzazione stanno nel suo
spazio, il registro condiviso ne tiene l'hash; il comitato guida vede i parametri comuni e li adotta o
chiede una ricalibrazione motivata.
"""

import psycopg
import pytest
from psycopg import sql

from neartech.governance import (
    DecisioneGiaPresa,
    adotta_parametro_comune,
    approva_indirizzo,
    approva_parametro,
    chiedi_ricalibrazione,
    indirizzi_vigenti,
    parametri_comuni,
    parametro_vigente,
    proponi_indirizzo,
    proponi_parametro,
    richieste_ricalibrazione,
    segnala,
    verifica_contenuti,
)
from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore
from neartech.registro import MARCATORE_SPAZIO, registra, verifica_testi

SPAZIO = sql.Identifier("org_sintetica")


@pytest.fixture
def org(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    org_id = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    comitato = crea_utente(conn, "sso|comitato")
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, comitato, "comitato_guida", org_id, assegnata_da=admin)
    assegna_ruolo(conn, revisore, "revisore", org_id, assegnata_da=admin)
    return {"id": org_id, "admin": admin, "comitato": comitato, "revisore": revisore}


def _comune(conn, org, valore=0.9, codice="soglia_prova"):
    parametro = proponi_parametro(conn, org["admin"], codice=codice, valore={"valore": valore},
                                  descrizione="soglia comune di prova", motivazione="valore iniziale", org_id=None)
    approva_parametro(conn, org["admin"], parametro, motivazione="approvato")
    return parametro


def _atto(conn, decisione_id):
    return conn.execute(
        "SELECT motivazione, dettagli FROM registro_decisioni WHERE decisione_id = %s", (decisione_id,)
    ).fetchone()


def _testo(conn, decisione_id):
    return conn.execute(
        sql.SQL("SELECT motivazione, dettagli FROM {}.testi_atti WHERE decisione_id = %s").format(SPAZIO),
        (decisione_id,),
    ).fetchone()


# --- testi degli atti nello spazio -------------------------------------------------

def test_motivazione_di_un_atto_dell_organizzazione_sta_nello_spazio(conn, org):
    atto = registra(conn, autore_id=org["comitato"], tipo_oggetto="prova", oggetto_id="x", atto="proposta",
                    motivazione="testo scritto dal comitato", org_id=org["id"], dettagli={"codice": "x"},
                    dettagli_riservati={"nota": "testo libero"})
    motivazione, dettagli = _atto(conn, atto)
    assert motivazione == MARCATORE_SPAZIO
    assert dettagli["codice"] == "x" and "nota" not in dettagli and len(dettagli["hash_testo"]) == 64
    assert _testo(conn, atto) == ("testo scritto dal comitato", {"nota": "testo libero"})
    assert verifica_testi(conn, org["id"]) == []


def test_atti_comuni_restano_in_public(conn, org):
    atto = registra(conn, autore_id=org["admin"], tipo_oggetto="prova", oggetto_id="x", atto="proposta",
                    motivazione="atto NEARTECH")
    assert _atto(conn, atto)[0] == "atto NEARTECH"


def test_database_rifiuta_testo_in_public_per_un_organizzazione_con_spazio(conn, org):
    with pytest.raises(psycopg.errors.RaiseException, match="spazio"):
        conn.execute(
            """INSERT INTO registro_decisioni (org_id, tipo_oggetto, oggetto_id, atto, autore_id, motivazione)
               VALUES (%s, 'prova', 'x', 'proposta', %s, 'testo in chiaro')""",
            (org["id"], org["comitato"]),
        )


def test_testo_alterato_nello_spazio_rilevato(conn, org):
    atto = registra(conn, autore_id=org["comitato"], tipo_oggetto="prova", oggetto_id="x", atto="proposta",
                    motivazione="originale", org_id=org["id"])
    conn.execute(sql.SQL("ALTER TABLE {}.testi_atti DISABLE TRIGGER testi_atti_append_only").format(SPAZIO))
    conn.execute(sql.SQL("UPDATE {}.testi_atti SET motivazione = 'alterata' WHERE decisione_id = %s")
                 .format(SPAZIO), (atto,))
    assert verifica_testi(conn, org["id"]) == [(atto, "hash diverso")]


def test_testo_mancante_nello_spazio_rilevato(conn, org):
    atto = registra(conn, autore_id=org["comitato"], tipo_oggetto="prova", oggetto_id="x", atto="proposta",
                    motivazione="originale", org_id=org["id"])
    conn.execute(sql.SQL("ALTER TABLE {}.testi_atti DISABLE TRIGGER testi_atti_append_only").format(SPAZIO))
    conn.execute(sql.SQL("DELETE FROM {}.testi_atti WHERE decisione_id = %s").format(SPAZIO), (atto,))
    assert verifica_testi(conn, org["id"]) == [(atto, "testo mancante")]


def test_testi_dello_spazio_non_si_modificano(conn, org):
    atto = registra(conn, autore_id=org["comitato"], tipo_oggetto="prova", oggetto_id="x", atto="proposta",
                    motivazione="originale", org_id=org["id"])
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute(sql.SQL("UPDATE {}.testi_atti SET motivazione = 'x' WHERE decisione_id = %s")
                     .format(SPAZIO), (atto,))


# --- indirizzi, parametri dell'organizzazione, segnalazioni --------------------------

def test_testo_degli_indirizzi_sta_nello_spazio(conn, org):
    indirizzo = proponi_indirizzo(conn, org["comitato"], org_id=org["id"], codice="relazione",
                                  testo="Tutelare la relazione diretta", ambito="Accoglienza", motivazione="m")
    approva_indirizzo(conn, org["comitato"], indirizzo, motivazione="ok")
    assert conn.execute("SELECT testo, ambito FROM indirizzi_comitato WHERE indirizzo_id = %s",
                        (indirizzo,)).fetchone() == (None, None)
    vigenti = indirizzi_vigenti(conn, org["id"])
    assert [(i.testo, i.ambito) for i in vigenti] == [("Tutelare la relazione diretta", "Accoglienza")]
    assert verifica_contenuti(conn) == []


def test_indirizzo_alterato_nello_spazio_rilevato(conn, org):
    indirizzo = proponi_indirizzo(conn, org["comitato"], org_id=org["id"], codice="relazione",
                                  testo="originale", ambito="a", motivazione="m")
    conn.execute(sql.SQL("ALTER TABLE {}.testi_indirizzi DISABLE TRIGGER testi_indirizzi_append_only")
                 .format(SPAZIO))
    conn.execute(sql.SQL("UPDATE {}.testi_indirizzi SET testo = 'alterato'").format(SPAZIO))
    assert verifica_contenuti(conn) == [("indirizzo", indirizzo)]


def test_descrizione_dei_parametri_dell_organizzazione_sta_nello_spazio(conn, org):
    parametro = proponi_parametro(conn, org["comitato"], codice="quota_prova", valore={"valore": 0.2},
                                  descrizione="quota decisa dal comitato", motivazione="m", org_id=org["id"])
    assert conn.execute("SELECT descrizione FROM parametri_governance WHERE parametro_id = %s",
                        (parametro,)).fetchone()[0] is None
    assert conn.execute(sql.SQL("SELECT descrizione FROM {}.testi_parametri WHERE parametro_id = %s")
                        .format(SPAZIO), (parametro,)).fetchone()[0] == "quota decisa dal comitato"
    assert verifica_contenuti(conn) == []


def test_descrizione_dei_parametri_comuni_resta_in_public(conn, org):
    parametro = _comune(conn, org)
    assert conn.execute("SELECT descrizione FROM parametri_governance WHERE parametro_id = %s",
                        (parametro,)).fetchone()[0] == "soglia comune di prova"


def test_dettagli_della_segnalazione_nello_spazio(conn, org):
    atto = segnala(conn, org["revisore"], org_id=org["id"], tipo_oggetto="task_canonico", oggetto_id="t1",
                   motivazione="ricaduta anomala", dettagli={"nota": "testo libero del revisore"})
    assert "nota" not in _atto(conn, atto)[1]
    assert _testo(conn, atto) == ("ricaduta anomala", {"nota": "testo libero del revisore"})


def test_uscita_del_cliente_non_lascia_testo_in_public(conn, org):
    indirizzo = proponi_indirizzo(conn, org["comitato"], org_id=org["id"], codice="relazione",
                                  testo="testo riservato", ambito="ambito riservato", motivazione="motivo riservato")
    approva_indirizzo(conn, org["comitato"], indirizzo, motivazione="approvazione riservata")
    conn.execute("DROP SCHEMA org_sintetica CASCADE")
    testi = conn.execute(
        """SELECT count(*) FROM registro_decisioni
           WHERE org_id = %s AND (motivazione LIKE '%%riservat%%' OR dettagli::text LIKE '%%riservat%%')""",
        (org["id"],),
    ).fetchone()[0]
    assert testi == 0


# --- parametri comuni e comitato guida (decisione b) ---------------------------------

def test_comitato_vede_i_parametri_comuni_da_esaminare(conn, org):
    parametro = _comune(conn, org)
    stato = parametri_comuni(conn, org["comitato"], org["id"])
    assert [(s.parametro_id, s.descrizione, s.valore, s.stato) for s in stato] == [
        (parametro, "soglia comune di prova", {"valore": 0.9}, "da_esaminare")
    ]


def test_comitato_adotta_il_parametro_comune(conn, org):
    parametro = _comune(conn, org)
    atto = adotta_parametro_comune(conn, org["comitato"], org_id=org["id"], parametro_id=parametro,
                                   motivazione="coerente con l'organizzazione")
    assert parametro_vigente(conn, "soglia_prova", org["id"]).adozione_id == atto
    assert [s.stato for s in parametri_comuni(conn, org["comitato"], org["id"])] == ["adottato"]


def test_versione_comune_nuova_va_adottata_di_nuovo(conn, org):
    adotta_parametro_comune(conn, org["comitato"], org_id=org["id"], parametro_id=_comune(conn, org),
                            motivazione="ok")
    _comune(conn, org, valore=0.85)
    vigente = parametro_vigente(conn, "soglia_prova", org["id"])
    assert (vigente.versione, vigente.adozione_id) == (2, None)


def test_parametro_dell_organizzazione_non_ha_adozione(conn, org):
    parametro = proponi_parametro(conn, org["comitato"], codice="soglia_prova", valore={"valore": 0.95},
                                  descrizione="d", motivazione="m", org_id=org["id"])
    approva_parametro(conn, org["comitato"], parametro, motivazione="ok")
    assert parametro_vigente(conn, "soglia_prova", org["id"]).adozione_id is None


def test_si_adotta_solo_la_versione_comune_vigente(conn, org):
    prima = _comune(conn, org)
    _comune(conn, org, valore=0.85)
    with pytest.raises(ValueError, match="vigente"):
        adotta_parametro_comune(conn, org["comitato"], org_id=org["id"], parametro_id=prima, motivazione="ok")


def test_parametro_dell_organizzazione_non_si_adotta(conn, org):
    parametro = proponi_parametro(conn, org["comitato"], codice="soglia_prova", valore={"valore": 0.95},
                                  descrizione="d", motivazione="m", org_id=org["id"])
    with pytest.raises(ValueError, match="comune"):
        adotta_parametro_comune(conn, org["comitato"], org_id=org["id"], parametro_id=parametro, motivazione="ok")


def test_adozione_una_volta_per_versione(conn, org):
    parametro = _comune(conn, org)
    adotta_parametro_comune(conn, org["comitato"], org_id=org["id"], parametro_id=parametro, motivazione="ok")
    with pytest.raises(DecisioneGiaPresa):
        adotta_parametro_comune(conn, org["comitato"], org_id=org["id"], parametro_id=parametro, motivazione="ok")


def test_revisore_non_adotta(conn, org):
    parametro = _comune(conn, org)
    with pytest.raises(PermessoNegato):
        adotta_parametro_comune(conn, org["revisore"], org_id=org["id"], parametro_id=parametro, motivazione="ok")


def test_richiesta_di_ricalibrazione_motivata_arriva_all_amministratore(conn, org):
    parametro = _comune(conn, org)
    atto = chiedi_ricalibrazione(conn, org["comitato"], org_id=org["id"], parametro_id=parametro,
                                 motivazione="la soglia è troppo alta per un'organizzazione piccola")
    assert _atto(conn, atto)[0] == MARCATORE_SPAZIO
    assert [s.stato for s in parametri_comuni(conn, org["comitato"], org["id"])] == ["ricalibrazione_richiesta"]
    richieste = richieste_ricalibrazione(conn, org["admin"])
    assert [(r["org_id"], r["parametro_id"], r["motivazione"]) for r in richieste] == [
        (org["id"], parametro, "la soglia è troppo alta per un'organizzazione piccola")
    ]


def test_ricalibrazione_senza_motivazione_rifiutata(conn, org):
    parametro = _comune(conn, org)
    with pytest.raises(ValueError, match="motivazione"):
        chiedi_ricalibrazione(conn, org["comitato"], org_id=org["id"], parametro_id=parametro, motivazione="  ")


def test_solo_l_amministratore_vede_tutte_le_richieste(conn, org):
    with pytest.raises(PermessoNegato):
        richieste_ricalibrazione(conn, org["comitato"])


def test_database_rifiuta_adozione_di_un_parametro_dell_organizzazione(conn, org):
    parametro = proponi_parametro(conn, org["comitato"], codice="soglia_prova", valore={"valore": 0.95},
                                  descrizione="d", motivazione="m", org_id=org["id"])
    with pytest.raises(psycopg.errors.RaiseException, match="comune"):
        registra(conn, autore_id=org["comitato"], tipo_oggetto="parametro", oggetto_id=parametro,
                 atto="adozione", motivazione="m", org_id=org["id"])


# --- rafforzamenti dopo le revisioni (2026-10-17) ------------------------------------

def test_impronta_con_la_chiave_dello_spazio(conn, org):
    """Chi legge solo public non conferma un testo indovinato: l'impronta non è lo sha256 del testo."""
    import hashlib
    import json
    atto = registra(conn, autore_id=org["comitato"], tipo_oggetto="prova", oggetto_id="x", atto="proposta",
                    motivazione="approvato", org_id=org["id"])
    semplice = hashlib.sha256(json.dumps({"dettagli": {}, "motivazione": "approvato"}, sort_keys=True,
                                         ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    assert _atto(conn, atto)[1]["hash_testo"] != semplice


def test_impronta_stabile_con_numeri_che_jsonb_normalizza(conn, org):
    registra(conn, autore_id=org["comitato"], tipo_oggetto="prova", oggetto_id="x", atto="proposta",
             motivazione="m", org_id=org["id"], dettagli_riservati={"grande": 1e20, "zero": -0.0})
    assert verifica_testi(conn, org["id"]) == []


def _inserisci_atto(conn, org, dettagli):
    from psycopg.types.json import Jsonb
    conn.execute(
        """INSERT INTO registro_decisioni (org_id, tipo_oggetto, oggetto_id, atto, autore_id, motivazione, dettagli)
           VALUES (%s, 'prova', 'x', 'proposta', %s, %s, %s)""",
        (org["id"], org["comitato"], MARCATORE_SPAZIO, Jsonb(dettagli)),
    )


def test_database_rifiuta_testo_libero_nei_dettagli(conn, org):
    with pytest.raises(psycopg.errors.RaiseException, match="solo codici"):
        _inserisci_atto(conn, org, {"hash_testo": "a" * 64, "nota": "testo libero del cliente"})


def test_database_rifiuta_impronta_non_valida(conn, org):
    with pytest.raises(psycopg.errors.RaiseException, match="spazio"):
        _inserisci_atto(conn, org, {"hash_testo": "testo del cliente"})


def test_atto_senza_testo_nello_spazio_rifiutato_alla_fine_della_transazione(conn, org):
    _inserisci_atto(conn, org, {"hash_testo": "a" * 64})
    with pytest.raises(psycopg.errors.RaiseException, match="senza testo"):
        conn.execute("SET CONSTRAINTS registro_testo_presente IMMEDIATE")


def test_organizzazione_senza_spazio_non_registra_atti(conn, org):
    altra = str(conn.execute("INSERT INTO organizations (name) VALUES ('Senza spazio') RETURNING org_id").fetchone()[0])
    with pytest.raises(LookupError, match="spazio"):
        registra(conn, autore_id=org["admin"], tipo_oggetto="prova", oggetto_id="x", atto="proposta",
                 motivazione="m", org_id=altra)
    with pytest.raises(psycopg.errors.RaiseException, match="spazio"):
        conn.execute(
            """INSERT INTO registro_decisioni (org_id, tipo_oggetto, oggetto_id, atto, autore_id, motivazione)
               VALUES (%s, 'prova', 'x', 'proposta', %s, 'testo in chiaro')""",
            (altra, org["admin"]),
        )


def test_testo_di_un_altra_organizzazione_rifiutato_nello_spazio(conn, org):
    crea_organizzazione(conn, org["admin"], nome="Altra", codice="altra")
    atto = registra(conn, autore_id=org["comitato"], tipo_oggetto="prova", oggetto_id="x", atto="proposta",
                    motivazione="m", org_id=org["id"])
    with pytest.raises(psycopg.errors.RaiseException, match="altra organizzazione"):
        conn.execute("INSERT INTO org_altra.testi_atti (decisione_id, motivazione) VALUES (%s, 'copiato')", (atto,))


def test_database_rifiuta_adozione_di_una_versione_comune_superata(conn, org):
    prima = _comune(conn, org)
    _comune(conn, org, valore=0.85)
    with pytest.raises(psycopg.errors.RaiseException, match="vigente"):
        registra(conn, autore_id=org["comitato"], tipo_oggetto="parametro", oggetto_id=prima,
                 atto="adozione", motivazione="m", org_id=org["id"])


def test_verifica_dei_contenuti_per_una_sola_organizzazione(conn, org):
    crea_organizzazione(conn, org["admin"], nome="Altra", codice="altra")
    conn.execute("DROP SCHEMA org_altra CASCADE")  # spazio mancante: non blocca le altre organizzazioni
    assert verifica_contenuti(conn, org["id"]) == []
    assert verifica_contenuti(conn) == []


# --- lettura delle richieste di ricalibrazione (revisione del 2026-10-17) -----------------------

def test_lettura_delle_richieste_lascia_una_voce_per_organizzazione(conn, org):
    altra = crea_organizzazione(conn, org["admin"], nome="Altra org sintetica", codice="sintetica_altra")
    richieste_ricalibrazione(conn, org["admin"])
    lette = {r[0] for r in conn.execute(
        """SELECT org_id::text FROM log_accessi
           WHERE utente_id = %s AND azione = 'approvare_parametro_comune'
             AND risorsa = 'richieste_ricalibrazione' AND esito = 'consentito' AND org_id IS NOT NULL""",
        (org["admin"],)).fetchall()}
    assert {org["id"], altra} <= lette


def test_richiesta_superata_quando_il_parametro_non_e_piu_vigente(conn, org):
    prima = _comune(conn, org, valore=0.9)
    chiedi_ricalibrazione(conn, org["comitato"], org_id=org["id"], parametro_id=prima,
                          motivazione="soglia troppo alta")
    assert [r["superata"] for r in richieste_ricalibrazione(conn, org["admin"])] == [False]
    seconda = _comune(conn, org, valore=0.85)  # nuova versione comune: la richiesta ha avuto risposta
    chiedi_ricalibrazione(conn, org["comitato"], org_id=org["id"], parametro_id=seconda,
                          motivazione="ancora troppo alta")
    assert [(r["parametro_id"], r["superata"]) for r in richieste_ricalibrazione(conn, org["admin"])] == [
        (prima, True), (seconda, False)]
