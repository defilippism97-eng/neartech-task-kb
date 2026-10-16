"""Utenti, ruoli e permessi. I permessi stanno in tabella, ogni verifica lascia
una riga nel log di accesso, e il log non si modifica."""

from datetime import timedelta

import psycopg
import pytest

from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, puo, richiedi


def _org(conn, nome: str) -> str:
    return str(conn.execute(
        "INSERT INTO organizations (name) VALUES (%s) RETURNING org_id", (nome,)
    ).fetchone()[0])


@pytest.fixture
def scenario(conn):
    a = _org(conn, "Org A sintetica")
    b = _org(conn, "Org B sintetica")
    utenti = {nome: crea_utente(conn, f"sso|{nome}") for nome in
              ("admin", "auditor", "comitato", "revisore", "rappresentante", "scaduto")}
    assegna_ruolo(conn, utenti["admin"], "amministratore_tecnico")
    assegna_ruolo(conn, utenti["auditor"], "auditor")
    assegna_ruolo(conn, utenti["comitato"], "comitato_guida", a)
    assegna_ruolo(conn, utenti["revisore"], "revisore", a)
    assegna_ruolo(conn, utenti["rappresentante"], "rappresentante_lavoratori", a)
    adesso = conn.execute("SELECT now()").fetchone()[0]
    assegna_ruolo(conn, utenti["scaduto"], "revisore", a,
                  valida_dal=adesso - timedelta(days=1), valida_al=adesso - timedelta(seconds=1))
    return {"a": a, "b": b, **utenti}


def test_ruolo_di_organizzazione_vale_solo_nella_propria(conn, scenario):
    assert puo(conn, scenario["revisore"], "giudicare_task", scenario["a"])
    assert not puo(conn, scenario["revisore"], "giudicare_task", scenario["b"])


def test_auditor_legge_ogni_organizzazione_ma_non_giudica(conn, scenario):
    assert puo(conn, scenario["auditor"], "leggere", scenario["a"])
    assert puo(conn, scenario["auditor"], "leggere", scenario["b"])
    assert not puo(conn, scenario["auditor"], "giudicare_task", scenario["a"])


def test_amministratore_gestisce_utenti_ma_non_approva_indirizzi(conn, scenario):
    assert puo(conn, scenario["admin"], "gestire_utenti")
    assert not puo(conn, scenario["admin"], "approvare_indirizzo", scenario["a"])


def test_comitato_approva_indirizzi_ma_non_giudica_task(conn, scenario):
    assert puo(conn, scenario["comitato"], "approvare_indirizzo", scenario["a"])
    assert not puo(conn, scenario["comitato"], "giudicare_task", scenario["a"])


def test_solo_il_rappresentante_blocca_un_ribasso(conn, scenario):
    assert puo(conn, scenario["rappresentante"], "bloccare_ribasso", scenario["a"])
    assert not puo(conn, scenario["comitato"], "bloccare_ribasso", scenario["a"])


def test_revisore_approva_abbinamenti_e_fusioni(conn, scenario):
    """Decisione 2026-10-16: i compiti del curatore su abbinamenti e fusioni sono dei revisori."""
    assert puo(conn, scenario["revisore"], "approvare_abbinamenti", scenario["a"])
    assert puo(conn, scenario["revisore"], "approvare_fusioni", scenario["a"])


def test_assegnazione_scaduta_non_da_permessi(conn, scenario):
    assert not puo(conn, scenario["scaduto"], "giudicare_task", scenario["a"])


def test_azione_sconosciuta_e_negata(conn, scenario):
    assert not puo(conn, scenario["admin"], "azione_inesistente")


def test_richiedi_solleva_permesso_negato(conn, scenario):
    with pytest.raises(PermessoNegato):
        richiedi(conn, scenario["revisore"], "gestire_utenti")


def test_ogni_verifica_scrive_il_log(conn, scenario):
    puo(conn, scenario["revisore"], "giudicare_task", scenario["a"])
    puo(conn, scenario["revisore"], "giudicare_task", scenario["b"])
    righe = conn.execute(
        "SELECT azione, esito FROM log_accessi WHERE utente_id = %s ORDER BY accesso_id",
        (scenario["revisore"],),
    ).fetchall()
    assert righe == [("giudicare_task", "consentito"), ("giudicare_task", "negato")]


@pytest.mark.parametrize("comando", ["UPDATE log_accessi SET esito = 'consentito'", "DELETE FROM log_accessi"])
def test_log_accessi_non_si_modifica(conn, scenario, comando):
    puo(conn, scenario["revisore"], "gestire_utenti")
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute(comando)


def test_ruolo_di_organizzazione_richiede_organizzazione(conn):
    utente = crea_utente(conn, "sso|senza-org")
    with pytest.raises(psycopg.errors.RaiseException):
        assegna_ruolo(conn, utente, "revisore")


def test_ruolo_globale_non_ammette_organizzazione(conn):
    org = _org(conn, "Org sintetica")
    utente = crea_utente(conn, "sso|globale")
    with pytest.raises(psycopg.errors.RaiseException):
        assegna_ruolo(conn, utente, "auditor", org)


def test_assegnazione_si_chiude_ma_non_si_riscrive(conn):
    org = _org(conn, "Org sintetica")
    utente = crea_utente(conn, "sso|revisore")
    assegnazione = assegna_ruolo(conn, utente, "revisore", org)
    conn.execute("UPDATE assegnazioni_ruolo SET valida_al = now() WHERE assegnazione_id = %s", (assegnazione,))
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("UPDATE assegnazioni_ruolo SET ruolo = 'auditor' WHERE assegnazione_id = %s", (assegnazione,))


def test_utente_identificato_solo_da_soggetto_sso(conn):
    colonne = {r[0] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'utenti'"
    ).fetchall()}
    assert not colonne & {"nome", "cognome", "email"}
