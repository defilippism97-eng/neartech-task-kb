"""Report di audit unico di un'organizzazione (ADR 0004): JSON verificabile e versione Markdown.

Uso (DATABASE_URL dall'ambiente; l'utente è indicato dal soggetto SSO e deve avere leggere_audit):
  python scripts/report_audit.py --utente-sso S --org societa_dolce --uscita C:/audit/societa_dolce-2026-10-17
  python scripts/report_audit.py ... --ancora 23:277d2305...2d59

Scrive <uscita>.json e <uscita>.md fuori dal repository e non sovrascrive file esistenti. L'ancora (posizione:hash,
da docs/audit/ancore-registro.md) verifica che le righe del registro fino a quel punto non siano cambiate.
Il report contiene testo dell'organizzazione: va conservato fuori dal repository.
Sola lettura sui dati; il log di accesso usa una connessione dedicata.
"""

import argparse
import json
import os
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "src"))

from neartech.audit import report_in_markdown, report_organizzazione  # noqa: E402
from neartech.db import connect  # noqa: E402
from neartech.permessi import configura_log  # noqa: E402


def _ancora(testo: str | None) -> tuple[int, str] | None:
    if testo is None:
        return None
    posizione, _, valore = testo.partition(":")
    if not posizione.isdigit() or len(valore) != 64:
        raise SystemExit("ancora non valida: attesa posizione:hash (64 caratteri esadecimali)")
    return int(posizione), valore


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--utente-sso", required=True)
    parser.add_argument("--org", required=True, help="codice dell'organizzazione")
    parser.add_argument("--uscita", required=True, help="percorso senza estensione")
    parser.add_argument("--ancora")
    args = parser.parse_args()
    if os.environ.get("NEARTECH_DB_VIA", "").lower() == "https":
        raise SystemExit("questo script richiede la connessione diretta: il collegamento HTTPS non ha transazioni")
    ancora = _ancora(args.ancora)
    file_json, file_md = Path(f"{args.uscita}.json").resolve(), Path(f"{args.uscita}.md").resolve()
    if file_json.is_relative_to(RADICE):
        raise SystemExit("il report contiene testo dell'organizzazione: scriverlo fuori dal repository")
    for percorso in (file_json, file_md):
        if percorso.exists():
            raise SystemExit(f"il file {percorso} esiste già: scegliere un altro nome")

    with connect() as conn, connect() as conn_log:
        conn_log.autocommit = True
        configura_log(conn_log)
        try:
            conn.read_only = True
            utente = conn.execute("SELECT utente_id FROM utenti WHERE soggetto_sso = %s",
                                  (args.utente_sso,)).fetchone()
            org = conn.execute("SELECT org_id FROM organizations WHERE codice = %s", (args.org,)).fetchone()
            if utente is None or org is None:
                raise SystemExit("utente o organizzazione sconosciuti")
            report = report_organizzazione(conn, str(utente[0]), str(org[0]), ancora=ancora)
        except (LookupError, PermissionError) as errore:
            raise SystemExit(f"errore ({type(errore).__name__}): {errore}") from None
        finally:
            configura_log(None)

    # Entrambi i testi pronti prima di scrivere; "x" non sovrascrive un file comparso nel frattempo.
    testo_json, testo_md = json.dumps(report, ensure_ascii=False, indent=2), report_in_markdown(report)
    file_json.parent.mkdir(parents=True, exist_ok=True)
    with open(file_json, "x", encoding="utf-8") as uscita:
        uscita.write(testo_json)
    with open(file_md, "x", encoding="utf-8") as uscita:
        uscita.write(testo_md)
    i = report["integrita"]
    print(f"report scritto: {file_json} e {file_md}")
    print(f"catena: {i['catena']}; testi non corrispondenti: {len(i['testi'])}; "
          f"contenuti non corrispondenti: {len(i['contenuti'])}; atti: {len(report['atti'])}")


if __name__ == "__main__":
    main()
