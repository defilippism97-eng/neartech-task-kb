"""Campioni di revisione e metrica di precisione (fase 2).

Uso (l'utente è indicato dal soggetto SSO; DATABASE_URL dall'ambiente):
  python scripts/metrica.py anteprima --tipo fusione --filtro decisione=stessa_attivita
  python scripts/metrica.py crea-campione --utente-sso S --org ORG --tipo fusione --filtro decisione=stessa_attivita \
      --criterio tutte --istruzioni istruzioni-fusioni-v1 --motivazione "..."
  python scripts/metrica.py crea-campione ... --criterio casuale --dimensione 60 --seme 20261016
  python scripts/metrica.py esporta --utente-sso S --campione C --file campione.jsonl
  python scripts/metrica.py importa-giudizi --utente-sso S --campione C --file giudizi.jsonl --istruzioni v1
  python scripts/metrica.py importa-crosswalk --utente-sso S --org ORG --campione crosswalk-2026-10-11
  python scripts/metrica.py calcola --utente-sso S --campione C

'anteprima' è in sola lettura. Gli altri comandi scrivono: su produzione richiedono
l'approvazione del responsabile del progetto. Il file dei giudizi ha una riga JSON per
elemento: {"posizione": 1, "esito": "corretto|parziale|errato", "nota": "..."}.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.campioni import (  # noqa: E402
    _popolazione,
    crea_campione,
    esporta_campione,
    importa_revisioni_crosswalk,
    registra_giudizio,
)
from neartech.db import connect  # noqa: E402
from neartech.metrica import calcola_precisione  # noqa: E402


def _filtro(coppie: list[str]) -> dict[str, str]:
    filtro = {}
    for coppia in coppie or []:
        chiave, _, valore = coppia.partition("=")
        if not chiave or not valore:
            raise SystemExit(f"filtro non valido: {coppia!r} (atteso chiave=valore)")
        filtro[chiave] = valore
    return filtro


def _utente(conn, soggetto_sso: str) -> str:
    riga = conn.execute("SELECT utente_id FROM utenti WHERE soggetto_sso = %s", (soggetto_sso,)).fetchone()
    if riga is None:
        raise SystemExit("utente sconosciuto")
    return str(riga[0])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    comandi = parser.add_subparsers(dest="comando", required=True)

    anteprima = comandi.add_parser("anteprima")
    anteprima.add_argument("--tipo", required=True, choices=["fusione", "crosswalk"])
    anteprima.add_argument("--filtro", nargs="*")

    crea = comandi.add_parser("crea-campione")
    for nome in ("--utente-sso", "--org", "--istruzioni", "--motivazione"):
        crea.add_argument(nome, required=True)
    crea.add_argument("--tipo", required=True, choices=["fusione", "crosswalk"])
    crea.add_argument("--filtro", nargs="*")
    crea.add_argument("--criterio", required=True, choices=["tutte", "casuale"])
    crea.add_argument("--dimensione", type=int)
    crea.add_argument("--seme", type=int)

    esporta = comandi.add_parser("esporta")
    for nome in ("--utente-sso", "--campione", "--file"):
        esporta.add_argument(nome, required=True)

    importa = comandi.add_parser("importa-giudizi")
    for nome in ("--utente-sso", "--campione", "--file", "--istruzioni"):
        importa.add_argument(nome, required=True)

    crosswalk = comandi.add_parser("importa-crosswalk")
    for nome in ("--utente-sso", "--org", "--campione"):
        crosswalk.add_argument(nome, required=True)

    calcola = comandi.add_parser("calcola")
    for nome in ("--utente-sso", "--campione"):
        calcola.add_argument(nome, required=True)

    args = parser.parse_args()
    with connect() as conn:
        if args.comando == "anteprima":
            conn.read_only = True
            print(f"proposte nella popolazione: {len(_popolazione(conn, args.tipo, _filtro(args.filtro)))}")
            return
        utente = _utente(conn, args.utente_sso)
        if args.comando == "crea-campione":
            campione = crea_campione(
                conn, utente, org_id=args.org, tipo=args.tipo, filtro=_filtro(args.filtro), criterio=args.criterio,
                versione_istruzioni=args.istruzioni, motivazione=args.motivazione,
                dimensione=args.dimensione, seme=args.seme,
            )
            print(f"campione creato: {campione}")
        elif args.comando == "esporta":
            righe = esporta_campione(conn, utente, args.campione)
            Path(args.file).write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in righe), encoding="utf-8"
            )
            print(f"elementi esportati: {len(righe)}")
        elif args.comando == "importa-giudizi":
            righe = [json.loads(r) for r in Path(args.file).read_text(encoding="utf-8").splitlines() if r.strip()]
            with conn.transaction():
                for riga in righe:
                    registra_giudizio(conn, utente, args.campione, int(riga["posizione"]), riga["esito"],
                                      nota=riga.get("nota"), versione_istruzioni=args.istruzioni)
            print(f"giudizi registrati: {len(righe)}")
        elif args.comando == "importa-crosswalk":
            campione = importa_revisioni_crosswalk(conn, utente, org_id=args.org, campione=args.campione)
            print(f"campione importato: {campione}")
        else:
            misura = calcola_precisione(conn, utente, args.campione)
            print(f"precisione {misura.precisione:.3f} (intervallo {misura.intervallo[0]:.3f}-"
                  f"{misura.intervallo[1]:.3f}), {misura.esito}; corretti {misura.n_corretti}, "
                  f"parziali {misura.n_parziali}, errati {misura.n_errati}; misura {misura.misura_id}")
        conn.commit()


if __name__ == "__main__":
    main()
