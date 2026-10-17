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
    # Un secondo task dell'organizzazione senza copertura nello snapshot: N vuoto per lui.
    scoperto = str(conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Task scoperto', 2) "
                                "RETURNING task_id").fetchone()[0])
    registra_occorrenza(conn, org, task_id=scoperto, ruolo_id=r, documento_id=d, estratto="altro",
                        nota_contesto=None, model_name="m", prompt_hash="h")
    snapshot = str(conn.execute(
        """INSERT INTO capability_snapshots (as_of, method_version, half_life_days, status, tipo_capacita)
           VALUES ('2026-10-17', 'riserva-prova', 180, 'proposed', 'riserva') RETURNING snapshot_id""").fetchone()[0])
    for dim, valore in (("k1", 1), ("k2", 1), ("k3", 2)):
        conn.execute("""INSERT INTO task_capability (snapshot_id, task_id, dimension, c_mean, c_low, c_high, n_evidence)
                        VALUES (%s, %s, %s, %s, %s, %s, 1)""", (snapshot, task, dim, valore, valore, valore))
    from neartech.capacita import pubblica_snapshot
    pubblica_snapshot(conn, admin, snapshot, nota="copertura di prova")
    for voce, valore in (("k1", 3), ("k2", 3), ("k3", 1), ("r", 3), ("d1", 4), ("d2", 3)):
        conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind, rater_ref,
                                                     rubric_version, prompt_hash)
                        VALUES ('task', %s, %s, %s, 'llm', 'modello-prova', 'rubrica-prova', 'h')""",
                     (task, voce, valore))
    scoperta = str(conn.execute("SELECT occurrence_id FROM task_occurrences WHERE task_id = %s",
                                (scoperto,)).fetchone()[0])
    return {"admin": admin, "org": org, "task": task, "occorrenza": occorrenza, "snapshot": snapshot,
            "scoperta": scoperta}


def _stime(conn, occorrenza):
    return conn.execute(
        """SELECT n_mean, d_mean, p_q1, tipo_capacita, componenti_d, d_provvisorio, versione_calcolo, seme,
                  estrazioni, profile_id, rubric_version, snapshot_id, d_source_mix
           FROM policy_estimates WHERE occurrence_id = %s ORDER BY computed_at""", (occorrenza,)).fetchall()


def test_calcolo_scrive_i_risultati_con_le_loro_chiavi(conn, mondo):
    esito = calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=200)
    assert esito == {"occorrenze": 2, "nuove": 2, "senza_n": 1, "senza_d": 1}  # il task scoperto non ha giudizi
    (n, d, q1, capacita, componenti, provvisorio, versione, seme, estrazioni, profilo, rubrica, snapshot,
     fonti) = _stime(conn, mondo["occorrenza"])[0]
    # Copertura di riserva 1, 1, 2 vale 0, 0, 1 (sezione 22): divari 3, 3, 0 su 4, N = 0,6 × 1,375 = 0,825.
    assert float(n) == pytest.approx(0.825) and float(d) == pytest.approx(0.875) and float(q1) == 1
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
    scoperto = conn.execute("SELECT task_id FROM task_occurrences WHERE occurrence_id = %s",
                            (mondo["scoperta"],)).fetchone()[0]
    conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind, rater_ref,
                                                 rubric_version) VALUES ('task', %s, 'd1', 2, 'llm', 'm', 'rubrica-prova')""",
                 (scoperto,))
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    n, d, q1, capacita = _stime(conn, mondo["scoperta"])[0][:4]
    assert (n, q1, capacita) == (None, None, None) and float(d) == pytest.approx(0.5)


def test_servono_rubrica_profilo_e_snapshot_approvati(conn, mondo):
    conn.execute("UPDATE weight_profiles SET is_active = false")  # un profilo approvato non si disapprova
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


# --- correzioni dopo le revisioni della fase 4 ---------------------------------------

