"""Ruoli di database: l'applicazione non è proprietaria delle tabelle, quindi non può
disattivare i trigger append-only né svuotare le tabelle; la lettura non scrive."""

import psycopg
import pytest

from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import inizializza_amministratore


def _come(conn, ruolo):
    conn.execute(f"SET LOCAL ROLE {ruolo}")


@pytest.mark.parametrize("comando", [
    "ALTER TABLE registro_decisioni DISABLE TRIGGER registro_append_only",
    "TRUNCATE log_accessi",
    "INSERT INTO permessi_ruolo (ruolo, azione) VALUES ('revisore', 'gestire_utenti')",
    "DELETE FROM migrazioni_applicate",
    "CREATE TABLE public.tabella_abusiva (x int)",
])
def test_l_applicazione_non_aggira_le_protezioni(conn, comando):
    _come(conn, "neartech_app")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute(comando)


def test_l_applicazione_legge_e_scrive_dove_serve(conn):
    _come(conn, "neartech_app")
    conn.execute("SELECT count(*) FROM canonical_tasks").fetchone()
    utente = conn.execute("INSERT INTO utenti (soggetto_sso) VALUES ('sso|ruolo-app') RETURNING utente_id").fetchone()[0]
    conn.execute(
        """INSERT INTO log_accessi (utente_id, azione, esito) VALUES (%s, 'leggere', 'consentito')""", (utente,)
    )


def test_la_lettura_non_scrive(conn):
    _come(conn, "neartech_lettura")
    conn.execute("SELECT count(*) FROM registro_decisioni").fetchone()
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute("INSERT INTO utenti (soggetto_sso) VALUES ('sso|lettura')")


def test_lo_spazio_dell_organizzazione_e_accessibile_all_applicazione(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")  # come proprietario
    _come(conn, "neartech_app")
    assert conn.execute("SELECT count(*) FROM org_sintetica.occorrenze").fetchone()[0] == 0
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute("DROP TABLE org_sintetica.occorrenze")
