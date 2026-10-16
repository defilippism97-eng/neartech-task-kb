"""Canonicalizer: unisce i task canonici equivalenti emersi da fonti diverse.

Per ogni task attivo di granularità 2:
1. si cercano i 5 task più vicini per embedding (bge-m3);
2. il modello decide per ciascun vicino: "stessa_attivita" oppure "diversa", con una motivazione;
3. ogni decisione è un record (fusioni_proposte), mai sovrascritto;
4. le coppie con almeno una decisione "stessa_attivita" vengono fuse: il task con più occorrenze resta,
   gli altri diventano 'merged' e puntano a quello rimasto, con occorrenze e relazioni spostate.

Regole dal piano: il modello propone, il codice applica; nessuna soglia di similarità nel codice
(si confrontano sempre i k vicini più prossimi); le aree di responsabilità (granularità 3) non sono task
e non entrano nel confronto.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Literal

import psycopg
from pydantic import BaseModel, Field, ValidationError

from neartech.crosswalk import EMBEDDING_MODEL

MODEL_ID = "claude-haiku-5-5"
NEIGHBOURS = 5
MAX_ATTEMPTS = 2
MAX_TOKENS = 4000

Decisione = Literal["stessa_attivita", "diversa"]

SYSTEM_PROMPT = (
    "Sei un revisore di task di lavoro. Ricevi un task di riferimento e un elenco numerato di task simili, "
    "provenienti da job description diverse. Per ciascun candidato decidi: \"stessa_attivita\" se descrive "
    "lo stesso compito di lavoro (stesso risultato e stesso oggetto, formulazioni diverse ammesse), "
    "\"diversa\" altrimenti (anche se sono affini o uno è più ampio dell'altro). "
    "Rispondi solo con un oggetto JSON: "
    "{\"giudizi\": [{\"n\": <numero del candidato>, \"decisione\": \"stessa_attivita|diversa\", "
    "\"motivazione\": \"<una frase in italiano>\"}]}."
)


class CanonicalizerError(RuntimeError):
    pass


@dataclass(frozen=True)
class Vicino:
    task_id: str
    titolo: str
    occorrenze: int


class _Giudizio(BaseModel):
    n: int
    decisione: Decisione
    motivazione: str = Field(min_length=1)


class _Giudizi(BaseModel):
    giudizi: list[_Giudizio]


def prompt_hash() -> str:
    return hashlib.sha256((SYSTEM_PROMPT + "\n" + MODEL_ID).encode("utf-8")).hexdigest()


def trova_vicini(conn: psycopg.Connection, task_id: str, k: int = NEIGHBOURS) -> list[Vicino]:
    rows = conn.execute(
        """
        SELECT v.task_id, v.title_it,
               (SELECT count(*) FROM task_occurrences o WHERE o.task_id = v.task_id) AS occ
        FROM (
            SELECT t.task_id, t.title_it
            FROM canonical_tasks t
            JOIN task_embeddings eb ON eb.task_id = t.task_id AND eb.model_name = %s
            JOIN task_embeddings ea ON ea.task_id = %s AND ea.model_name = %s
            WHERE t.task_id <> %s AND t.status = 'active' AND t.granularity IN (1, 2)
            ORDER BY eb.vec <=> ea.vec
            LIMIT %s
        ) v
        """,
        (EMBEDDING_MODEL, task_id, EMBEDDING_MODEL, task_id, k),
    ).fetchall()
    return [Vicino(task_id=str(r[0]), titolo=r[1], occorrenze=int(r[2])) for r in rows]


def _messaggio(titolo: str, vicini: list[Vicino]) -> str:
    righe = [f"{i}. {v.titolo}" for i, v in enumerate(vicini, start=1)]
    return f"Task di riferimento: {titolo}\n\nCandidati:\n" + "\n".join(righe)


def _parse(text: str, vicini: list[Vicino]) -> list[tuple[Vicino, str, str]]:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("nessun oggetto JSON nella risposta")
    parsed = _Giudizi.model_validate(json.loads(match.group(0)))
    by_n = {i: v for i, v in enumerate(vicini, start=1)}
    out, visti = [], set()
    for g in parsed.giudizi:
        if g.n not in by_n:
            raise ValueError(f"candidato inesistente: {g.n}")
        if g.n in visti:
            raise ValueError(f"candidato valutato due volte: {g.n}")
        visti.add(g.n)
        out.append((by_n[g.n], g.decisione, g.motivazione))
    if len(out) != len(vicini):
        raise ValueError("non tutti i candidati sono stati giudicati")
    return out


def giudica(client, titolo: str, vicini: list[Vicino]) -> list[tuple[Vicino, str, str]]:
    ultimo: Exception | None = None
    for _ in range(MAX_ATTEMPTS):
        resp = client.messages.create(
            model=MODEL_ID,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _messaggio(titolo, vicini)}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        try:
            return _parse(text, vicini)
        except (ValueError, ValidationError, json.JSONDecodeError) as err:
            ultimo = err
    raise CanonicalizerError(f"{titolo}: risposta non valida dopo {MAX_ATTEMPTS} tentativi: {ultimo}")


def registra_giudizi(conn: psycopg.Connection, task_id: str, giudizi: list[tuple[Vicino, str, str]]) -> int:
    phash = prompt_hash()
    nuovi = 0
    for vicino, decisione, motivazione in giudizi:
        cur = conn.execute(
            """INSERT INTO fusioni_proposte
                 (task_id, altro_task_id, decisione, motivazione, model_name, prompt_hash)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (task_id, altro_task_id) DO NOTHING""",
            (task_id, vicino.task_id, decisione, motivazione, MODEL_ID, phash),
        )
        nuovi += cur.rowcount
    return nuovi


def _gruppi_da_fondere(conn: psycopg.Connection) -> list[list[str]]:
    """Gruppi di task che il modello ha giudicato equivalenti in almeno una direzione (chiusura transitiva)."""
    # Esclusi i task separati da una persona dopo una fusione sbagliata (neartech.scissione):
    # una loro nuova fusione richiede di nuovo il giudizio di un revisore.
    coppie = conn.execute(
        """SELECT f.task_id, f.altro_task_id FROM fusioni_proposte f
           WHERE f.decisione = 'stessa_attivita'
             AND NOT EXISTS (
               SELECT 1 FROM registro_decisioni r
               WHERE r.tipo_oggetto = 'task_canonico' AND r.atto = 'correzione'
                 AND r.dettagli ->> 'operazione' = 'scissione'
                 AND r.oggetto_id IN (f.task_id::text, f.altro_task_id::text))"""
    ).fetchall()
    padre: dict[str, str] = {}

    def radice(x: str) -> str:
        while padre.get(x, x) != x:
            x = padre[x]
        return x

    for a, b in coppie:
        a, b = str(a), str(b)
        padre.setdefault(a, a)
        padre.setdefault(b, b)
        ra, rb = radice(a), radice(b)
        if ra != rb:
            padre[rb] = ra
    gruppi: dict[str, list[str]] = {}
    for x in padre:
        gruppi.setdefault(radice(x), []).append(x)
    return [g for g in gruppi.values() if len(g) > 1]


def _array_uuid(ids: list[str]) -> str:
    """Letterale di array Postgres: vale sia per la connessione diretta sia per quella HTTPS."""
    return "{" + ",".join(ids) + "}"


def fondi(conn: psycopg.Connection, task_ids: list[str]) -> str:
    """Fonde un gruppo: il task con più occorrenze resta, gli altri puntano a lui. Ritorna l'id superstite."""
    occ = {
        str(r[0]): int(r[1]) for r in conn.execute(
            """SELECT t.task_id, count(o.occurrence_id) FROM canonical_tasks t
               LEFT JOIN task_occurrences o ON o.task_id = t.task_id
               WHERE t.task_id = ANY(%s::uuid[]) AND t.status = 'active' GROUP BY t.task_id""",
            (_array_uuid(task_ids),),
        ).fetchall()
    }
    if len(occ) < 2:
        return ""
    titoli = {str(r[0]): r[1] for r in conn.execute(
        "SELECT task_id, title_it FROM canonical_tasks WHERE task_id = ANY(%s::uuid[])", (_array_uuid(list(occ)),)
    ).fetchall()}
    superstite = max(occ, key=lambda t: (occ[t], -len(titoli[t]), titoli[t]))
    for m in occ:
        if m == superstite:
            continue
        # Occorrenze: se il ruolo ha già il superstite, si tiene quella del superstite.
        conn.execute(
            """DELETE FROM task_occurrences o WHERE o.task_id = %s
               AND EXISTS (SELECT 1 FROM task_occurrences s WHERE s.task_id = %s AND s.role_id = o.role_id)""",
            (m, superstite),
        )
        conn.execute("UPDATE task_occurrences SET task_id = %s WHERE task_id = %s", (superstite, m))
        # Relazioni: si trasferiscono quelle che il superstite non ha già.
        conn.execute(
            """INSERT INTO task_mappings (task_id, node_id, relation, confidence, rationale, validated, model_name, prompt_hash)
               SELECT %s, node_id, relation, confidence, rationale, validated, model_name, prompt_hash
               FROM task_mappings WHERE task_id = %s
               ON CONFLICT (task_id, node_id) DO NOTHING""",
            (superstite, m),
        )
        conn.execute("DELETE FROM task_mappings WHERE task_id = %s", (m,))
        conn.execute("DELETE FROM crosswalk_giudizi WHERE task_id = %s", (m,))
        conn.execute(
            "UPDATE canonical_tasks SET status = 'merged', merged_into = %s WHERE task_id = %s", (superstite, m)
        )
    return superstite


