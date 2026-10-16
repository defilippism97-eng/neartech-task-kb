"""Utenti, ruoli e permessi. I permessi stanno in tabella, ogni verifica lascia
una riga nel log di accesso, e il log non si modifica."""

import psycopg
import pytest

from neartech.permessi import (
    AmministratoreGiaPresente,
    PermessoNegato,
    assegna_ruolo,
    chiudi_assegnazione,
    configura_log,
    crea_utente,
    inizializza_amministratore,
    puo,
    richiedi,
)


def _org(conn, nome: str) -> str:
    return str(conn.execute(
        "INSERT INTO organizations (name) VALUES (%s) RETURNING org_id", (nome,)
    ).fetchone()[0])


@pytest.fixture
def scenario(conn):
    a = _org(conn, "Org A sintetica")
    b = _org(conn, "Org B sintetica")
    admin = inizializza_amministratore(conn, "sso|admin")
    utenti = {nome: crea_utente(conn, f"sso|{nome}") for nome in
              ("auditor", "comitato", "revisore", "rappresentante", "scaduto")}
    assegna_ruolo(conn, utenti["auditor"], "auditor", assegnata_da=admin)
    assegna_ruolo(conn, utenti["comitato"], "comitato_guida", a, assegnata_da=admin)
    assegna_ruolo(conn, utenti["revisore"], "revisore", a, assegnata_da=admin)
    assegna_ruolo(conn, utenti["rappresentante"], "rappresentante_lavoratori", a, assegnata_da=admin)
    conn.execute(
        """INSERT INTO assegnazioni_ruolo (utente_id, ruolo, org_id, valida_dal, valida_al, assegnata_da)
           VALUES (%s, 'revisore', %s, now() - interval '1 day', now() - interval '1 second', %s)""",
        (utenti["scaduto"], a, admin),
    )
    return {"a": a, "b": b, "admin": admin, **utenti}


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


@pytest.mark.parametrize("utente", ["00000000-0000-0000-0000-000000000001", "non-un-uuid"])
def test_utente_sconosciuto_o_malformato_e_negato(conn, scenario, utente):
    assert not puo(conn, utente, "leggere", scenario["a"])
    assert conn.execute(
        "SELECT esito FROM log_accessi WHERE utente_id IS NULL ORDER BY accesso_id DESC LIMIT 1"
    ).fetchone()[0] == "negato"


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


def test_il_rifiuto_resta_nel_log_anche_se_la_transazione_viene_annullata(dsn):
    with psycopg.connect(dsn, autocommit=True) as log_conn:
        configura_log(log_conn)
        try:
            with psycopg.connect(dsn) as conn:
                utente = crea_utente(conn, "sso|log-durevole")
                with pytest.raises(PermessoNegato):
                    richiedi(conn, utente, "gestire_utenti", risorsa="prova-log-durevole")
                conn.rollback()
            righe = log_conn.execute(
                "SELECT esito FROM log_accessi WHERE risorsa = 'prova-log-durevole'"
            ).fetchall()
            assert righe == [("negato",)]
        finally:
            configura_log(None)


@pytest.mark.parametrize("comando", [
    "UPDATE log_accessi SET esito = 'consentito'",
    "DELETE FROM log_accessi",
    "TRUNCATE log_accessi",
    "TRUNCATE assegnazioni_ruolo",
    "UPDATE permessi_ruolo SET azione = 'gestire_utenti'",
    "DELETE FROM ruoli",
    "TRUNCATE permessi_ruolo",
])
def test_tabelle_protette_non_si_modificano(conn, scenario, comando):
    puo(conn, scenario["revisore"], "gestire_utenti")
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute(comando)


def test_ruolo_di_organizzazione_richiede_organizzazione(conn, scenario):
    utente = crea_utente(conn, "sso|senza-org")
    with pytest.raises(psycopg.errors.RaiseException):
        assegna_ruolo(conn, utente, "revisore", assegnata_da=scenario["admin"])


def test_ruolo_globale_non_ammette_organizzazione(conn, scenario):
    utente = crea_utente(conn, "sso|globale")
    with pytest.raises(psycopg.errors.RaiseException):
        assegna_ruolo(conn, utente, "auditor", scenario["a"], assegnata_da=scenario["admin"])


def test_solo_chi_gestisce_utenti_assegna_ruoli(conn, scenario):
    nuovo = crea_utente(conn, "sso|nuovo")
    with pytest.raises(PermessoNegato):
        assegna_ruolo(conn, nuovo, "revisore", scenario["a"], assegnata_da=scenario["comitato"])


def test_assegnazione_registrata_nel_registro(conn, scenario):
    nuovo = crea_utente(conn, "sso|nuovo")
    assegnazione = assegna_ruolo(conn, nuovo, "revisore", scenario["a"], assegnata_da=scenario["admin"])
    assert conn.execute(
        "SELECT atto FROM registro_decisioni WHERE tipo_oggetto = 'assegnazione_ruolo' AND oggetto_id = %s",
        (assegnazione,),
    ).fetchall() == [("approvazione",)]


def test_nessuna_assegnazione_attiva_duplicata(conn, scenario):
    with pytest.raises(psycopg.errors.UniqueViolation):
        assegna_ruolo(conn, scenario["revisore"], "revisore", scenario["a"], assegnata_da=scenario["admin"])


def test_amministratore_iniziale_solo_una_volta(conn, scenario):
    with pytest.raises(AmministratoreGiaPresente):
        inizializza_amministratore(conn, "sso|secondo-admin")


def test_assegnazione_si_chiude_una_volta_e_non_si_riscrive(conn, scenario):
    nuovo = crea_utente(conn, "sso|nuovo")
    assegnazione = assegna_ruolo(conn, nuovo, "revisore", scenario["a"], assegnata_da=scenario["admin"])
    chiudi_assegnazione(conn, assegnazione, chiusa_da=scenario["admin"], motivazione="fine incarico")
    assert not puo(conn, nuovo, "giudicare_task", scenario["a"])
    assert conn.execute(
        "SELECT chiusa_da FROM assegnazioni_ruolo WHERE assegnazione_id = %s", (assegnazione,)
    ).fetchone()[0] is not None
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("UPDATE assegnazioni_ruolo SET ruolo = 'auditor' WHERE assegnazione_id = %s", (assegnazione,))


def test_solo_chi_gestisce_utenti_chiude_assegnazioni(conn, scenario):
    assegnazione = conn.execute(
        "SELECT assegnazione_id FROM assegnazioni_ruolo WHERE utente_id = %s", (scenario["revisore"],)
    ).fetchone()[0]
    with pytest.raises(PermessoNegato):
        chiudi_assegnazione(conn, assegnazione, chiusa_da=scenario["comitato"], motivazione="x")


def test_utente_identificato_solo_da_soggetto_sso(conn):
    colonne = {r[0] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'utenti'"
    ).fetchall()}
    assert not colonne & {"nome", "cognome", "email"}
