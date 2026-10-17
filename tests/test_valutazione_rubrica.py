"""Valutazione dei task sulla rubrica da parte dei revisori (fase 6, fetta 4)."""

import pytest

from neartech.calcolo import calcola_organizzazione
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente
from neartech.sperimentazione import avanzamento_sperimentazione
from neartech.valutazione_rubrica import coda_valutazione, registra_giudizio_rubrica, rubrica_corrente
from test_calcolo import mondo  # noqa: F401


@pytest.fixture
def revisore(conn, mondo):  # noqa: F811
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    utente = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, utente, "revisore", mondo["org"], assegnata_da=mondo["admin"])
    return utente


def test_la_coda_parte_dal_task_meno_certo_con_le_stime_del_modello(conn, mondo, revisore):  # noqa: F811
    coda = coda_valutazione(conn, revisore, mondo["org"])
    assert [c["task"] for c in coda] == ["Colloquio con la famiglia"]
    assert coda[0]["stime_modello"]["k1"] == 3 and coda[0]["miei_giudizi"] == {} and coda[0]["ruoli"] == "Coordinatore"


def test_un_giudizio_del_revisore_conta_come_giudizio_di_persona(conn, mondo, revisore):  # noqa: F811
    atto = registra_giudizio_rubrica(conn, revisore, mondo["org"], mondo["task"], "d1", 2, nota="colloquio di routine")
    assert conn.execute("SELECT tipo_oggetto, atto FROM registro_decisioni WHERE decisione_id = %s",
                        (atto,)).fetchone() == ("giudizio_rubrica", "proposta")
    coda = coda_valutazione(conn, revisore, mondo["org"])
    assert coda[0]["miei_giudizi"] == {"d1": 2} and coda[0]["voci_con_giudizi_di_persona"] == ["d1"]
    assert avanzamento_sperimentazione(conn, revisore, mondo["org"])["voci"]["d1"]["persone"] == 1


def test_voce_e_livello_validi(conn, mondo, revisore):  # noqa: F811
    with pytest.raises(ValueError, match="voce"):
        registra_giudizio_rubrica(conn, revisore, mondo["org"], mondo["task"], "d3", 2)
    with pytest.raises(ValueError, match="0 a 4"):
        registra_giudizio_rubrica(conn, revisore, mondo["org"], mondo["task"], "k1", 5)


def test_solo_task_dell_organizzazione(conn, mondo, revisore):  # noqa: F811
    estraneo = str(conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Altro', 2) "
                                "RETURNING task_id").fetchone()[0])
    with pytest.raises(LookupError):
        registra_giudizio_rubrica(conn, revisore, mondo["org"], estraneo, "k1", 1)


def test_solo_il_revisore_giudica(conn, mondo, revisore):  # noqa: F811
    comitato = crea_utente(conn, "sso|comitato")
    assegna_ruolo(conn, comitato, "comitato_guida", mondo["org"], assegnata_da=mondo["admin"])
    with pytest.raises(PermessoNegato):
        registra_giudizio_rubrica(conn, comitato, mondo["org"], mondo["task"], "k1", 1)
    with pytest.raises(PermessoNegato):
        coda_valutazione(conn, comitato, mondo["org"])


def test_la_rubrica_ha_i_testi_dei_livelli(conn, mondo):  # noqa: F811
    conn.execute("UPDATE rubric_versions SET is_current = false")
    conn.execute("INSERT INTO rubric_versions (version, is_current, approved_by, approved_at) "
                 "VALUES ('bozza-3', true, 'prova', now()) ON CONFLICT (version) DO UPDATE SET is_current = true")
    r = rubrica_corrente(conn)
    assert r["versione"] == "bozza-3" and [v["codice"] for v in r["voci"]] == ["k1", "k2", "k3", "r", "d1", "d2"]
    assert all(len(v["livelli"]) == 5 for v in r["voci"])
