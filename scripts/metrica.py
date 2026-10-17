"""Campioni di revisione e metrica di precisione (fase 2).

Uso (l'utente è indicato dal soggetto SSO; DATABASE_URL dall'ambiente):
  python scripts/metrica.py anteprima --tipo fusione --filtro decisione=stessa_attivita
  python scripts/metrica.py crea-campione --utente-sso S --org ORG --tipo fusione --filtro decisione=stessa_attivita \
      --criterio tutte --istruzioni istruzioni-fusioni-v1 --motivazione "..."
  python scripts/metrica.py crea-campione ... --criterio casuale --dimensione 60 --seme 20261016
  python scripts/metrica.py esporta --utente-sso S --campione C --file campione.csv
  python scripts/metrica.py importa-giudizi --utente-sso S --campione C --file campione.csv --istruzioni v1
  python scripts/metrica.py importa-crosswalk --utente-sso S --org ORG --campione crosswalk-2026-10-11 \
      --popolazione-originale 6520
  python scripts/metrica.py calcola --utente-sso S --campione C

'anteprima' è in sola lettura. Gli altri comandi scrivono: su produzione richiedono
l'approvazione del responsabile del progetto. Il file dei giudizi ha una riga JSON per
elemento: {"posizione": 1, "esito": "corretto|parziale|errato", "nota": "..."}.
Con estensione .csv esportazione e importazione usano un CSV separato da punto e virgola
(si apre in Excel): si compilano le colonne "esito" e "nota" e si reimporta lo stesso file;
le righe con "esito" vuoto si saltano.
Serve la connessione diretta: il collegamento HTTPS (NEARTECH_DB_VIA=https) non ha transazioni.
Il log di accesso usa una connessione dedicata, così i rifiuti restano anche se l'operazione fallisce.
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.campioni import (  # noqa: E402
    crea_campione,
    esporta_campione,
    importa_revisioni_crosswalk,
    popolazione,
    registra_giudizio,
)
from neartech.db import connect  # noqa: E402
from neartech.metrica import calcola_precisione  # noqa: E402
from neartech.permessi import configura_log  # noqa: E402


def _filtro(coppie: list[str]) -> dict[str, str]:
    filtro = {}
    for coppia in coppie or []:
        chiave, _, valore = coppia.partition("=")
        if not chiave or not valore:
            raise SystemExit(f"filtro non valido: {coppia!r} (atteso chiave=valore)")
        filtro[chiave] = valore
    return filtro


def _cella_csv(valore):
    """Un titolo che inizia con = + - @ Excel lo esegue come formula: si apre con un apostrofo."""
    if isinstance(valore, str) and valore[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + valore
    return valore


def _scrivi_esportazione(percorso: Path, righe: list[dict]) -> None:
    # "x": non si sovrascrive un file esistente, nemmeno uno comparso dopo il controllo.
    if percorso.suffix.lower() == ".csv":
        colonne = [*righe[0], "esito", "nota"] if righe else ["posizione", "esito", "nota"]
        with percorso.open("x", encoding="utf-8-sig", newline="") as f:
            scrittore = csv.DictWriter(f, fieldnames=colonne, delimiter=";")
            scrittore.writeheader()
            for riga in righe:
                scrittore.writerow({**{k: _cella_csv(v) for k, v in riga.items()}, "esito": "", "nota": ""})
        return
    with percorso.open("x", encoding="utf-8") as f:
        f.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in righe))


def _leggi_giudizi(percorso: Path) -> list[dict]:
    if percorso.suffix.lower() == ".csv":
        # Excel può risalvare il file con un'altra codifica e un altro separatore: si riconoscono entrambi.
        dati = percorso.read_bytes()
        try:
            testo = dati.decode("utf-8-sig")
        except UnicodeDecodeError:
            testo = dati.decode("cp1252")
        intestazione = testo.splitlines()[0] if testo else ""
        separatore = max(";\t,", key=intestazione.count)
        lettore = csv.DictReader(testo.splitlines(), delimiter=separatore)
        if not {"posizione", "esito"} <= set(lettore.fieldnames or []):
            raise ValueError(f"colonne 'posizione' ed 'esito' non trovate in {percorso.name}")
        righe = [r for r in lettore if (r.get("esito") or "").strip()]
        return [{"posizione": r["posizione"], "esito": r["esito"].strip().lower(),
                 "nota": (r.get("nota") or "").strip() or None} for r in righe]
    return [json.loads(r) for r in percorso.read_text(encoding="utf-8").splitlines() if r.strip()]


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
    crosswalk.add_argument("--popolazione-originale", type=int, required=True)

    calcola = comandi.add_parser("calcola")
    for nome in ("--utente-sso", "--campione"):
        calcola.add_argument(nome, required=True)

    args = parser.parse_args()
    if os.environ.get("NEARTECH_DB_VIA", "").lower() == "https":
        raise SystemExit("questo script richiede la connessione diretta: il collegamento HTTPS non ha transazioni")
    try:
        _esegui(args)
    except (LookupError, ValueError, PermissionError, RuntimeError, KeyError, json.JSONDecodeError) as errore:
        raise SystemExit(f"errore ({type(errore).__name__}): {errore}") from None


def _esegui(args: argparse.Namespace) -> None:
    with connect() as conn:
        if args.comando == "anteprima":
            conn.read_only = True
            print(f"proposte nella popolazione: {len(popolazione(conn, args.tipo, _filtro(args.filtro)))}")
            return
        with connect() as conn_log:
            conn_log.autocommit = True
            configura_log(conn_log)
            try:
                _scrivi(conn, args)
            finally:
                configura_log(None)


def _scrivi(conn, args: argparse.Namespace) -> None:
    utente = _utente(conn, args.utente_sso)
    if args.comando == "crea-campione":
        campione = crea_campione(
            conn, utente, org_id=args.org, tipo=args.tipo, filtro=_filtro(args.filtro), criterio=args.criterio,
            versione_istruzioni=args.istruzioni, motivazione=args.motivazione,
            dimensione=args.dimensione, seme=args.seme,
        )
        print(f"campione creato: {campione}")
    elif args.comando == "esporta":
        if Path(args.file).exists():
            raise SystemExit(f"il file {args.file} esiste già: scegliere un altro nome")
        righe = esporta_campione(conn, utente, args.campione)
        _scrivi_esportazione(Path(args.file), righe)
        print(f"elementi esportati: {len(righe)}")
    elif args.comando == "importa-giudizi":
        righe = _leggi_giudizi(Path(args.file))
        with conn.transaction():
            for riga in righe:
                registra_giudizio(conn, utente, args.campione, int(riga["posizione"]), riga["esito"],
                                  nota=riga.get("nota"), versione_istruzioni=args.istruzioni)
        print(f"giudizi registrati: {len(righe)}")
    elif args.comando == "importa-crosswalk":
        campione = importa_revisioni_crosswalk(conn, utente, org_id=args.org, campione=args.campione,
                                               popolazione_originale=args.popolazione_originale)
        print(f"campione importato: {campione}")
    else:
        misura = calcola_precisione(conn, utente, args.campione)
        print(f"precisione {misura.precisione:.3f} (intervallo {misura.intervallo[0]:.3f}-"
              f"{misura.intervallo[1]:.3f}), {misura.esito}; corretti {misura.n_corretti}, "
              f"parziali {misura.n_parziali}, errati {misura.n_errati}; misura {misura.misura_id}")
    conn.commit()


if __name__ == "__main__":
    main()
