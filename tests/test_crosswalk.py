"""Test del Crosswalk Mapper con un client finto: nessuna chiamata al modello."""

import json
from types import SimpleNamespace

import pytest

from neartech.crosswalk import (
    CANDIDATES_PER_SCHEME,
    MODEL_ID,
    CrosswalkError,
    find_candidates,
    judge,
    map_task,
    prompt_hash,
    save_judgements,
)

DIM = 1024


def _unit(i: int) -> list[float]:
    v = [0.0] * DIM
    v[i] = 1.0
    return v


def _vec(v: list[float]) -> str:
    return "[" + ",".join(str(x) for x in v) + "]"


class FakeClient:
    """Imita client.messages.create restituendo testi preparati."""

    def __init__(self, *texts: str):
        self.texts = list(texts)
        self.calls = 0
        self.messages = self

    def create(self, **kwargs):
        self.calls += 1
        text = self.texts.pop(0) if len(self.texts) > 1 else self.texts[0]
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


@pytest.fixture
def base(conn):
    """Due schemi, quattro nodi e un task canonico il cui embedding coincide con il primo nodo di O*NET."""
    src = conn.execute(
        "INSERT INTO sources (kind, name, version, license, content_hash) "
        "VALUES ('taxonomy', 'test', '1', 'test', 'h') RETURNING source_id"
    ).fetchone()[0]
    nodes = {}
    specs = [
        ("ONET_TASK", "T1", "Compilare i turni del personale", 0),
        ("ONET_TASK", "T2", "Gestire la contabilità", 1),
        ("ESCO_SKILL", "S1", "pianificazione del lavoro", 2),
        ("ESCO_SKILL", "S2", "saldatura", 3),
    ]
    for scheme, code, label, dim in specs:
        node_id = conn.execute(
            "INSERT INTO taxonomy_nodes (scheme, code, label, lang, source_id) "
            "VALUES (%s, %s, %s, 'it', %s) RETURNING node_id",
            (scheme, code, label, src),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO taxonomy_embeddings (node_id, model_name, vec) VALUES (%s, %s, %s::vector)",
            (node_id, "BAAI/bge-m3", _vec(_unit(dim))),
        )
        nodes[code] = str(node_id)
    task_id = conn.execute(
        "INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Pianificare i turni', 2) RETURNING task_id"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO task_embeddings (task_id, model_name, vec) VALUES (%s, 'BAAI/bge-m3', %s::vector)",
        (task_id, _vec(_unit(0))),
    )
    return {"task_id": str(task_id), "nodes": nodes}


def test_candidati_per_schema_ordinati_per_vicinanza(conn, base):
    cands = find_candidates(conn, base["task_id"], "ONET_TASK")
    assert [c.code for c in cands] == ["T1", "T2"]
    assert all(c.scheme == "ONET_TASK" for c in cands)
    assert len(cands) <= CANDIDATES_PER_SCHEME


def test_giudizio_valido_viene_parsato(base):
    candidates = find_candidates_stub(base)
    text = json.dumps({"relazioni": [
        {"n": 1, "relazione": "exact", "confidenza": 0.9, "motivazione": "stesso compito"}
    ]})
    out = judge(FakeClient(text), "Pianificare i turni", candidates)
    assert len(out) == 1
    assert out[0].node_id == candidates[0].node_id and out[0].relation == "exact"


def test_candidato_inesistente_viene_rifiutato(base):
    candidates = find_candidates_stub(base)
    bad = json.dumps({"relazioni": [{"n": 9, "relazione": "exact", "confidenza": 0.5, "motivazione": "x"}]})
    with pytest.raises(CrosswalkError):
        judge(FakeClient(bad), "Pianificare i turni", candidates)


def test_relazione_non_ammessa_viene_rifiutata(base):
    candidates = find_candidates_stub(base)
    bad = json.dumps({"relazioni": [{"n": 1, "relazione": "nessuna", "confidenza": 0.5, "motivazione": "x"}]})
    with pytest.raises(CrosswalkError):
        judge(FakeClient(bad), "Pianificare i turni", candidates)


def test_salvataggio_con_provenienza_e_idempotente(conn, base):
    cands = find_candidates_stub(base)
    text = json.dumps({"relazioni": [
        {"n": 1, "relazione": "broad", "confidenza": 0.7, "motivazione": "più ampio"}
    ]})
    out = judge(FakeClient(text), "Pianificare i turni", cands)
    assert save_judgements(conn, base["task_id"], out) == 1
    assert save_judgements(conn, base["task_id"], out) == 0  # la stessa coppia non viene sovrascritta
    row = conn.execute(
        "SELECT relation, validated, model_name, prompt_hash FROM task_mappings WHERE task_id = %s",
        (base["task_id"],),
    ).fetchone()
    assert row == ("broad", False, MODEL_ID, prompt_hash())


def test_map_task_salva_solo_relazioni_non_nulle(conn, base):
    # Ogni chiamata (uno per schema) risponde con una sola relazione sul primo candidato.
    text = json.dumps({"relazioni": [
        {"n": 1, "relazione": "related", "confidenza": 0.6, "motivazione": "affine"}
    ]})
    saved = map_task(conn, FakeClient(text), base["task_id"], "Pianificare i turni")
    # ONET_TASK e ESCO_SKILL hanno candidati e una relazione ciascuno; ATLANTE_ATTIVITA non ha nodi nel test.
    assert saved == 2
    count = conn.execute("SELECT count(*) FROM task_mappings WHERE task_id = %s", (base["task_id"],)).fetchone()[0]
    assert count == 2


def find_candidates_stub(base):
    from neartech.crosswalk import Candidate

    return [Candidate(node_id=base["nodes"]["T1"], scheme="ONET_TASK", code="T1",
                      label="Compilare i turni del personale"),
            Candidate(node_id=base["nodes"]["T2"], scheme="ONET_TASK", code="T2",
                      label="Gestire la contabilità")]
