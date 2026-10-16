"""Stima preliminare (llm_prior) dei punteggi di N per le attività O*NET di staff.

Ogni attività è valutata su k1, k2, k3 e r con 5 campioni indipendenti (SAMPLES_PER_ITEM dello Scorer).
Il risultato va in un JSONL con i campioni grezzi: l'aggregazione è un passo successivo.
Riprende da dove si era fermato: le attività già presenti nel file in uscita non vengono rifatte.

Uso (chiave in NEARTECH_ANTHROPIC_API_KEY):
  python scripts/stima_prior_n.py --tasks docs/ricerca/staff_tasks.jsonl \
      --rubric config/rubrica_n_bozza.json --out docs/ricerca/estratti/llm-prior-staff.jsonl
"""

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic

from neartech.scorer import MODEL_ID, SAMPLES_PER_ITEM, ScoringError, score_item


def rubric_text(rubric: dict, item: str) -> str:
    ancore = rubric["items"][item]["ancore"]
    return "\n".join(f"{liv}: {testo}" for liv, testo in sorted(ancore.items()))


def stima_task(client, task: dict, rubric: dict, campioni: int, voci=("k1", "k2", "k3", "r")) -> dict:
    punteggi, errori = {}, {}
    for item in voci:
        try:
            risultati = score_item(client, task_title=task["text"], item=item,
                                   rubric_text=rubric_text(rubric, item), n_samples=campioni)
            punteggi[item] = [x.value for x in risultati]
        except ScoringError as err:
            errori[item] = str(err)
    return {"task_id": task["task_id"], "soc": task["soc"], "title": task["text"],
            "modello": MODEL_ID, "rubrica": rubric["versione"], "campioni": campioni, "punteggi": punteggi,
            "errori": errori, "stato": "preliminare, non calibrato"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, required=True)
    ap.add_argument("--rubric", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--campioni", type=int, default=SAMPLES_PER_ITEM)
    ap.add_argument("--voci", default="k1,k2,k3,r")
    args = ap.parse_args()

    tasks = [json.loads(l) for l in args.tasks.read_text(encoding="utf-8").splitlines()]
    if args.limit:
        tasks = tasks[: args.limit]
    rubric = json.loads(args.rubric.read_text(encoding="utf-8"))
    fatti = set()
    if args.out.exists():
        fatti = {json.loads(l)["task_id"] for l in args.out.read_text(encoding="utf-8").splitlines() if l.strip()}
    da_fare = [t for t in tasks if t["task_id"] not in fatti]
    print(f"attività totali {len(tasks)}, già fatte {len(fatti)}, da fare {len(da_fare)}", flush=True)

    client = anthropic.Anthropic(api_key=os.environ["NEARTECH_ANTHROPIC_API_KEY"], timeout=60.0, max_retries=3)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a", encoding="utf-8") as fh, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futuri = [pool.submit(stima_task, client, t, rubric, args.campioni, tuple(args.voci.split(","))) for t in da_fare]
        for n, f in enumerate(as_completed(futuri), 1):
            fh.write(json.dumps(f.result(), ensure_ascii=False) + "\n")
            fh.flush()
            if n % 100 == 0:
                print(f"completate {n}/{len(da_fare)}", flush=True)
    print("fatto", flush=True)


if __name__ == "__main__":
    main()
