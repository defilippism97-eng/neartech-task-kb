"""Scompone le job description in task canonici e occorrenze, con Sonnet 5.5.

Uso (la chiave del modello è letta da NEARTECH_ANTHROPIC_API_KEY):
  DATABASE_URL=... python scripts/scomponi_job.py --dir <cartella con i .docx> \\
      --org <codice organizzazione> --utente-sso <soggetto SSO> [--dry-run]

--org indica l'organizzazione dei documenti: il testo va nel suo spazio. --utente-sso è chi carica:
serve gestire_dataset_centrale (verificato prima di chiamare il modello), e ogni documento caricato
lascia un atto nel registro (neartech.scomposizione.carica_documento).
Il caricamento richiede la connessione diretta: con NEARTECH_DB_VIA=https ogni istruzione è una
transazione a sé, e l'atto non troverebbe il suo testo nello spazio (controllo differito, migrazione 0025).
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
from neartech.db_https import HttpConnection  # noqa: E402
from neartech.permessi import richiedi  # noqa: E402
from neartech.scomposizione import (  # noqa: E402
    ScompostoError,
    attivita_da_record,
    carica_documenti,
    carica_documento,
    proponi_attivita,
    organizzazione_per_codice,
    titoli_attivi,
    verifica_attivita,
)


def _utente_autorizzato(conn, soggetto_sso: str, org_id: str) -> str:
    """Utente che carica, con il permesso verificato subito: prima di chiamare il modello o scrivere."""
    riga = conn.execute("SELECT utente_id FROM utenti WHERE soggetto_sso = %s", (soggetto_sso,)).fetchone()
    if riga is None:
        raise SystemExit("utente sconosciuto")
    utente_id = str(riga[0])
    if isinstance(conn, HttpConnection):
        raise SystemExit("il caricamento richiede la connessione diretta, non NEARTECH_DB_VIA=https")
    richiedi(conn, utente_id, "gestire_dataset_centrale", org_id, risorsa="caricamento_documenti")
    return utente_id


def carica_da_file(cartella: Path, file_proposte: Path, codice_org: str, soggetto_sso: str) -> None:
    """Carica esattamente le attività del file approvato. Ogni passo viene ricontrollato sul documento."""
    docs, _ = carica_documenti(cartella)
    per_nome = {d.nome_file: d for d in docs}
    records = [json.loads(l) for l in file_proposte.read_text(encoding="utf-8").splitlines() if l.strip()]
    with connect() as conn:
        org_id = organizzazione_per_codice(conn, codice_org)
        utente_id = _utente_autorizzato(conn, soggetto_sso, org_id)
        for i, rec in enumerate(records, start=1):
            doc = per_nome[rec["documento"]]
            attivita = verifica_attivita(attivita_da_record(rec), doc.testo)
            nuove = carica_documento(conn, utente_id, doc, attivita, org_id=org_id, modalita="da_file",
                                     motivazione=f"caricamento dal file di proposte approvato {file_proposte.name}")
            conn.commit()
            print(f"[{i}/{len(records)}] {doc.ruolo}: {len(attivita)} attività, occorrenze nuove: {nuove}", flush=True)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--org", required=True, help="codice dell'organizzazione dei documenti")
    ap.add_argument("--utente-sso", help="soggetto SSO di chi carica (obbligatorio se si scrive nel database)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--proposte", type=Path, help="scrive le proposte in JSON, per confrontarle con la revisione")
    ap.add_argument("--da-file", type=Path, help="carica le attività da un file di proposte approvato, senza chiamare il modello")
    return ap


def main() -> None:
    ap = parser()
    args = ap.parse_args()
    if not args.dry_run and not args.utente_sso:
        ap.error("--utente-sso è obbligatorio, salvo con --dry-run")

    if args.da_file:
        return carica_da_file(args.dir, args.da_file, args.org, args.utente_sso)

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
        org_id = organizzazione_per_codice(conn, args.org)
        utente_id = None if args.dry_run else _utente_autorizzato(conn, args.utente_sso, org_id)
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
            nuove = carica_documento(conn, utente_id, doc, attivita, org_id=org_id, modalita="modello",
                                     motivazione="caricamento delle attività proposte dal modello")
            conn.commit()
            print(f"    occorrenze nuove: {nuove}", flush=True)
    if falliti:
        raise SystemExit(f"documenti da rielaborare: {len(falliti)}: {falliti}")


if __name__ == "__main__":
    main()
