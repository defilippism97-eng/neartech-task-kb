"""Calcolo deterministico di N e D (fase 4; registro di metodo, sezione 17).

Le formule si verificano sull'esempio svolto del piano; la simulazione è ripetibile con lo stesso seme;
i risultati portano le loro chiavi e non si modificano.
"""

import psycopg
import pytest

from neartech.calcolo import (
    VERSIONE_CALCOLO,
    Profilo,
    calcola_organizzazione,
    d_puntuale,
    n_puntuale,
    quadrante,
    simula,
)
from neartech.occorrenze import documento, registra_occorrenza, ruolo
from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore

PROFILO = Profilo("esempio", w_k={"k1": 0.4, "k2": 0.4, "k3": 0.2}, lambda_r=0.5,
                  w_d={"d1": 0.25, "d2": 0.25, "d3": 0.25, "d4": 0.25}, theta_n=0.5, theta_d=0.5)


# --- formule (esempio svolto del piano) ---------------------------------------------

def test_n_dell_esempio_svolto():
    assert n_puntuale({"k1": 3, "k2": 3, "k3": 1}, {"k1": 1, "k2": 1, "k3": 2}, 3, PROFILO) == pytest.approx(0.55)
    assert n_puntuale({"k1": 2, "k2": 2, "k3": 0}, {"k1": 3, "k2": 2, "k3": 4}, 2, PROFILO) == 0


def test_n_limitato_a_uno():
    assert n_puntuale({"k1": 4, "k2": 4, "k3": 4}, {"k1": 0, "k2": 0, "k3": 0}, 4, PROFILO) == 1


def test_d_dell_esempio_svolto():
    assert d_puntuale({"d1": 4, "d2": 3, "d3": 4, "d4": 4}, PROFILO) == (pytest.approx(0.9375), ("d1", "d2", "d3", "d4"))
    assert d_puntuale({"d1": 1, "d2": 2, "d3": 1, "d4": 0}, PROFILO)[0] == pytest.approx(0.25)


def test_d_provvisorio_su_d1_e_d2_con_i_pesi_a_somma_uno():
    valore, componenti = d_puntuale({"d1": 4, "d2": 3}, PROFILO)
    assert valore == pytest.approx(0.875) and componenti == ("d1", "d2")


def test_d_senza_componenti():
    assert d_puntuale({}, PROFILO) == (None, ())


def test_quadranti():
    assert quadrante(0.55, 0.94, 0.5, 0.5) == "q1"
    assert quadrante(0.6, 0.2, 0.5, 0.5) == "q2"
    assert quadrante(0.1, 0.8, 0.5, 0.5) == "q3"
    assert quadrante(0.0, 0.25, 0.5, 0.5) == "q4"
    assert quadrante(0.5, 0.5, 0.5, 0.5) == "q1"  # sulla soglia: alto


# --- simulazione -----------------------------------------------------------------------

GIUDIZI_B = {"k1": [3], "k2": [3], "k3": [1], "r": [3], "d1": [4], "d2": [3]}
COPERTURA_B = {"k1": (1, 1), "k2": (1, 1), "k3": (2, 2)}


def test_simulazione_senza_incertezza_coincide_con_le_formule():
    r = simula(GIUDIZI_B, COPERTURA_B, PROFILO, estrazioni=200, seme=1)
    assert r.n_media == pytest.approx(0.55) and r.n_dev == pytest.approx(0)
    assert r.d_media == pytest.approx(0.875) and r.provvisorio and r.componenti_d == ("d1", "d2")
    assert r.p_quadranti == {"q1": 1.0, "q2": 0.0, "q3": 0.0, "q4": 0.0}


def test_simulazione_ripetibile_con_lo_stesso_seme():
    giudizi = {"k1": [1, 2, 3], "k2": [2, 3], "k3": [0, 1], "r": [1, 2], "d1": [1, 3], "d2": [0, 2]}
    copertura = {"k1": (0.5, 2.5), "k2": (1, 3), "k3": (0, 1)}
    a = simula(giudizi, copertura, PROFILO, estrazioni=500, seme=42)
    assert a == simula(giudizi, copertura, PROFILO, estrazioni=500, seme=42)
    assert a != simula(giudizi, copertura, PROFILO, estrazioni=500, seme=43)
    assert sum(a.p_quadranti.values()) == pytest.approx(1.0)


def test_senza_copertura_n_e_quadranti_vuoti():
    r = simula(GIUDIZI_B, None, PROFILO, estrazioni=100, seme=1)
    assert r.n_media is None and r.p_quadranti is None and r.d_media == pytest.approx(0.875)


# --- calcolo per un'organizzazione ------------------------------------------------

