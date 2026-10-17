"""Avanzamento della sperimentazione e ruoli dell'utente per l'interfaccia (fase 6)."""

import pytest

from neartech.calcolo import calcola_organizzazione
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, ruoli_utente
from neartech.sperimentazione import VOCI, avanzamento_sperimentazione
from test_calcolo import mondo  # noqa: F401


def _giudizio(conn, task, voce, valore, valutatore):
    conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind, rater_ref,
                                                 rubric_version) VALUES ('task', %s, %s, %s, %s, 'rif', 'rubrica-prova')""",
                 (task, voce, valore, valutatore))


def test_senza_giudizi_di_persona_l_avanzamento_e_zero(conn, mondo):  # noqa: F811
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    a = avanzamento_sperimentazione(conn, mondo["admin"], mondo["org"])
    assert a["totale"] == 1 and a["quota"] == 0 and a["occorrenze"] == {}
    assert set(a["voci"]) == set(VOCI) and all(v == {"persone": 0, "totale": 1} for v in a["voci"].values())


def test_un_giudizio_di_persona_conta_per_la_sua_voce(conn, mondo):  # noqa: F811
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    _giudizio(conn, mondo["task"], "d1", 2, "expert")
    _giudizio(conn, mondo["task"], "d3", 3, "worker")
    _giudizio(conn, mondo["task"], "k1", 1, "llm")  # il modello non conta
    a = avanzamento_sperimentazione(conn, mondo["admin"], mondo["org"])
    assert a["voci"]["d1"]["persone"] == 1 and a["voci"]["d3"]["persone"] == 1 and a["voci"]["k1"]["persone"] == 0
    assert a["occorrenze"] == {mondo["occorrenza"]: ["d1", "d3"]} and a["quota"] == pytest.approx(2 / 8)


def test_l_avanzamento_richiede_di_poter_leggere(conn, mondo):  # noqa: F811
    with pytest.raises(PermessoNegato):
        avanzamento_sperimentazione(conn, crea_utente(conn, "sso|estraneo"), mondo["org"])


def test_ruoli_dell_utente(conn, mondo):  # noqa: F811
    comitato = crea_utente(conn, "sso|comitato")
    assegna_ruolo(conn, comitato, "comitato_guida", mondo["org"], assegnata_da=mondo["admin"])
    assert ruoli_utente(conn, comitato) == [
        {"ruolo": "comitato_guida", "org_id": mondo["org"], "codice": "sintetica", "nome": "Org sintetica"}]
    assert ruoli_utente(conn, mondo["admin"])[0]["ruolo"] == "amministratore_tecnico"
    assert ruoli_utente(conn, "non-un-uuid") == []
