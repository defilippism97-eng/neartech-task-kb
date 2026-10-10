"""Test dello scorer con un client finto: nessuna chiamata di rete.

Il test con il modello reale è in fondo ed è saltato senza NEARTECH_ANTHROPIC_API_KEY.
"""

import os
from types import SimpleNamespace

import pytest

from neartech.scorer import MODEL_ID, SAMPLES_PER_ITEM, ScoringError, save_samples, score_item


class FakeMessages:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = self.replies.pop(0)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


class FakeClient:
    def __init__(self, replies):
        self.messages = FakeMessages(replies)


def test_cinque_campioni_indipendenti_con_il_modello_fissato():
    client = FakeClient(['{"value": 2, "rationale": "a"}'] * SAMPLES_PER_ITEM)
    samples = score_item(client, task_title="Comporre il piano turni", item="k2", rubric_text="...")
    assert len(samples) == SAMPLES_PER_ITEM == 5
    assert all(c["model"] == MODEL_ID == "claude-haiku-5-5" for c in client.messages.calls)


def test_risposta_non_json_viene_ritentata_una_volta():
    client = FakeClient(["non è json", '{"value": 3, "rationale": "ok"}'] + ['{"value": 3, "rationale": "ok"}'] * 4)
    samples = score_item(client, task_title="t", item="d1", rubric_text="...")
    assert [s.value for s in samples] == [3] * 5
    assert len(client.messages.calls) == 6  # 1 tentativo fallito + 5 campioni


def test_valore_fuori_scala_non_viene_accettato():
    client = FakeClient(['{"value": 7, "rationale": "x"}'] * 2)
    with pytest.raises(ScoringError):
        score_item(client, task_title="t", item="k1", rubric_text="...", n_samples=1)


def test_hash_del_prompt_stabile_e_presente_in_ogni_campione():
    client = FakeClient(['{"value": 1, "rationale": "a"}'] * 2)
    s = score_item(client, task_title="t", item="k3", rubric_text="R", n_samples=2)
    assert s[0].prompt_hash == s[1].prompt_hash and len(s[0].prompt_hash) == 64


def test_campioni_salvati_come_record_separati_marcati_llm(conn):
    # Un task e una rubrica minimi, dentro la transazione di test.
    task = conn.execute(
        "INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Task sintetico scorer', 2) RETURNING task_id"
    ).fetchone()[0]
    conn.execute("INSERT INTO rubric_versions (version, is_current) VALUES ('r-scorer', true)")
    client = FakeClient(['{"value": 2, "rationale": "a"}'] * 5)
    samples = score_item(client, task_title="t", item="k2", rubric_text="R")
    assert save_samples(conn, task_id=task, rubric_version="r-scorer", samples=samples) == 5
    rows = conn.execute(
        "SELECT rater_kind, rater_ref, item FROM assessment_runs WHERE target_id = %s", (task,)
    ).fetchall()
    assert len(rows) == 5
    assert {r[0] for r in rows} == {"llm"} and {r[1] for r in rows} == {MODEL_ID}


@pytest.mark.skipif(not os.environ.get("NEARTECH_ANTHROPIC_API_KEY"), reason="serve NEARTECH_ANTHROPIC_API_KEY")
def test_modello_reale_risponde_in_formato_atteso():
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["NEARTECH_ANTHROPIC_API_KEY"])
    samples = score_item(
        client,
        task_title="Registrare presenze da badge",
        item="k1",
        rubric_text="0: input strutturato e completo. 4: contesto aperto che cambia durante l'esecuzione.",
        n_samples=2,
    )
    assert len(samples) == 2
    assert all(0 <= s.value <= 4 for s in samples)
