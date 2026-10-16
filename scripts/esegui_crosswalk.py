"""Esegue il Crosswalk Mapper sui task canonici attivi che non hanno ancora relazioni.

Uso (la chiave del modello è letta da NEARTECH_ANTHROPIC_API_KEY):
  DATABASE_URL=... [NEARTECH_DB_VIA=https] python scripts/esegui_crosswalk.py

Passi:
1. calcola l'embedding bge-m3 dei task canonici che non ce l'hanno;
2. per ogni task senza relazioni, esegue il mapper su ciascuno schema (vedi crosswalk.py).
Lo script si può rilanciare: i task già mappati vengono saltati, e le relazioni esistenti non cambiano.
"""

import os
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.crosswalk import EMBEDDING_MODEL, CrosswalkError, map_task  # noqa: E402
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
    model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    vecs = model.encode([r[1] for r in missing], batch_size=64, normalize_embeddings=True)
    for (task_id, _title), vec in zip(missing, vecs):
        conn.execute(
            "INSERT INTO task_embeddings (task_id, model_name, vec) VALUES (%s, %s, %s::vector)",
            (task_id, EMBEDDING_MODEL, "[" + ",".join(f"{x:.6f}" for x in vec) + "]"),
        )
    return len(missing)


def main() -> None:
    api_key = os.environ.get("NEARTECH_ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("NEARTECH_ANTHROPIC_API_KEY non configurata")
    client = anthropic.Anthropic(api_key=api_key)

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
