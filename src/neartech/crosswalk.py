"""Crosswalk Mapper: collega i task canonici italiani ai nodi delle tassonomie ufficiali.

Per ogni task canonico e per ogni schema di tassonomia:
1. si cercano i nodi più vicini per embedding (bge-m3);
2. un modello linguistico assegna a ciascun candidato una relazione SKOS
   (exact, broad, narrow, related) con una motivazione breve, oppure nessuna relazione;
3. si salvano solo le relazioni diverse da "nessuna", ciascuna con modello e impronta del prompt.

Regole dal piano:
- gli agenti propongono, il codice calcola: il modello non decide mai un punteggio;
- nessuna soglia di approvazione qui dentro: la validazione (campione del 10%, soglia di precisione)
  sta nelle tabelle di governance; le righe nascono con validated = false;
- il modello è fissato a una versione precisa (MODEL_ID), come per lo Scorer.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Literal

import psycopg
from pydantic import BaseModel, Field, ValidationError

MODEL_ID = "claude-haiku-5-5"
EMBEDDING_MODEL = "BAAI/bge-m3"
# Schemi di tassonomia con voci a livello di attività (le occupazioni ESCO_OCC non sono task).
CANDIDATE_SCHEMES = ("ONET_TASK", "ATLANTE_ATTIVITA", "ESCO_SKILL")
CANDIDATES_PER_SCHEME = 20
MAX_ATTEMPTS = 2
MAX_TOKENS = 2000

Relation = Literal["exact", "broad", "narrow", "related"]

SYSTEM_PROMPT = (
    "Sei un valutatore di corrispondenze tra task di lavoro. Ricevi un task da classificare e un elenco "
    "numerato di candidati da tassonomie ufficiali. Per ogni candidato che corrisponde al task scegli una "
    "relazione: \"exact\" (stesso compito), \"broad\" (il candidato è più ampio), \"narrow\" (il candidato è più "
    "stretto), \"related\" (affine ma non equivalente). Ignora i candidati che non corrispondono. "
    "Rispondi solo con un oggetto JSON: "
    "{\"relazioni\": [{\"n\": <numero del candidato>, \"relazione\": \"exact|broad|narrow|related\", "
    "\"confidenza\": <numero tra 0 e 1>, \"motivazione\": \"<una frase in italiano>\"}]}. "
    "Se nessun candidato corrisponde, rispondi con {\"relazioni\": []}."
)


class CrosswalkError(RuntimeError):
    pass


@dataclass(frozen=True)
class Candidate:
    node_id: str
    scheme: str
    code: str
    label: str


class _JudgementOut(BaseModel):
    n: int
    relazione: Relation
    confidenza: float = Field(ge=0, le=1)
    motivazione: str = Field(min_length=1)


class _JudgementList(BaseModel):
    relazioni: list[_JudgementOut]


@dataclass(frozen=True)
class Judgement:
    node_id: str
    relation: str
    confidence: float
    rationale: str


def prompt_hash() -> str:
    return hashlib.sha256((SYSTEM_PROMPT + "\n" + MODEL_ID).encode("utf-8")).hexdigest()


def find_candidates(conn: psycopg.Connection, task_id: str, scheme: str, k: int = CANDIDATES_PER_SCHEME) -> list[Candidate]:
    """I k nodi più vicini al task, nello schema indicato, per coseno."""
    rows = conn.execute(
        """
        SELECT n.node_id, n.scheme, n.code, n.label
        FROM taxonomy_embeddings e
        JOIN taxonomy_nodes n ON n.node_id = e.node_id
        WHERE e.model_name = %s AND n.scheme = %s
        ORDER BY e.vec <=> (SELECT t.vec FROM task_embeddings t
                            WHERE t.task_id = %s AND t.model_name = %s)
        LIMIT %s
        """,
        (EMBEDDING_MODEL, scheme, task_id, EMBEDDING_MODEL, k),
    ).fetchall()
    return [Candidate(node_id=str(r[0]), scheme=r[1], code=r[2], label=r[3]) for r in rows]


def _user_message(task_title: str, candidates: list[Candidate]) -> str:
    lines = [f"{i}. [{c.code}] {c.label}" for i, c in enumerate(candidates, start=1)]
    return f"Task canonico: {task_title}\n\nCandidati:\n" + "\n".join(lines)


def _parse(text: str, candidates: list[Candidate]) -> list[Judgement]:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("nessun oggetto JSON nella risposta")
    parsed = _JudgementList.model_validate(json.loads(match.group(0)))
    by_n = {i: c for i, c in enumerate(candidates, start=1)}
    out: list[Judgement] = []
    seen: set[int] = set()
    for j in parsed.relazioni:
        if j.n not in by_n:
            raise ValueError(f"candidato inesistente: {j.n}")
        if j.n in seen:
            raise ValueError(f"candidato valutato due volte: {j.n}")
        seen.add(j.n)
        out.append(Judgement(node_id=by_n[j.n].node_id, relation=j.relazione,
                             confidence=j.confidenza, rationale=j.motivazione))
    return out


def judge(client, task_title: str, candidates: list[Candidate]) -> list[Judgement]:
    """Giudica un blocco di candidati con una sola chiamata. Ritorna solo le relazioni diverse da nessuna."""
    if not candidates:
        return []
    user = _user_message(task_title, candidates)
    last_error: Exception | None = None
    for _attempt in range(MAX_ATTEMPTS):
        resp = client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        try:
            return _parse(text, candidates)
        except (ValueError, ValidationError, json.JSONDecodeError) as err:
            last_error = err
    raise CrosswalkError(f"risposta non valida dopo {MAX_ATTEMPTS} tentativi: {last_error}")


def save_judgements(conn: psycopg.Connection, task_id: str, judgements: list[Judgement]) -> int:
    """Salva le relazioni. Una coppia task-nodo ha una sola relazione: le esistenti non vengono sovrascritte."""
    phash = prompt_hash()
    inserted = 0
    with conn.transaction():
        for j in judgements:
            cur = conn.execute(
                """
                INSERT INTO task_mappings
                  (task_id, node_id, relation, confidence, rationale, validated, model_name, prompt_hash)
                VALUES (%s, %s, %s, %s, %s, false, %s, %s)
                ON CONFLICT (task_id, node_id) DO NOTHING
                """,
                (task_id, j.node_id, j.relation, round(j.confidence, 2), j.rationale, MODEL_ID, phash),
            )
            inserted += cur.rowcount
    return inserted


def map_task(conn: psycopg.Connection, client, task_id: str, task_title: str) -> int:
    """Esegue il crosswalk per un task canonico su tutti gli schemi. Ritorna le relazioni salvate."""
    total = 0
    for scheme in CANDIDATE_SCHEMES:
        candidates = find_candidates(conn, task_id, scheme)
        judgements = judge(client, task_title, candidates)
        total += save_judgements(conn, task_id, judgements)
    return total
