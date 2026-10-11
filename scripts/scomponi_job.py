"""Scompone le job description in task canonici e occorrenze, con Sonnet 5.5.

Uso (la chiave del modello è letta da NEARTECH_ANTHROPIC_API_KEY):
  DATABASE_URL=... [NEARTECH_DB_VIA=https] python scripts/scomponi_job.py --dir <cartella con i .docx> [--dry-run]

--dry-run stampa le proposte senza scrivere nel database: da usare per la revisione prima del caricamento.
Lo script si può rilanciare: documenti già caricati (stessa impronta) e occorrenze esistenti non cambiano.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.db import connect  # noqa: E402
from neartech.scomposizione import (  # noqa: E402
    carica_documenti,
    proponi_attivita,
    salva_documento,
    titoli_attivi,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--proposte", type=Path, help="scrive le proposte in JSON, per confrontarle con la revisione")
    args = ap.parse_args()

    api_key = os.environ.get("NEARTECH_ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("NEARTECH_ANTHROPIC_API_KEY non configurata")
    client = anthropic.Anthropic(api_key=api_key)

    docs, scartati = carica_documenti(args.dir)
    for nome in scartati:
        print(f"scartato (vuoto o senza titolo di posizione): {nome}", flush=True)
    print(f"documenti da elaborare: {len(docs)}", flush=True)

    with connect() as conn:
        for i, doc in enumerate(docs, start=1):
            titoli = titoli_attivi(conn) if not args.dry_run else []
            attivita = proponi_attivita(client, doc, titoli)
            print(f"[{i}/{len(docs)}] {doc.ruolo}: {len(attivita)} attività", flush=True)
            if args.proposte:
                with args.proposte.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"ruolo": doc.ruolo, "documento": doc.nome_file,
                                         "attivita": [a.model_dump() for a in attivita]}, ensure_ascii=False) + "\n")
            if args.dry_run:
                for a in attivita:
                    print(f"    g{a.granularita} {a.titolo}", flush=True)
                continue
            nuove = salva_documento(conn, doc, attivita)
            print(f"    occorrenze nuove: {nuove}", flush=True)


if __name__ == "__main__":
    main()
