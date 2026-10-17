"""Fase 4: snapshot di capacità di riserva e calcolo deterministico di N e D (metodo, sezione 17).

Uso (DATABASE_URL dall'ambiente; l'utente è indicato dal soggetto SSO). Nessuna chiamata all'API.
  python scripts/calcola.py snapshot-riserva --utente-sso S --data 2026-10-17 --emivita 180 --motivazione "..."
  python scripts/calcola.py pubblica-snapshot --utente-sso S --snapshot ID --nota "..."
  python scripts/calcola.py calcola --utente-sso S --org CODICE --seme 20261017 [--estrazioni 2000]

Lo snapshot nasce proposto e lo pubblica chi approva gli snapshot (atto con nota esplicativa). Il calcolo usa
la rubrica corrente approvata, il profilo di pesi attivo e approvato dell'organizzazione (o quello comune) e lo
snapshot pubblicato; senza uno di questi si ferma. Tutti e tre i comandi scrivono nel database.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.calcolo import ESTRAZIONI, calcola_organizzazione  # noqa: E402
from neartech.capacita import proponi_snapshot_riserva, pubblica_snapshot  # noqa: E402
from neartech.db import connect  # noqa: E402
from neartech.permessi import configura_log  # noqa: E402
from neartech.scomposizione import organizzazione_per_codice  # noqa: E402


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    comandi = ap.add_subparsers(dest="comando", required=True)
    s = comandi.add_parser("snapshot-riserva")
    s.add_argument("--data", required=True)
    s.add_argument("--emivita", type=int, required=True, help="giorni in cui il peso di un'evidenza si dimezza")
    s.add_argument("--motivazione", required=True)
    p = comandi.add_parser("pubblica-snapshot")
    p.add_argument("--snapshot", required=True)
    p.add_argument("--nota", required=True)
    c = comandi.add_parser("calcola")
    c.add_argument("--org", required=True)
    c.add_argument("--seme", type=int, required=True)
    c.add_argument("--estrazioni", type=int, default=ESTRAZIONI)
    for sotto in (s, p, c):
        sotto.add_argument("--utente-sso", required=True)
    return ap


def main() -> None:
    args = parser().parse_args()
    if os.environ.get("NEARTECH_DB_VIA", "").lower() == "https":
        raise SystemExit("questo script richiede la connessione diretta: il collegamento HTTPS non ha transazioni")
    with connect() as conn, connect() as conn_log:
        conn_log.autocommit = True
        configura_log(conn_log)
        try:
            riga = conn.execute("SELECT utente_id FROM utenti WHERE soggetto_sso = %s", (args.utente_sso,)).fetchone()
            if riga is None:
                raise SystemExit("utente sconosciuto")
            utente = str(riga[0])
            if args.comando == "snapshot-riserva":
                snapshot = proponi_snapshot_riserva(conn, utente, as_of=args.data, emivita_giorni=args.emivita,
                                                    motivazione=args.motivazione)
                print(f"snapshot proposto: {snapshot}")
            elif args.comando == "pubblica-snapshot":
                atto = pubblica_snapshot(conn, utente, args.snapshot, nota=args.nota)
                print(f"snapshot pubblicato, atto {atto}")
            else:
                esito = calcola_organizzazione(conn, utente, organizzazione_per_codice(conn, args.org),
                                               seme=args.seme, estrazioni=args.estrazioni)
                print(f"occorrenze {esito['occorrenze']}, risultati nuovi {esito['nuove']}, "
                      f"senza N {esito['senza_n']}, senza D {esito['senza_d']}")
        except (LookupError, ValueError, PermissionError) as errore:
            raise SystemExit(f"errore ({type(errore).__name__}): {errore}") from None
        finally:
            configura_log(None)


if __name__ == "__main__":
    main()
