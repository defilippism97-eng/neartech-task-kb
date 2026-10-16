"""Scorer: valuta un task su un item della rubrica con un modello linguistico.

Regole dal piano:
- un giudizio di modello è un record a sé, sempre marcato come `llm`;
- ogni voce ha 5 campioni indipendenti, e si conservano tutti;
- la versione della rubrica e l'impronta del prompt accompagnano ogni record;
- l'aritmetica non passa mai dal modello: qui si salva solo il punteggio.

Il modello è fissato a una versione precisa (MODEL_ID). Cambiarla richiede
il set di controllo e la ritaratura del prompt prima di nuove valutazioni.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Literal

import psycopg
from pydantic import BaseModel, Field, ValidationError

MODEL_ID = "claude-haiku-5-5"
SAMPLES_PER_ITEM = 5
MAX_ATTEMPTS = 2  # un nuovo tentativo se la risposta non è un JSON valido

NItem = Literal["k1", "k2", "k3", "r"]
DItem = Literal["d1", "d2", "d3", "d4"]


class ScoreOutput(BaseModel):
    value: int = Field(ge=0, le=4)
    rationale: str = Field(min_length=1)


@dataclass(frozen=True)
class ScoreSample:
    item: str
    value: int
    rationale: str
    prompt_hash: str


class ScoringError(RuntimeError):
    pass


def _prompt_hash(system: str, user: str) -> str:
    return hashlib.sha256((system + "\n---\n" + user).encode("utf-8")).hexdigest()


def _parse(text: str) -> ScoreOutput:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("nessun oggetto JSON nella risposta")
    return ScoreOutput.model_validate(json.loads(match.group(0)))


def score_item(
    client,
    *,
    task_title: str,
    item: str,
    rubric_text: str,
    n_samples: int = SAMPLES_PER_ITEM,
) -> list[ScoreSample]:
    """Ritorna n_samples campioni indipendenti per un item della rubrica.

    `client` è un anthropic.Anthropic (o un oggetto con la stessa interfaccia messages.create).
    """
    system = (
        "Sei un valutatore. Applica la rubrica al task indicato e rispondi "
        "solo con un oggetto JSON: {\"value\": <intero 0-4>, \"rationale\": \"<breve motivazione>\"}."
    )
    user = f"Rubrica per l'item {item}:\n{rubric_text}\n\nTask da valutare: {task_title}"
    phash = _prompt_hash(system, user)

    samples: list[ScoreSample] = []
    for _ in range(n_samples):
        last_error: Exception | None = None
        for _attempt in range(MAX_ATTEMPTS):
            resp = client.messages.create(
                model=MODEL_ID,
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
            try:
                out = _parse(text)
                samples.append(ScoreSample(item=item, value=out.value, rationale=out.rationale, prompt_hash=phash))
                break
            except (ValueError, ValidationError, json.JSONDecodeError) as err:
                last_error = err
        else:
            raise ScoringError(f"risposta non valida dopo {MAX_ATTEMPTS} tentativi: {last_error}")
    return samples


def save_samples(
    conn: psycopg.Connection,
    *,
    task_id: str,
    rubric_version: str,
    samples: list[ScoreSample],
    campaign_id: str | None = None,
) -> int:
    """Salva ogni campione come record separato in assessment_runs (rater_kind = 'llm')."""
    with conn.transaction():
        for s in samples:
            conn.execute(
                """
                INSERT INTO assessment_runs
                  (target_kind, target_id, item, value, rater_kind, rater_ref,
                   rubric_version, prompt_hash, rationale, campaign_id)
                VALUES ('task', %s, %s, %s, 'llm', %s, %s, %s, %s, %s)
                """,
                (task_id, s.item, s.value, MODEL_ID, rubric_version, s.prompt_hash, s.rationale, campaign_id),
            )
    return len(samples)
