"""Verifiche di F0 dal piano (sezione 'Test minimo di F0') e test dei caricatori.

I dati sono sintetici. Le tre verifiche di F0 riguardano lo schema e la vista:
il job di calcolo non è ancora implementato, quindi i risultati vengono
inseriti direttamente nelle tabelle, come farebbe il job.
"""

from pathlib import Path

import psycopg
import pytest

from neartech.evidence import add_evidence
from neartech.models import EvidenceIn
from neartech.taxonomy import load_taxonomy

FIXTURES = Path(__file__).parent / "fixtures"


def _weights(profile_id: str, *, org_id=None, active=True) -> tuple:
    return (profile_id, org_id, 0.4, 0.4, 0.2, 0.25, 0.25, 0.25, 0.25, active)


WEIGHT_SQL = """
INSERT INTO weight_profiles
  (profile_id, org_id, w_k1, w_k2, w_k3, w_d1, w_d2, w_d3, w_d4, is_active)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def _setup_base(conn: psycopg.Connection) -> dict:
    """Crea org, ruolo, task, occorrenza, fonte, rubrica e profilo di default."""
    org = conn.execute("INSERT INTO organizations (name) VALUES ('Org sintetica') RETURNING org_id").fetchone()[0]
    role = conn.execute(
        "INSERT INTO roles (org_id, name) VALUES (%s, 'Coordinatore sintetico') RETURNING role_id", (org,)
    ).fetchone()[0]
    task = conn.execute(
        "INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Task sintetico', 2) RETURNING task_id"
    ).fetchone()[0]
    src = conn.execute(
        """INSERT INTO sources (kind, name, version, license, content_hash)
           VALUES ('org_document', 'Mansionario sintetico', '1', 'interno', 'hash-synth') RETURNING source_id"""
    ).fetchone()[0]
    occ = conn.execute(
        """INSERT INTO task_occurrences
             (task_id, role_id, raw_snippet, time_share, source_id, model_name, prompt_hash)
           VALUES (%s, %s, 'frammento sintetico', 1.0, %s, 'test', 'test') RETURNING occurrence_id""",
        (task, role, src),
    ).fetchone()[0]
    conn.execute("INSERT INTO rubric_versions (version, is_current) VALUES ('r-test', true)")
    conn.execute(WEIGHT_SQL, _weights("default-test"))
    return {"org": org, "role": role, "occurrence": occ}


def _snapshot(conn: psycopg.Connection, status: str, as_of: str) -> str:
    return conn.execute(
        """INSERT INTO capability_snapshots (as_of, method_version, half_life_days, status)
           VALUES (%s, 'm-test', 180, %s) RETURNING snapshot_id""",
        (as_of, status),
    ).fetchone()[0]


def _estimate(conn, occ, snapshot, n: float, d: float) -> None:
    conn.execute(
        """INSERT INTO policy_estimates
             (occurrence_id, profile_id, snapshot_id, rubric_version,
              n_mean, n_sd, d_mean, d_sd, p_q1, p_q2, p_q3, p_q4, d_source_mix)
           VALUES (%s, 'default-test', %s, 'r-test', %s, 0.05, %s, 0.05, 0.7, 0.1, 0.1, 0.1, '{"preliminare": 1.0}')""",
        (occ, snapshot, n, d),
    )


# ---- Verifiche di F0 dal piano -------------------------------------------------

def test_due_profili_attivi_nello_stesso_ambito_sono_rifiutati(conn):
    conn.execute(WEIGHT_SQL, _weights("globale-a"))
    with pytest.raises(psycopg.errors.UniqueViolation):
        with conn.transaction():  # savepoint: l'errore atteso non abortisce il test
            conn.execute(WEIGHT_SQL, _weights("globale-b"))


def test_un_task_con_piu_valutazioni_produce_una_sola_riga_per_configurazione(conn):
    base = _setup_base(conn)
    snap = _snapshot(conn, "published", "2026-10-01")
    # Due giudizi distinti sullo stesso item: di modello e umano, entrambi conservati.
    for rater_kind, rater_ref in [("llm", "modello-x"), ("expert", "esperto-1")]:
        conn.execute(
            """INSERT INTO assessment_runs
                 (target_kind, target_id, item, value, rater_kind, rater_ref, rubric_version)
               VALUES ('task', (SELECT task_id FROM task_occurrences WHERE occurrence_id = %s), 'k2', 2, %s, %s, 'r-test')""",
            (base["occurrence"], rater_kind, rater_ref),
        )
    count = conn.execute("SELECT count(*) FROM assessment_runs").fetchone()[0]
    assert count == 2  # ogni giudizio è un record a sé
    _estimate(conn, base["occurrence"], snap, 0.3, 0.6)
    with pytest.raises(psycopg.errors.UniqueViolation):
        with conn.transaction():
            _estimate(conn, base["occurrence"], snap, 0.4, 0.6)  # stessa configurazione: nessuna seconda riga
    rows = conn.execute("SELECT count(*) FROM policy_estimates WHERE occurrence_id = %s", (base["occurrence"],)).fetchone()[0]
    assert rows == 1


def test_dopo_un_nuovo_snapshot_la_vista_restituisce_una_riga_per_ruolo(conn):
    base = _setup_base(conn)
    old = _snapshot(conn, "published", "2026-09-01")
    _estimate(conn, base["occurrence"], old, 0.3, 0.6)
    assert conn.execute("SELECT count(*) FROM v_role_metrics").fetchone()[0] == 1

    # Pubblicazione di un nuovo snapshot: il precedente va ritirato (un solo published).
    conn.execute("UPDATE capability_snapshots SET status = 'retired' WHERE snapshot_id = %s", (old,))
    new = _snapshot(conn, "published", "2026-10-01")
    _estimate(conn, base["occurrence"], new, 0.5, 0.6)

    rows = conn.execute(
        "SELECT role_id, n_tasks, barycenter_n FROM v_role_metrics WHERE role_id = %s", (base["role"],)
    ).fetchall()
    assert len(rows) == 1
    assert rows[0][1] == 1
    assert float(rows[0][2]) == pytest.approx(0.5)  # valore del nuovo snapshot, non del vecchio


# ---- Caricatori --------------------------------------------------------------

def test_tassonomia_caricata_due_volte_non_duplica_i_nodi(conn):
    path = FIXTURES / "taxonomy_sample.csv"
    first = load_taxonomy(conn, path, name="sintetica", version="1.0", license="test")
    second = load_taxonomy(conn, path, name="sintetica", version="1.0", license="test")
    assert first.nodes_inserted == 3
    assert second.nodes_inserted == 0
    assert second.nodes_total == 3


def test_tassonomia_con_stessa_versione_e_contenuto_diverso_viene_rifiutata(conn, tmp_path):
    path = tmp_path / "t.csv"
    path.write_text((FIXTURES / "taxonomy_sample.csv").read_text(encoding="utf-8"), encoding="utf-8")
    load_taxonomy(conn, path, name="sintetica", version="1.0", license="test")
    path.write_text((FIXTURES / "taxonomy_sample.csv").read_text(encoding="utf-8") + "ONET_TASK,SYN-9,Nuovo,it,\n",
                    encoding="utf-8")
    with pytest.raises(ValueError, match="incrementa la versione"):
        load_taxonomy(conn, path, name="sintetica", version="1.0", license="test")


def test_parent_code_collega_il_genitore(conn):
    load_taxonomy(conn, FIXTURES / "taxonomy_sample.csv", name="sintetica", version="1.0", license="test")
    child, parent = conn.execute(
        """SELECT c.parent_id IS NOT NULL, p.code FROM taxonomy_nodes c
           JOIN taxonomy_nodes p ON p.node_id = c.parent_id WHERE c.code = 'SYN-3'"""
    ).fetchone()
    assert child and parent == "SYN-1"


def test_evidenza_su_nodo_inesistente_viene_rifiutata(conn):
    load_taxonomy(conn, FIXTURES / "taxonomy_sample.csv", name="sintetica", version="1.0", license="test")
    conn.execute(
        """INSERT INTO sources (kind, name, version, license, content_hash)
           VALUES ('evidence', 'fonte-sintetica', '1', 'test', 'h')"""
    )
    ev = EvidenceIn(
        source_name="fonte-sintetica", source_version="1", evidence_type="benchmark", dimension="k2",
        raw_value=0.7, score_0_4=2.8, quality=0.9, observed_at="2026-09-01",
        node_scheme="ONET_TASK", node_code="NON-ESISTE",
    )
    with pytest.raises(ValueError, match="nodo non trovato"):
        add_evidence(conn, ev)


def test_evidenza_valida_viene_inserita(conn):
    load_taxonomy(conn, FIXTURES / "taxonomy_sample.csv", name="sintetica", version="1.0", license="test")
    conn.execute(
        """INSERT INTO sources (kind, name, version, license, content_hash)
           VALUES ('evidence', 'fonte-sintetica', '1', 'test', 'h')"""
    )
    ev = EvidenceIn(
        source_name="fonte-sintetica", source_version="1", evidence_type="benchmark", dimension="k2",
        raw_value=0.7, score_0_4=2.8, quality=0.9, observed_at="2026-09-01",
        node_scheme="ONET_TASK", node_code="SYN-1",
    )
    evidence_id = add_evidence(conn, ev)
    assert evidence_id
    assert conn.execute("SELECT count(*) FROM evidence_items").fetchone()[0] == 1


def test_evidenza_con_punteggio_fuori_scala_e_rifiutata_dal_modello():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        EvidenceIn(
            source_name="x", source_version="1", evidence_type="benchmark", dimension="k1",
            raw_value=1, score_0_4=4.5, quality=0.5, observed_at="2026-01-01",
        )
