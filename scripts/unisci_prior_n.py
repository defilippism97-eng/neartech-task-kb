"""Unisce la classificazione di N in un unico file, con la versione della rubrica per ciascuna voce.

- attività già classificate con la v1: k1 e k3 restano v1 (ancore invariate); k2 e r vengono
  dal ricalcolo con la v2;
- attività nuove: tutte le voci con la v2.
Nessuna voce viene ricalcolata o corretta algebricamente.
"""

import json
from pathlib import Path

ESTRATTI = Path("docs/ricerca/estratti")
VERSIONE_PER_VOCE_V1 = {"k1": "bozza-1", "k2": "bozza-1", "k3": "bozza-1", "r": "bozza-1"}
VERSIONE_PER_VOCE_V2 = {"k1": "bozza-2", "k2": "bozza-2", "k3": "bozza-2", "r": "bozza-2"}


def leggi(p: Path) -> dict:
    return {json.loads(l)["task_id"]: json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}


def main() -> None:
    v1 = leggi(ESTRATTI / "llm-prior-staff.jsonl")
    ric = leggi(ESTRATTI / "ricalcolo_k2_r_v2.jsonl")
    nuovi = leggi(ESTRATTI / "nuovi_v2.jsonl")
    out = []
    for tid, r in v1.items():
        if tid not in ric:
            continue
        r2 = ric[tid]
        punteggi = {"k1": r["punteggi"].get("k1", []), "k3": r["punteggi"].get("k3", []),
                    "k2": r2["punteggi"].get("k2", []), "r": r2["punteggi"].get("r", [])}
        errori = {**{k: v for k, v in r["errori"].items() if k in ("k1", "k3")},
                  **{k: v for k, v in r2["errori"].items() if k in ("k2", "r")}}
        out.append({"task_id": tid, "soc": r["soc"], "title": r["title"], "modello": r["modello"],
                    "rubrica_per_voce": {"k1": "bozza-1", "k2": "bozza-2", "k3": "bozza-1", "r": "bozza-2"},
                    "campioni_per_voce": {k: len(v) for k, v in punteggi.items()},
                    "punteggi": punteggi, "errori": errori, "stato": "preliminare, non calibrato"})
    for tid, r in nuovi.items():
        out.append({"task_id": tid, "soc": r["soc"], "title": r["title"], "modello": r["modello"],
                    "rubrica_per_voce": VERSIONE_PER_VOCE_V2,
                    "campioni_per_voce": {k: len(v) for k, v in r["punteggi"].items()},
                    "punteggi": r["punteggi"], "errori": r["errori"], "stato": "preliminare, non calibrato"})
    dest = ESTRATTI / "llm-prior-staff-finale.jsonl"
    dest.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out), encoding="utf-8")
    con_errori = sum(1 for x in out if x["errori"])
    print(f"record uniti: {len(out)} (da v1 ricalcolati: {len(v1.keys() & ric.keys())}, nuovi: {len(nuovi)}), con errori: {con_errori}")


if __name__ == "__main__":
    main()
