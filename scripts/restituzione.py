"""Restituzione dei risultati a un'organizzazione (fase 5; registro di metodo, sezione 24).

Uso (DATABASE_URL dall'ambiente; l'utente è indicato dal soggetto SSO):
  python scripts/restituzione.py scrivi --utente-sso S --org CODICE --uscita C:/restituzioni/CODICE-2026-10-17
  python scripts/restituzione.py approva --utente-sso S --org CODICE --file C:/restituzioni/CODICE-2026-10-17.json \
      --motivazione "..."

scrivi: sola lettura (serve leggere); scrive <uscita>.md e <uscita>.json fuori dal repository e non sovrascrive
file esistenti. La restituzione contiene testo dell'organizzazione: va conservata fuori dal repository.
approva: scrive nel registro l'atto di approvazione del comitato guida (serve approvare_restituzione) sulla
restituzione letta dal file JSON; se i risultati sono cambiati dopo la lettura, la restituzione è superata.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "src"))

from neartech.db import connect  # noqa: E402
from neartech.permessi import configura_log  # noqa: E402
from neartech.restituzione import (  # noqa: E402
    approva_restituzione,
    restituzione_in_markdown,
    restituzione_organizzazione,
)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    comandi = ap.add_subparsers(dest="comando", required=True)
    s = comandi.add_parser("scrivi")
    s.add_argument("--uscita", required=True, help="percorso senza estensione, fuori dal repository")
    a = comandi.add_parser("approva")
    a.add_argument("--file", required=True, help="restituzione JSON scritta da 'scrivi'")
    a.add_argument("--motivazione", required=True)
    for sotto in (s, a):
        sotto.add_argument("--utente-sso", required=True)
        sotto.add_argument("--org", required=True, help="codice dell'organizzazione")
    return ap


def file_di_uscita(uscita: str, radice: Path = RADICE) -> tuple[Path, Path]:
    """Percorsi del Markdown e del JSON: fuori dal repository, non ancora esistenti, cartella creata."""
    file_md, file_json = Path(f"{uscita}.md").resolve(), Path(f"{uscita}.json").resolve()
    if file_json.is_relative_to(radice):
        raise SystemExit("la restituzione contiene testo dell'organizzazione: scriverla fuori dal repository")
    for percorso in (file_md, file_json):
        if percorso.exists():
            raise SystemExit(f"il file {percorso} esiste già: scegliere un altro nome")
    file_json.parent.mkdir(parents=True, exist_ok=True)
    return file_md, file_json


def scrivi_file(file_md: Path, testo_md: str, file_json: Path, testo_json: str) -> None:
    """Prima il Markdown, poi il JSON (quello che si approva): un errore non lascia un JSON senza il suo
    Markdown, e i file creati si tolgono. Creazione esclusiva, letture solo per il proprietario dove il
    sistema lo consente, a capo uguali su ogni sistema."""
    creati = []
    try:
        for percorso, testo in ((file_md, testo_md), (file_json, testo_json)):
            descrittore = os.open(percorso, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            creati.append(percorso)
            with open(descrittore, "w", encoding="utf-8", newline="\n") as uscita:
                uscita.write(testo)
    except BaseException:
        for percorso in creati:
            percorso.unlink(missing_ok=True)
        raise


def leggi_restituzione(percorso: str) -> dict:
    try:
        with open(percorso, encoding="utf-8") as ingresso:
            letta = json.load(ingresso)
    except (OSError, ValueError) as errore:  # ValueError comprende JSON e codifica non validi
        raise SystemExit(f"restituzione non leggibile: {errore}") from None
    if not isinstance(letta, dict):
        raise SystemExit("restituzione non valida: atteso un oggetto JSON")
    return letta


def main() -> None:
    args = parser().parse_args()
    if os.environ.get("NEARTECH_DB_VIA", "").lower() == "https":
        raise SystemExit("questo script richiede la connessione diretta: il collegamento HTTPS non ha transazioni")
    if args.comando == "scrivi":
        file_md, file_json = file_di_uscita(args.uscita)
    else:
        letta = leggi_restituzione(args.file)

    atto = None
    try:
        with connect() as conn, connect() as conn_log:
            conn_log.autocommit = True
            configura_log(conn_log)
            try:
                conn.read_only = args.comando == "scrivi"
                utente = conn.execute("SELECT utente_id FROM utenti WHERE soggetto_sso = %s",
                                      (args.utente_sso,)).fetchone()
                org = conn.execute("SELECT org_id FROM organizations WHERE codice = %s", (args.org,)).fetchone()
                if utente is None or org is None:
                    raise SystemExit("utente o organizzazione sconosciuti")
                if args.comando == "approva":
                    atto = approva_restituzione(conn, str(utente[0]), str(org[0]), letta,
                                                motivazione=args.motivazione)
                else:
                    restituzione = restituzione_organizzazione(conn, str(utente[0]), str(org[0]))
            finally:
                configura_log(None)
        # Uscendo dal blocco la transazione è confermata.
    except (LookupError, ValueError, PermissionError, RuntimeError, psycopg.Error) as errore:
        raise SystemExit(f"errore ({type(errore).__name__}): {errore}") from None

    if args.comando == "approva":
        print(f"restituzione {letta['impronta']} approvata, atto {atto}")
        return
    try:
        scrivi_file(file_md, restituzione_in_markdown(restituzione),
                    file_json, json.dumps(restituzione, ensure_ascii=False, indent=2))
    except OSError as errore:
        raise SystemExit(f"restituzione non scritta: {errore}") from None
    q = restituzione["riepilogo"]
    print(f"restituzione scritta: {file_md} e {file_json}")
    print(f"impronta {restituzione['impronta']}; occorrenze {q['occorrenze']}, con risultato {q['con_risultato']}, "
          f"quadranti {q['quadranti']}, instabili {q['instabili']}; avvertenze {', '.join(restituzione['avvertenze'])}")


if __name__ == "__main__":
    main()
