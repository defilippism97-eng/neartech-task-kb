"""Esegue il Crosswalk Mapper sui task canonici attivi che non hanno ancora relazioni.

Uso (la chiave del modello è letta da NEARTECH_ANTHROPIC_API_KEY):
  DATABASE_URL=... [NEARTECH_DB_VIA=https] python scripts/esegui_crosswalk.py
  DATABASE_URL=... python scripts/esegui_crosswalk.py --solo-separati

--solo-separati: solo i task separati da una fusione sbagliata (atti 'correzione' con operazione
'scissione', crosswalk da rifare) e, per ciascuno, solo gli schemi senza giudizio registrato.
--limite-uscita N: si ferma prima della chiamata successiva quando i token in uscita superano N
(il limite approvato dal responsabile); stampa sempre il consumo.

Passi:
1. calcola l'embedding bge-m3 dei task canonici che non ce l'hanno;
2. per ogni task senza relazioni, esegue il mapper su ciascuno schema (vedi crosswalk.py).
Lo script si può rilanciare: i task già mappati vengono saltati, e le relazioni esistenti non cambiano.
"""

import argparse
import os
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.crosswalk import (  # noqa: E402
    CANDIDATE_SCHEMES,
    EMBEDDING_MODEL,
    EMBEDDING_REVISION,
    CrosswalkError,
    find_candidates,
    judge,
    map_task,
    registra_giudizio,
    save_judgements,
)
from neartech.db import connect  # noqa: E402


def _embed_missing_tasks(conn) -> int:
    from sentence_transformers import SentenceTransformer

    missing = conn.execute(
        """
        SELECT t.task_id, t.title_it FROM canonical_tasks t
        WHERE t.status = 'active' AND t.granularity <> 3
          AND NOT EXISTS (SELECT 1 FROM task_embeddings e
                          WHERE e.task_id = t.task_id AND e.model_name = %s)
        """,
        (EMBEDDING_MODEL,),
    ).fetchall()
    if not missing:
        return 0
    model = SentenceTransformer(EMBEDDING_MODEL, revision=EMBEDDING_REVISION, device="cpu")
    vecs = model.encode([r[1] for r in missing], batch_size=64, normalize_embeddings=True)
    for (task_id, _title), vec in zip(missing, vecs):
        conn.execute(
            "INSERT INTO task_embeddings (task_id, model_name, vec) VALUES (%s, %s, %s::vector)",
            (task_id, EMBEDDING_MODEL, "[" + ",".join(f"{x:.6f}" for x in vec) + "]"),
        )
    return len(missing)


class _ClienteConConsumo:
    """Conta i token di ogni chiamata, tentativi ripetuti compresi."""

    def __init__(self, client):
        self._client = client
        self.chiamate = self.ingresso = self.uscita = 0
        self.messages = self

    def create(self, **kwargs):
        risposta = self._client.messages.create(**kwargs)
        self.chiamate += 1
        self.ingresso += risposta.usage.input_tokens
        self.uscita += risposta.usage.output_tokens
        return risposta


def _separati(conn, client: _ClienteConConsumo, limite_uscita: int | None) -> None:
    """Crosswalk dei task separati, schema per schema, saltando quelli già giudicati."""
    todo = conn.execute(
        """SELECT DISTINCT t.task_id, t.title_it FROM canonical_tasks t
           JOIN registro_decisioni r ON r.oggetto_id = t.task_id::text AND r.tipo_oggetto = 'task_canonico'
            AND r.atto = 'correzione' AND r.dettagli ->> 'operazione' = 'scissione'
           WHERE t.status = 'active' ORDER BY t.title_it"""
    ).fetchall()
    print(f"task separati: {len(todo)}", flush=True)
    falliti = 0
    for i, (task_id, title) in enumerate(todo, start=1):
        for scheme in CANDIDATE_SCHEMES:
            if conn.execute("SELECT EXISTS (SELECT 1 FROM crosswalk_giudizi WHERE task_id = %s AND scheme = %s)",
                            (task_id, scheme)).fetchone()[0]:
                continue
            if limite_uscita is not None and client.uscita >= limite_uscita:
                print(f"limite di {limite_uscita} token in uscita raggiunto: mi fermo", flush=True)
                falliti += 1
                break
            try:
                judgements = judge(client, title, find_candidates(conn, str(task_id), scheme))
            except CrosswalkError as err:
                print(f"[{i}/{len(todo)}] {scheme} ERRORE: {err}", flush=True)
                falliti += 1
                continue
            with conn.transaction():
                salvate = save_judgements(conn, str(task_id), judgements)
                registra_giudizio(conn, str(task_id), scheme, len(judgements))
            print(f"[{i}/{len(todo)}] {scheme}: {salvate} relazioni", flush=True)
    print(f"consumo: {client.chiamate} chiamate, {client.ingresso} token in ingresso, {client.uscita} in uscita",
          flush=True)
    if falliti:
        raise SystemExit(f"schemi da rielaborare: {falliti}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--solo-separati", action="store_true")
    parser.add_argument("--limite-uscita", type=int)
    args = parser.parse_args()
    api_key = os.environ.get("NEARTECH_ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("NEARTECH_ANTHROPIC_API_KEY non configurata")
    client = anthropic.Anthropic(api_key=api_key)

    if args.solo_separati:
        with connect() as conn:
            conn.autocommit = True  # ogni schema giudicato si conferma da sé: un errore dopo non lo annulla
            _separati(conn, _ClienteConConsumo(client), args.limite_uscita)
        return

    with connect() as conn:
        embedded = _embed_missing_tasks(conn)
        print(f"embedding calcolati per {embedded} task", flush=True)
        todo = conn.execute(
            """
            SELECT t.task_id, t.title_it FROM canonical_tasks t
            WHERE t.status = 'active' AND t.granularity <> 3
              AND NOT EXISTS (SELECT 1 FROM task_mappings m WHERE m.task_id = t.task_id)
            ORDER BY t.title_it
            """
        ).fetchall()
        print(f"task da mappare: {len(todo)}", flush=True)
        falliti: list[str] = []
        for i, (task_id, title) in enumerate(todo, start=1):
            try:
                saved = map_task(conn, client, str(task_id), title)
            except CrosswalkError as err:
                # Un task che fallisce non blocca gli altri: rilanciando lo script viene ripreso.
                print(f"[{i}/{len(todo)}] ERRORE {title}: {err}", flush=True)
                falliti.append(title)
                continue
            print(f"[{i}/{len(todo)}] {title}: {saved} relazioni", flush=True)
    if falliti:
        raise SystemExit(f"task da rielaborare: {len(falliti)}")


if __name__ == "__main__":
    main()
