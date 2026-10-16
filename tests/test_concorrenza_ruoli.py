"""Validità dei ruoli fra transazioni concorrenti (santa-loop, giro 3).

Ogni test conferma davvero su un database isolato: una transazione iniziata prima di una
revoca o di una chiusura deve vederne l'effetto appena è confermata, non all'ora di inizio.
"""

import psycopg
import pytest

from neartech.permessi import (
    AmministratoreGiaPresente,
    UltimoAmministratore,
    assegna_ruolo,
    chiudi_assegnazione,
    crea_utente,
    inizializza_amministratore,
    puo,
)


def _assegnazione(conn, utente, ruolo):
    return conn.execute(
        "SELECT assegnazione_id FROM assegnazioni_ruolo WHERE utente_id = %s AND ruolo = %s",
        (utente, ruolo),
    ).fetchone()[0]


def test_bootstrap_non_si_ripete_in_una_transazione_iniziata_prima(dsn_isolato):
    with psycopg.connect(dsn_isolato) as prima, psycopg.connect(dsn_isolato) as seconda:
        seconda.execute("SELECT 1")  # la transazione della seconda connessione è già aperta
        inizializza_amministratore(prima, "sso|primo")
        prima.commit()
        with pytest.raises(AmministratoreGiaPresente):
            inizializza_amministratore(seconda, "sso|secondo")


def test_chiusure_concorrenti_non_lasciano_senza_amministratore(dsn_isolato):
    with psycopg.connect(dsn_isolato) as setup:
        a = inizializza_amministratore(setup, "sso|admin-a")
        b = crea_utente(setup, "sso|admin-b")
        assegna_ruolo(setup, b, "amministratore_tecnico", assegnata_da=a)
        setup.commit()
        ass_a = _assegnazione(setup, a, "amministratore_tecnico")
        ass_b = _assegnazione(setup, b, "amministratore_tecnico")
        setup.commit()
    with psycopg.connect(dsn_isolato) as prima, psycopg.connect(dsn_isolato) as seconda:
        seconda.execute("SELECT 1")
        chiudi_assegnazione(prima, ass_a, chiusa_da=b, motivazione="chiusura A")
        prima.commit()
        with pytest.raises(UltimoAmministratore):
            chiudi_assegnazione(seconda, ass_b, chiusa_da=b, motivazione="chiusura B")


def test_ruolo_revocato_non_autorizza_una_transazione_iniziata_prima(dsn_isolato):
    with psycopg.connect(dsn_isolato) as setup:
        admin = inizializza_amministratore(setup, "sso|admin")
        org = setup.execute("INSERT INTO organizations (name) VALUES ('Org') RETURNING org_id").fetchone()[0]
        membro = crea_utente(setup, "sso|membro")
        assegnazione = assegna_ruolo(setup, membro, "comitato_guida", str(org), assegnata_da=admin)
        setup.commit()
    with psycopg.connect(dsn_isolato) as revoca, psycopg.connect(dsn_isolato) as membro_conn:
        membro_conn.execute("SELECT 1")
        chiudi_assegnazione(revoca, assegnazione, chiusa_da=admin, motivazione="revoca")
        revoca.commit()
        assert not puo(membro_conn, membro, "approvare_parametro", str(org))


def test_soggetto_sso_non_si_cambia(conn):
    utente = crea_utente(conn, "sso|originale")
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("UPDATE utenti SET soggetto_sso = 'sso|altro' WHERE utente_id = %s", (utente,))
