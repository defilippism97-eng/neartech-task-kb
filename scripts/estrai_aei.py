"""Estrae dagli file dell'Anthropic Economic Index gli insight di uso per task (solo contesto).

Il collegamento a ONET_TASK avviene per testo esatto normalizzato (minuscole, spazi,
punto finale). Un testo che corrisponde a più task O*NET è ambiguo e non viene collegato.
Il valore è uso osservato: non entra in N come capacità (vedi config/mappe_scala.json).

Uso:
  python scripts/estrai_aei.py --penetration aei/task_penetration.csv \
      --onet31 "onet/Task Statements.txt" --out docs/ricerca/estratti/aei_task_penetration.jsonl
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

LICENZA = "MIT (dataset card Hugging Face Anthropic/EconomicIndex)"


def normalizza(testo: str) -> str:
    return re.sub(r"\s+", " ", testo).strip().lower().rstrip(".")


def indice_onet(righe_onet: list[dict]) -> dict[str, list[str]]:
    """Mappa il testo normalizzato al/i Task ID O*NET che lo contengono."""
    indice: dict[str, list[str]] = defaultdict(list)
    for r in righe_onet:
        indice[normalizza(r["Task"])].append(r["Task ID"])
    return indice


def record_aei(riga: dict, numero: int, indice: dict[str, list[str]]) -> dict:
    chiave = normalizza(riga["task"])
    ids = indice.get(chiave, [])
    if len(ids) == 1:
        link, relazione = f"ONET_TASK {ids[0]}", "exact"
    elif len(ids) > 1:
        link, relazione = None, "ambiguo: più task O*NET con lo stesso testo"
    else:
        link, relazione = None, "nessun collegamento"
    return {
        "id": f"AEI-{numero:06d}",
        "source": "Anthropic Economic Index, release labor_market_impacts/task_penetration.csv",
        "source_location": f"task_penetration.csv, riga {numero}",
        "observed_at": "da verificare (data di rilascio del file)",
        "variable": "uso_task_penetration",
        "value_raw": float(riga["penetration"]),
        "scale": "quota di conversazioni Claude che coprono il task (0-1)",
        "value_0_4": None,
        "evidence_type": "usage",
        "task_link": link,
        "relation": relazione,
        "n": None,
        "agreement": None,
        "use": "contesto",
        "dimension": "any",
        "quality": "bassa per la capacità: uso osservato, non successo",
        "licence": LICENZA,
        "notes": "Uso osservato non è capacità: non converte a score_0_4 per N.",
    }


def leggi_csv(percorso: Path) -> list[dict]:
    with percorso.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--penetration", type=Path, required=True)
    ap.add_argument("--onet31", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    onet = leggi_csv_tsv(args.onet31)
    indice = indice_onet(onet)
    righe = leggi_csv(args.penetration)
    records = [record_aei(r, i + 2, indice) for i, r in enumerate(righe)]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")

    esatti = sum(1 for r in records if r["relation"] == "exact")
    ambigui = sum(1 for r in records if r["relation"].startswith("ambiguo"))
    print(f"record {len(records)}: exact {esatti}, ambigui {ambigui}, senza collegamento {len(records) - esatti - ambigui}")


def leggi_csv_tsv(percorso: Path) -> list[dict]:
    with percorso.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


if __name__ == "__main__":
    main()