def _giudizio(conn, target, voce, valore, valutatore="llm", rif="modello-prova", tipo="task"):
    conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind, rater_ref,
                                                 rubric_version) VALUES (%s, %s, %s, %s, %s, %s, 'rubrica-prova')""",
                 (tipo, target, voce, valore, valutatore, rif))


def test_l_impronta_cambia_con_i_valori_del_profilo(conn, mondo):
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    conn.execute("UPDATE weight_profiles SET is_active = false")
    conn.execute("""INSERT INTO weight_profiles (profile_id, org_id, w_k1, w_k2, w_k3, lambda_r, w_d1, w_d2, w_d3,
                                                 w_d4, theta_n, theta_d, is_active, approved_by)
                    VALUES ('profilo-2', NULL, 0.5, 0.3, 0.2, 0.5, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5, true, 'comitato')""")
    assert calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)["nuove"] == 2


def test_profilo_approvato_non_cambia_valori(conn, mondo):
    with pytest.raises(psycopg.errors.RaiseException, match="versione nuova"):
        conn.execute("UPDATE weight_profiles SET w_k1 = 0.5, w_k2 = 0.3")


def test_giudizi_di_un_task_fuso_valgono_per_il_superstite(conn, mondo):
    fuso = str(conn.execute("INSERT INTO canonical_tasks (title_it, granularity, status, merged_into) "
                            "VALUES ('Task fuso', 2, 'merged', %s) RETURNING task_id", (mondo["task"],)).fetchone()[0])
    _giudizio(conn, fuso, "d1", 0)
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=400)
    fonti = _stime(conn, mondo["occorrenza"])[0][12]
    assert fonti["giudizi"]["d1"] == 2  # il giudizio del task fuso si aggiunge a quello del superstite


def test_una_persona_che_corregge_sostituisce_il_suo_giudizio(conn, mondo):
    _giudizio(conn, mondo["task"], "d1", 0, valutatore="expert", rif="esperto-1")
    _giudizio(conn, mondo["task"], "d1", 2, valutatore="expert", rif="esperto-1")
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    d = _stime(conn, mondo["occorrenza"])[0][1]
    assert float(d) == pytest.approx((2 + 3) / 2 / 4)  # conta solo l'ultimo giudizio dell'esperto


def test_un_giudizio_sull_occorrenza_vale_piu_di_quello_sul_task(conn, mondo):
    _giudizio(conn, mondo["occorrenza"], "d2", 1, tipo="occurrence")
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=7, estrazioni=100)
    assert float(_stime(conn, mondo["occorrenza"])[0][1]) == pytest.approx((4 + 1) / 2 / 4)


def test_seme_ed_estrazioni_validati_prima_di_tutto(conn, mondo):
    with pytest.raises(ValueError, match="seme"):
        calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=2**63, estrazioni=100)
    with pytest.raises(ValueError, match="estrazioni"):
        calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=1, estrazioni=0)


def test_il_database_rifiuta_un_risultato_senza_configurazione_approvata(conn, mondo):
    conn.execute("INSERT INTO rubric_versions (version, is_current) VALUES ('bozza', false)")
    with pytest.raises(psycopg.errors.RaiseException, match="rubrica non approvata"):
        conn.execute(
            """INSERT INTO policy_estimates (occurrence_id, task_id, role_id, profile_id, snapshot_id, rubric_version,
                 d_source_mix, versione_calcolo, seme, estrazioni, componenti_d, d_provvisorio, impronta_input,
                 calcolata_da)
               SELECT o.occurrence_id, o.task_id, o.role_id, 'profilo-prova', %s, 'bozza', '{}', 'v', 1, 1, '{}', true,
                      repeat('0', 64), %s FROM task_occurrences o WHERE o.occurrence_id = %s""",
            (mondo["snapshot"], mondo["admin"], mondo["occorrenza"]))


def test_l_applicazione_non_registra_profili_approvati(conn, mondo):
    conn.execute("SET LOCAL ROLE neartech_app")
    with pytest.raises(psycopg.errors.RaiseException, match="bozze"):
        conn.execute("""INSERT INTO weight_profiles (profile_id, org_id, w_k1, w_k2, w_k3, lambda_r, w_d1, w_d2, w_d3,
                                                     w_d4, theta_n, theta_d, is_active, approved_by)
                        VALUES ('abusivo', %s, 0.4, 0.4, 0.2, 0.5, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5, true, 'io')""",
                     (mondo["org"],))


# --- copertura di riserva con supervisione (registro di metodo, sezione 22) --------------

@pytest.mark.parametrize("livello, effettiva", [(0, 0), (1, 0), (1.5, 0.5), (2, 1), (2.5, 2), (3, 3), (3.5, 3.5),
                                                (4, 4)])
def test_copertura_effettiva_della_scala_di_riserva(livello, effettiva):
    from neartech.calcolo import copertura_effettiva_riserva
    assert copertura_effettiva_riserva(livello) == pytest.approx(effettiva)


def test_la_supervisione_riduce_la_copertura_solo_con_la_riserva():
    giudizi = {"k1": [2], "k2": [2], "k3": [0], "r": [2], "d1": [1], "d2": [1]}
    copertura = {"k1": (2, 2), "k2": (2, 2), "k3": (2, 2)}
    assert simula(giudizi, copertura, PROFILO, estrazioni=10, seme=1).n_media == 0
    riserva = simula(giudizi, copertura, PROFILO, estrazioni=10, seme=1, riserva=True)
    assert riserva.n_media == pytest.approx((0.4 * 1 / 4 + 0.4 * 1 / 4) * (1 + 0.5 * 2 / 4))
