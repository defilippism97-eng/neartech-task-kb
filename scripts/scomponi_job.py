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

ORG_CODICE = "societa_dolce"  # organizzazione del pilota; il testo va nel suo spazio
from neartech.scomposizione import (  # noqa: E402
    ScompostoError,
    attivita_da_record,
    carica_documenti,
    proponi_attivita,
    organizzazione_per_codice,
    salva_documento,
    titoli_attivi,
    verifica_attivita,
)


def carica_da_file(cartella: Path, file_proposte: Path) -> None:
    """Carica esattamente le attività del file approvato. Ogni passo viene ricontrollato sul documento."""
    docs, _ = carica_documenti(cartella)
    per_nome = {d.nome_file: d for d in docs}
    records = [json.loads(l) for l in file_proposte.read_text(encoding="utf-8").splitlines() if l.strip()]
    with connect() as conn:
        for i, rec in enumerate(records, start=1):
            doc = per_nome[rec["documento"]]
            attivita = verifica_attivita(attivita_da_record(rec), doc.testo)
            nuove = salva_documento(conn, doc, attivita, org_id=organizzazione_per_codice(conn, ORG_CODICE))
            print(f"[{i}/{len(records)}] {doc.ruolo}: {len(attivita)} attività, occorrenze nuove: {nuove}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--proposte", type=Path, help="scrive le proposte in JSON, per confrontarle con la revisione")
    ap.add_argument("--da-file", type=Path, help="carica le attività da un file di proposte approvato, senza chiamare il modello")
    args = ap.parse_args()

    if args.da_file:
        return carica_da_file(args.dir, args.da_file)

    api_key = os.environ.get("NEARTECH_ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("NEARTECH_ANTHROPIC_API_KEY non configurata")
    client = anthropic.Anthropic(api_key=api_key)

    docs, scartati = carica_documenti(args.dir)
    for nome in scartati:
        print(f"scartato (vuoto o senza titolo di posizione): {nome}", flush=True)
    print(f"documenti da elaborare: {len(docs)}", flush=True)

    falliti: list[str] = []
    with connect() as conn:
        for i, doc in enumerate(docs, start=1):
            titoli = titoli_attivi(conn) if not args.dry_run else []
            try:
                attivita = proponi_attivita(client, doc, titoli)
            except ScompostoError as err:
                # Un documento che fallisce non blocca gli altri: si rilancia lo script per riprovarlo.
                print(f"[{i}/{len(docs)}] ERRORE {doc.nome_file}: {err}", flush=True)
                falliti.append(doc.nome_file)
                continue
            print(f"[{i}/{len(docs)}] {doc.ruolo}: {len(attivita)} attività", flush=True)
            if args.proposte:
                with args.proposte.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"ruolo": doc.ruolo, "documento": doc.nome_file,
                                         "attivita": [a.model_dump() for a in attivita]}, ensure_ascii=False) + "\n")
            if args.dry_run:
                for a in attivita:
                    print(f"    g{a.granularita} {a.titolo}", flush=True)
                continue
            nuove = salva_documento(conn, doc, attivita, org_id=organizzazione_per_codice(conn, ORG_CODICE))
            print(f"    occorrenze nuove: {nuove}", flush=True)
    if falliti:
        raise SystemExit(f"documenti da rielaborare: {len(falliti)}: {falliti}")


if __name__ == "__main__":
    main()
