"""Importazione dei giudizi del modello già prodotti (etichette silver v2) come valutazioni registrate.

Ogni giudizio è un record a sé, con modello, versione della rubrica, prompt e campagna. Il titolo del dataset
trova il task; un task fuso passa i suoi giudizi al superstite (registro di metodo, sezione 8); un task
ritirato resta fuori. Un rilancio non duplica.
"""

import pytest

from neartech.permessi import PermessoNegato, crea_utente, inizializza_amministratore
from neartech.valutazioni import importa_giudizi_modello


@pytest.fixture
def mondo(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    ids = {}
    for titolo in ("Comporre i turni", "Redigere i turni", "Area ritirata"):
        ids[titolo] = str(conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2) "
                                       "RETURNING task_id", (titolo,)).fetchone()[0])
    conn.execute("UPDATE canonical_tasks SET status = 'merged', merged_into = %s WHERE task_id = %s",
                 (ids["Comporre i turni"], ids["Redigere i turni"]))
    conn.execute("UPDATE canonical_tasks SET status = 'retired' WHERE task_id = %s", (ids["Area ritirata"],))
    return {"admin": admin, "ids": ids}


RIGHE = [
    {"titolo": "Comporre i turni", "valori": {"k1": 2, "k2": 2, "k3": 0, "r": 1}, "motivazione": "incertezza A"},
    {"titolo": "Redigere i turni", "valori": {"k1": 3, "k2": 2, "k3": 0, "r": 2}, "motivazione": None},
    {"titolo": "Area ritirata", "valori": {"k1": 1, "k2": 1, "k3": 1, "r": 1}, "motivazione": None},
    {"titolo": "Titolo sconosciuto", "valori": {"k1": 1, "k2": 1, "k3": 1, "r": 1}, "motivazione": None},
]


def _importa(conn, mondo, righe=RIGHE):
    return importa_giudizi_modello(conn, mondo["admin"], righe, campagna="silver-v2-run1", rubrica="bozza-3",
                                   modello="claude-haiku-5-5", prompt="N-v2", motivazione="etichette silver v2")


def test_giudizi_registrati_sul_task_o_sul_superstite(conn, mondo):
    esito = _importa(conn, mondo)
    assert esito == {"giudizi": 8, "task": 1, "su_superstite": 1, "ritirati": 1, "sconosciuti": 1}
    righe = conn.execute(
        """SELECT item, value, rater_kind, rater_ref, rubric_version, prompt_hash, campaign_id FROM assessment_runs
           WHERE target_kind = 'task' AND target_id = %s ORDER BY item, value""",
        (mondo["ids"]["Comporre i turni"],)).fetchall()
    assert len(righe) == 8 and {r[2:] for r in righe} == {
        ("llm", "claude-haiku-5-5", "bozza-3", "N-v2", "silver-v2-run1")}


def test_la_rubrica_bozza_resta_non_corrente_e_non_approvata(conn, mondo):
    _importa(conn, mondo)
    assert conn.execute("SELECT is_current, approved_by FROM rubric_versions WHERE version = 'bozza-3'"
                        ).fetchone() == (False, None)


def test_rilancio_non_duplica(conn, mondo):
    _importa(conn, mondo)
    assert _importa(conn, mondo)["giudizi"] == 0


def test_valori_fuori_scala_rifiutati(conn, mondo):
    with pytest.raises(ValueError, match="scala"):
        _importa(conn, mondo, [{"titolo": "Comporre i turni", "valori": {"k1": 5}, "motivazione": None}])


def test_solo_chi_gestisce_il_dataset_importa(conn, mondo):
    with pytest.raises(PermessoNegato):
        importa_giudizi_modello(conn, crea_utente(conn, "sso|x"), RIGHE, campagna="c", rubrica="bozza-3",
                                modello="m", prompt="p", motivazione="x")


def test_l_importazione_lascia_un_atto(conn, mondo):
    _importa(conn, mondo)
    assert conn.execute("SELECT count(*) FROM registro_decisioni WHERE tipo_oggetto = 'importazione_giudizi'"
                        ).fetchone()[0] == 1
