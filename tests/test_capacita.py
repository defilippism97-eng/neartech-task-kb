"""Snapshot di capacità di riserva (fase 4; registro di metodo, sezione 17).

La copertura di ogni task e dimensione si calcola dalle evidenze sul task con la formula del piano
(qualità, decadimento nel tempo); l'intervallo è dato dal disaccordo fra le evidenze. Lo snapshot nasce
proposto e diventa pubblicato con un atto; ne resta pubblicato uno solo.
"""

import pytest

from neartech.capacita import METODO_RISERVA, proponi_snapshot_riserva, pubblica_snapshot
from neartech.permessi import PermessoNegato, crea_utente, inizializza_amministratore


@pytest.fixture
def mondo(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    task = str(conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Comporre i turni', 2) "
                            "RETURNING task_id").fetchone()[0])
    fonte = str(conn.execute(
        """INSERT INTO sources (kind, name, version, license, content_hash)
           VALUES ('taxonomy', 'copertura di riserva', 'v1', 'interna', 'h') RETURNING source_id""").fetchone()[0])
    return {"admin": admin, "task": task, "fonte": fonte}


def _evidenza(conn, mondo, dimensione, punteggio, quando, qualita=1, tipo="llm_prior"):
    conn.execute(
        """INSERT INTO evidence_items (source_id, evidence_type, task_id, dimension, raw_value, score_0_4, quality,
                                       observed_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (mondo["fonte"], tipo, mondo["task"], dimensione, punteggio, punteggio, qualita, quando))


def _copertura(conn, snapshot):
    return {r[0]: (float(r[1]), float(r[2]), float(r[3]), r[4]) for r in conn.execute(
        "SELECT dimension, c_mean, c_low, c_high, n_evidence FROM task_capability WHERE snapshot_id = %s",
        (snapshot,))}


def test_snapshot_di_riserva_dalle_evidenze(conn, mondo):
    _evidenza(conn, mondo, "k1", 3, "2026-10-17")
    _evidenza(conn, mondo, "k2", 2, "2026-10-17")
    _evidenza(conn, mondo, "k3", 1, "2026-10-17")
    snapshot = proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180,
                                        motivazione="prima copertura di riserva")
    assert _copertura(conn, snapshot) == {"k1": (3, 3, 3, 1), "k2": (2, 2, 2, 1), "k3": (1, 1, 1, 1)}
    stato = conn.execute("SELECT status, tipo_capacita, method_version, half_life_days FROM capability_snapshots "
                         "WHERE snapshot_id = %s", (snapshot,)).fetchone()
    assert stato == ("proposed", "riserva", METODO_RISERVA, 180)


def test_decadimento_e_disaccordo(conn, mondo):
    _evidenza(conn, mondo, "k1", 4, "2026-10-17")   # peso 1
    _evidenza(conn, mondo, "k1", 1, "2026-04-20")   # 180 giorni prima: peso 1/2
    for dimensione in ("k2", "k3"):
        _evidenza(conn, mondo, dimensione, 2, "2026-10-17")
    snapshot = proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180,
                                        motivazione="x")
    media, basso, alto, n = _copertura(conn, snapshot)["k1"]
    assert media == pytest.approx(3.0, abs=0.01) and (basso, alto, n) == (1, 4, 2)  # (4 + 0,5) / 1,5


def test_evidenza_su_tutte_le_dimensioni(conn, mondo):
    _evidenza(conn, mondo, "any", 2, "2026-10-17")
    snapshot = proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180,
                                        motivazione="x")
    assert set(_copertura(conn, snapshot)) == {"k1", "k2", "k3"}


def test_evidenze_future_escluse(conn, mondo):
    _evidenza(conn, mondo, "any", 2, "2026-12-01")
    with pytest.raises(ValueError, match="evidenz"):
        proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180, motivazione="x")


def test_pubblicazione_con_atto_e_un_solo_snapshot_pubblicato(conn, mondo):
    _evidenza(conn, mondo, "any", 2, "2026-10-17")
    primo = proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180, motivazione="x")
    pubblica_snapshot(conn, mondo["admin"], primo, nota="prima copertura di riserva, qualità minima")
    secondo = proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-18", emivita_giorni=180, motivazione="x")
    atto = pubblica_snapshot(conn, mondo["admin"], secondo, nota="aggiornamento")
    stati = dict(conn.execute("SELECT snapshot_id::text, status FROM capability_snapshots").fetchall())
    assert stati == {primo: "retired", secondo: "published"}
    assert conn.execute("SELECT tipo_oggetto, atto FROM registro_decisioni WHERE decisione_id = %s",
                        (atto,)).fetchone() == ("snapshot_capacita", "approvazione")


def test_solo_chi_approva_gli_snapshot_pubblica(conn, mondo):
    _evidenza(conn, mondo, "any", 2, "2026-10-17")
    snapshot = proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180, motivazione="x")
    estraneo = crea_utente(conn, "sso|estraneo")
    with pytest.raises(PermessoNegato):
        pubblica_snapshot(conn, estraneo, snapshot, nota="x")


def test_emivita_positiva(conn, mondo):
    with pytest.raises(ValueError, match="emivita"):
        proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=0, motivazione="x")


def test_snapshot_e_calcolo_con_il_ruolo_applicativo(conn, mondo):
    """Il flusso della fase 4 funziona con i privilegi dell'applicazione, non del proprietario."""
    from neartech.calcolo import calcola_organizzazione
    from neartech.occorrenze import documento, registra_occorrenza, ruolo
    from neartech.organizzazioni import crea_organizzazione

    org = crea_organizzazione(conn, mondo["admin"], nome="Org sintetica", codice="sintetica")
    registra_occorrenza(conn, org, task_id=mondo["task"], ruolo_id=ruolo(conn, org, "Coordinatore"),
                        documento_id=documento(conn, org, nome_file="m.docx", sha256="a" * 64, licenza="interno"),
                        estratto="compone i turni", nota_contesto=None, model_name="m", prompt_hash="h")
    conn.execute("INSERT INTO rubric_versions (version, is_current, approved_by) VALUES ('r', true, 'comitato')")
    conn.execute("""INSERT INTO weight_profiles (profile_id, w_k1, w_k2, w_k3, lambda_r, w_d1, w_d2, w_d3, w_d4,
                                                 theta_n, theta_d, is_active, approved_by)
                    VALUES ('p', 0.4, 0.4, 0.2, 0.5, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5, true, 'comitato')""")
    for voce, valore in (("k1", 2), ("k2", 2), ("k3", 0), ("r", 2), ("d1", 1), ("d2", 2)):
        conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind, rater_ref,
                                                     rubric_version) VALUES ('task', %s, %s, %s, 'llm', 'm', 'r')""",
                     (mondo["task"], voce, valore))
    _evidenza(conn, mondo, "any", 2, "2026-10-17")
    conn.execute("SET LOCAL ROLE neartech_app")
    snapshot = proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180, motivazione="x")
    pubblica_snapshot(conn, mondo["admin"], snapshot, nota="riserva")
    assert calcola_organizzazione(conn, mondo["admin"], org, seme=1, estrazioni=50)["nuove"] == 1
    conn.execute("SET CONSTRAINTS ALL IMMEDIATE")


def test_qualita_diverse_rifiutate_senza_pesi_approvati(conn, mondo):
    _evidenza(conn, mondo, "any", 2, "2026-10-17", qualita=1)
    _evidenza(conn, mondo, "any", 3, "2026-10-17", qualita=2)
    with pytest.raises(ValueError, match="qualità"):
        proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180, motivazione="x")


def test_evidenze_di_un_task_fuso_valgono_per_il_superstite(conn, mondo):
    fuso = str(conn.execute("INSERT INTO canonical_tasks (title_it, granularity, status, merged_into) "
                            "VALUES ('Task fuso', 2, 'merged', %s) RETURNING task_id", (mondo["task"],)).fetchone()[0])
    conn.execute("""INSERT INTO evidence_items (source_id, evidence_type, task_id, dimension, raw_value, score_0_4,
                                                quality, observed_at)
                    VALUES (%s, 'llm_prior', %s, 'any', 3, 3, 1, '2026-10-17')""", (mondo["fonte"], fuso))
    snapshot = proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180, motivazione="x")
    task = {str(r[0]) for r in conn.execute("SELECT task_id FROM task_capability WHERE snapshot_id = %s", (snapshot,))}
    assert task == {mondo["task"]}


def test_il_database_protegge_il_ciclo_di_vita_dello_snapshot(conn, mondo):
    import psycopg
    with pytest.raises(psycopg.errors.RaiseException, match="nasce proposto"):
        conn.execute("""INSERT INTO capability_snapshots (as_of, method_version, half_life_days, status, tipo_capacita,
                                                          approved_by, approved_at)
                        VALUES ('2026-10-17', 'x', 180, 'published', 'riserva', 'io', now())""")


def test_senza_atto_lo_snapshot_non_si_pubblica_e_la_copertura_pubblicata_non_cambia(conn, mondo):
    import psycopg
    _evidenza(conn, mondo, "any", 2, "2026-10-17")
    snapshot = proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180, motivazione="x")
    with pytest.raises(psycopg.errors.RaiseException, match="atto di approvazione"):
        with conn.transaction():
            conn.execute("UPDATE capability_snapshots SET status = 'published', approved_by = 'io', approved_at = now()"
                         " WHERE snapshot_id = %s", (snapshot,))
    atto = pubblica_snapshot(conn, mondo["admin"], snapshot, nota="ok")
    assert conn.execute("SELECT dettagli FROM registro_decisioni WHERE decisione_id = %s",
                        (atto,)).fetchone()[0]["stesso_proponente"] is True
    with pytest.raises(psycopg.errors.RaiseException, match="proposto"):
        conn.execute("""INSERT INTO task_capability (snapshot_id, task_id, dimension, c_mean, c_low, c_high, n_evidence)
                        SELECT %s, task_id, 'k1', 4, 4, 4, 1 FROM canonical_tasks LIMIT 1""", (snapshot,))


def test_banda_di_mezzo_livello_attorno_a_una_sola_evidenza(conn, mondo):
    _evidenza(conn, mondo, "k1", 3, "2026-10-17")
    _evidenza(conn, mondo, "k2", 4, "2026-10-17")
    _evidenza(conn, mondo, "k3", 0, "2026-10-17")
    snapshot = proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180,
                                        motivazione="x", banda=0.5)
    copertura = _copertura(conn, snapshot)
    assert (copertura["k1"][1:3], copertura["k2"][1:3], copertura["k3"][1:3]) == ((2.5, 3.5), (3.5, 4), (0, 0.5))
    assert conn.execute("SELECT method_version FROM capability_snapshots WHERE snapshot_id = %s",
                        (snapshot,)).fetchone()[0] == "riserva-v2-banda-0.5"


def test_banda_fuori_misura_rifiutata(conn, mondo):
    with pytest.raises(ValueError, match="banda"):
        proponi_snapshot_riserva(conn, mondo["admin"], as_of="2026-10-17", emivita_giorni=180, motivazione="x",
                                 banda=3)