def canonicalizza(conn: psycopg.Connection, client) -> dict[str, int]:
    """Giudica i vicini di ogni task attivo non ancora esaminato, poi applica le fusioni. Ritorna i conteggi."""
    da_esaminare = [str(r[0]) for r in conn.execute(
        """SELECT t.task_id FROM canonical_tasks t
           WHERE t.status = 'active' AND t.granularity IN (1, 2)
             AND NOT EXISTS (SELECT 1 FROM fusioni_proposte f WHERE f.task_id = t.task_id)
           ORDER BY t.title_it"""
    ).fetchall()]
    titoli = {str(r[0]): r[1] for r in conn.execute("SELECT task_id, title_it FROM canonical_tasks").fetchall()}
    giudicati, falliti = 0, 0
    for task_id in da_esaminare:
        vicini = trova_vicini(conn, task_id)
        if not vicini:
            continue
        try:
            giudizi = giudica(client, titoli[task_id], vicini)
        except CanonicalizerError:
            falliti += 1
            continue
        registra_giudizi(conn, task_id, giudizi)
        giudicati += 1
    fusi = 0
    for gruppo in _gruppi_da_fondere(conn):
        if fondi(conn, gruppo):
            fusi += len(gruppo) - 1
    return {"task_giudicati": giudicati, "task_falliti": falliti, "task_fusi": fusi}