@pytest.fixture
def mondo(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    org = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    task = str(conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Colloquio con la famiglia', 2) "
                            "RETURNING task_id").fetchone()[0])
    r = ruolo(conn, org, "Coordinatore")
    d = documento(conn, org, nome_file="m.docx", sha256="a" * 64, licenza="interno")
    registra_occorrenza(conn, org, task_id=task, ruolo_id=r, documento_id=d, estratto="conduce il colloquio",
                        nota_contesto=None, model_name="m", prompt_hash="h")
    occorrenza = str(conn.execute("SELECT occurrence_id FROM task_occurrences WHERE task_id = %s", (task,)).fetchone()[0])
    conn.execute("INSERT INTO rubric_versions (version, is_current, approved_by, approved_at) "
                 "VALUES ('rubrica-prova', true, 'comitato di prova', now())")
    conn.execute("""INSERT INTO weight_profiles (profile_id, org_id, w_k1, w_k2, w_k3, lambda_r, w_d1, w_d2, w_d3, w_d4,
                                                 theta_n, theta_d, is_active, approved_by, approved_at)
                    VALUES ('profilo-prova', NULL, 0.4, 0.4, 0.2, 0.5, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5, true,
                            'comitato di prova', now())""")
    snapshot = str(conn.execute(
        """INSERT INTO capability_snapshots (as_of, method_version, half_life_days, status, tipo_capacita,
                                             approved_by, approved_at)
           VALUES ('2026-10-17', 'riserva-prova', 180, 'published', 'riserva', 'curatore di prova', now())
           RETURNING snapshot_id""").fetchone()[0])
    for dim, valore in (("k1", 1), ("k2", 1), ("k3", 2)):
        conn.execute("""INSERT INTO task_capability (snapshot_id, task_id, dimension, c_mean, c_low, c_high, n_evidence)
                        VALUES (%s, %s, %s, %s, %s, %s, 1)""", (snapshot, task, dim, valore, valore, valore))
    for voce, valore in (("k1", 3), ("k2", 3), ("k3", 1), ("r", 3), ("d1", 4), ("d2", 3)):
        conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind, rater_ref,
                                                     rubric_version, prompt_hash)
                        VALUES ('task', %s, %s, %s, 'llm', 'modello-prova', 'rubrica-prova', 'h')""",
                     (task, voce, valore))
    return {"admin": admin, "org": org, "task": task, "occorrenza": occorrenza, "snapshot": snapshot}


def _stime(conn, occorrenza):
    return conn.execute(
        """SELECT n_mean, d_mean, p_q1, tipo_capacita, componenti_d, d_provvisorio, versione_calcolo, seme,
                  estrazioni, profile_id, rubric_version, snapshot_id, d_source_mix
           FROM policy_estimates WHERE occurrence_id = %s ORDER BY computed_at""", (occorrenza,)).fetchall()


def test_calcolo_scrive_i_risultati_con_le_loro_chiavi(conn, mondo):
    esito = calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=200)
    assert esito == {"occorrenze": 1, "nuove": 1, "senza_n": 0, "senza_d": 0}
    (n, d, q1, capacita, componenti, provvisorio, versione, seme, estrazioni, profilo, rubrica, snapshot,
     fonti) = _stime(conn, mondo["occorrenza"])[0]
    assert float(n) == pytest.approx(0.55) and float(d) == pytest.approx(0.875) and float(q1) == 1
    assert (capacita, componenti, provvisorio, versione, seme, estrazioni, profilo, rubrica) == (
        "riserva", ["d1", "d2"], True, VERSIONE_CALCOLO, 7, 200, "profilo-prova", "rubrica-prova")
    assert str(snapshot) == mondo["snapshot"]
    assert fonti["fonti"] == {"llm": 1.0} and fonti["mancanti"] == ["d3", "d4"]


def test_stesso_input_nessuna_riga_nuova(conn, mondo):
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=200)
    assert calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=200)["nuove"] == 0
    assert len(_stime(conn, mondo["occorrenza"])) == 1


def test_un_giudizio_di_persona_prevale_e_produce_una_riga_nuova(conn, mondo):
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=200)
    conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind, rater_ref, rubric_version)
                    VALUES ('task', %s, 'd1', 0, 'expert', 'esperto-1', 'rubrica-prova')""", (mondo["task"],))
    assert calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=200)["nuove"] == 1
    # Stessa transazione nel test: computed_at coincide, quindi si confrontano le due righe per contenuto.
    righe = {float(r[1]): r[12]["fonti"] for r in _stime(conn, mondo["occorrenza"])}
    assert righe == {0.875: {"llm": 1.0}, 0.375: {"expert": 0.5, "llm": 0.5}}  # (0 + 3) / 2 / 4


def test_senza_copertura_n_vuoto(conn, mondo):
    conn.execute("DELETE FROM task_capability")
    esito = calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    assert esito["senza_n"] == 1
    n, d, q1, capacita = _stime(conn, mondo["occorrenza"])[0][:4]
    assert (n, q1, capacita) == (None, None, None) and d is not None


def test_servono_rubrica_profilo_e_snapshot_approvati(conn, mondo):
    conn.execute("UPDATE weight_profiles SET approved_by = NULL")
    with pytest.raises(LookupError, match="profilo"):
        calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)


def test_solo_l_amministratore_tecnico_calcola(conn, mondo):
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, revisore, "revisore", mondo["org"], assegnata_da=mondo["admin"])
    with pytest.raises(PermessoNegato):
        calcola_organizzazione(conn, revisore, mondo["org"], seme=7, estrazioni=100)


def test_risultati_non_si_modificano(conn, mondo):
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("UPDATE policy_estimates SET n_mean = 0")
