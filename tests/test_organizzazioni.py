"""Spazio dell'organizzazione (ADR 0001), stato di validazione dei task e
rimozione dei valori di policy dallo schema."""

import psycopg
import pytest

from neartech.migrazioni import CARTELLA_ORGANIZZAZIONE, da_applicare
from neartech.organizzazioni import (
    CodiceNonValido,
    aggiorna_spazi,
    crea_organizzazione,
    schema_organizzazione,
)
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore
from neartech.stato_task import TaskNonCollegato, imposta_stato, stato_corrente


@pytest.fixture
def admin(conn):
    return inizializza_amministratore(conn, "sso|admin")


def _tabelle(conn, schema: str) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (schema,)
    ).fetchall()}


# --- spazio dell'organizzazione ---------------------------------------------------

def test_crea_organizzazione_con_il_suo_spazio(conn, admin):
    org = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    schema = schema_organizzazione("sintetica")
    assert schema == "org_sintetica"
    assert {"ruoli_organizzativi", "documenti", "occorrenze"} <= _tabelle(conn, schema)
    assert conn.execute("SELECT codice FROM organizations WHERE org_id = %s", (org,)).fetchone()[0] == "sintetica"
    assert da_applicare(conn, CARTELLA_ORGANIZZAZIONE, schema) == []


def test_il_testo_del_cliente_sta_nello_spazio_dell_organizzazione(conn, admin):
    crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    colonne = {r[0] for r in conn.execute(
        """SELECT column_name FROM information_schema.columns
           WHERE table_schema = 'org_sintetica' AND table_name = 'occorrenze'"""
    ).fetchall()}
    assert {"estratto", "nota_contesto", "task_id", "ruolo_id"} <= colonne


def test_occorrenza_rimanda_al_task_condiviso(conn, admin):
    crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    task = conn.execute(
        "INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Task sintetico', 2) RETURNING task_id"
    ).fetchone()[0]
    ruolo = conn.execute(
        "INSERT INTO org_sintetica.ruoli_organizzativi (nome) VALUES ('Ruolo sintetico') RETURNING ruolo_id"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO org_sintetica.occorrenze (task_id, ruolo_id, estratto) VALUES (%s, %s, 'frammento')",
        (task, ruolo),
    )
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute(
            """INSERT INTO org_sintetica.occorrenze (task_id, ruolo_id, estratto)
               VALUES (gen_random_uuid(), %s, 'frammento')""",
            (ruolo,),
        )


@pytest.mark.parametrize("codice", ["Maiuscolo", "con-trattino", "x", "a; DROP SCHEMA public", ""])
def test_codice_non_valido_rifiutato_prima_del_database(conn, admin, codice):
    with pytest.raises(CodiceNonValido):
        crea_organizzazione(conn, admin, nome="Org", codice=codice)


def test_solo_l_amministratore_crea_organizzazioni(conn, admin):
    org = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, revisore, "revisore", org, assegnata_da=admin)
    with pytest.raises(PermessoNegato):
        crea_organizzazione(conn, revisore, nome="Altra", codice="altra")


def test_aggiorna_spazi_non_riapplica(conn, admin):
    crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    assert aggiorna_spazi(conn) == {"org_sintetica": []}


# --- stato di validazione dei task ---------------------------------------------------

@pytest.fixture
def revisione(conn, admin):
    org = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, revisore, "revisore", org, assegnata_da=admin)
    task = str(conn.execute(
        "INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Task sintetico', 2) RETURNING task_id"
    ).fetchone()[0])
    ruolo = conn.execute(
        "INSERT INTO org_sintetica.ruoli_organizzativi (nome) VALUES ('Ruolo sintetico') RETURNING ruolo_id"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO org_sintetica.occorrenze (task_id, ruolo_id, estratto) VALUES (%s, %s, 'frammento')",
        (task, ruolo),
    )
    return {"org": org, "revisore": revisore, "task": task}


def test_task_senza_storia_e_da_integrare(conn, revisione):
    assert stato_corrente(conn, revisione["task"]) == "da_integrare"


def test_cambio_di_stato_registrato_con_decisione(conn, revisione):
    imposta_stato(conn, revisione["revisore"], revisione["task"], "stima_modello",
                  org_id=revisione["org"], motivazione="etichette v2")
    imposta_stato(conn, revisione["revisore"], revisione["task"], "validato",
                  org_id=revisione["org"], motivazione="rivisto in seduta")
    assert stato_corrente(conn, revisione["task"]) == "validato"
    storia = conn.execute(
        """SELECT s.stato, r.atto FROM stati_validazione_task s
           JOIN registro_decisioni r USING (decisione_id)
           WHERE s.task_id = %s ORDER BY s.cambio_id""",
        (revisione["task"],),
    ).fetchall()
    assert storia == [("stima_modello", "approvazione"), ("validato", "approvazione")]


def test_stato_sconosciuto_rifiutato(conn, revisione):
    with pytest.raises(ValueError):
        imposta_stato(conn, revisione["revisore"], revisione["task"], "quasi_validato",
                      org_id=revisione["org"], motivazione="x")


def test_solo_chi_giudica_i_task_cambia_lo_stato(conn, revisione, admin):
    with pytest.raises(PermessoNegato):
        imposta_stato(conn, admin, revisione["task"], "validato", org_id=revisione["org"], motivazione="x")


def test_storia_degli_stati_non_si_modifica(conn, revisione):
    imposta_stato(conn, revisione["revisore"], revisione["task"], "validato",
                  org_id=revisione["org"], motivazione="x")
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("UPDATE stati_validazione_task SET stato = 'da_integrare'")


# --- nessun valore di policy nello schema ----------------------------------------------

def test_profili_di_peso_senza_default_di_policy(conn):
    default = dict(conn.execute(
        """SELECT column_name, column_default FROM information_schema.columns
           WHERE table_name = 'weight_profiles' AND column_name IN ('lambda_r', 'theta_n', 'theta_d')"""
    ).fetchall())
    assert default == {"lambda_r": None, "theta_n": None, "theta_d": None}


def test_revisore_cambia_solo_task_presenti_nella_propria_organizzazione(conn, revisione):
    estraneo = conn.execute(
        "INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Task estraneo', 2) RETURNING task_id"
    ).fetchone()[0]
    with pytest.raises(TaskNonCollegato):
        imposta_stato(conn, revisione["revisore"], str(estraneo), "validato",
                      org_id=revisione["org"], motivazione="x")


def test_stato_legato_alla_decisione_dello_stesso_task(conn, revisione):
    decisione = imposta_stato(conn, revisione["revisore"], revisione["task"], "validato",
                              org_id=revisione["org"], motivazione="x")
    altro = conn.execute(
        "INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Altro task', 2) RETURNING task_id"
    ).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute(
            "INSERT INTO stati_validazione_task (task_id, stato, decisione_id) VALUES (%s, 'validato', %s)",
            (altro, decisione),
        )
