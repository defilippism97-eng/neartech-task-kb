"""Abbinamento dei candidati di un'organizzazione al dataset consolidato (fase 3, ADR 0006).

Uso (DATABASE_URL dall'ambiente; l'utente è indicato dal soggetto SSO). Nessuna chiamata all'API:
l'embedding (bge-m3) si calcola in locale.
  python scripts/abbina.py proponi  --utente-sso S --org CODICE --motivazione "..."
  python scripts/abbina.py livello  --utente-sso REVISORE --org CODICE --lotto L --livello campione --motivazione "..."
  python scripts/abbina.py coda     --utente-sso S --org CODICE --lotto L [--quante 30]
  python scripts/abbina.py campione --utente-sso S --org CODICE --lotto L --seme 20261017 \\
      --istruzioni istruzioni-abbinamento-v1 --motivazione "..."
  python scripts/abbina.py decidi   --utente-sso S --org CODICE --lotto L --rifiutate rifiutate.txt --motivazione "..."
  python scripts/abbina.py applica  --utente-sso S --org CODICE --lotto L --motivazione "..."

Fra 'campione' e 'decidi': esportazione cieca, giudizi e misura con scripts/metrica.py
(esporta, importa-giudizi, calcola) sul campione creato. --rifiutate: un file con un identificativo di
proposta per riga (righe vuote e righe che iniziano con # ignorate); senza file il lotto si approva tutto.
Proponi, campione, decidi e applica scrivono nel database: in produzione con l'approvazione del responsabile.
Serve la connessione diretta: con NEARTECH_DB_VIA=https gli atti non troverebbero il testo nello spazio.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.abbinamento import (  # noqa: E402
    MODELLO_EMBEDDING,
    applica_lotto,
    coda_revisione,
    crea_campione_del_lotto,
    decidi_lotto,
    imposta_livello,
    proponi_abbinamenti,
)
from neartech.db import connect  # noqa: E402
from neartech.permessi import configura_log  # noqa: E402
from neartech.scomposizione import organizzazione_per_codice  # noqa: E402


def _incorpora():
    """bge-m3 in locale, caricato alla prima chiamata; vettori normalizzati come per i task del dataset."""
    caricato = []

    def incorpora(titoli: list[str]):
        if not caricato:
            from sentence_transformers import SentenceTransformer
            caricato.append(SentenceTransformer(MODELLO_EMBEDDING, device="cpu"))
        return caricato[0].encode(titoli, batch_size=64, normalize_embeddings=True).tolist()

    incorpora.modello = MODELLO_EMBEDDING
    return incorpora


def _rifiutate(percorso: Path | None) -> list[str]:
    if percorso is None:
        return []
    return [r.strip() for r in percorso.read_text(encoding="utf-8").splitlines()
            if r.strip() and not r.strip().startswith("#")]


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    comandi = ap.add_subparsers(dest="comando", required=True)
    for nome in ("proponi", "livello", "coda", "campione", "decidi", "applica"):
        c = comandi.add_parser(nome)
        c.add_argument("--utente-sso", required=True)
        c.add_argument("--org", required=True, help="codice dell'organizzazione")
        if nome != "proponi":
            c.add_argument("--lotto", required=True)
        if nome in ("proponi", "livello", "campione", "decidi", "applica"):
            c.add_argument("--motivazione", required=True)
    comandi.choices["livello"].add_argument("--livello", choices=("campione", "completa", "nulla"), required=True)
    comandi.choices["coda"].add_argument("--quante", type=int, default=30)
    comandi.choices["campione"].add_argument("--seme", type=int, required=True)
    comandi.choices["campione"].add_argument("--istruzioni", required=True)
    comandi.choices["decidi"].add_argument("--rifiutate", type=Path)
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
            utente, org = str(riga[0]), organizzazione_per_codice(conn, args.org)
            if args.comando == "proponi":
                lotto = proponi_abbinamenti(conn, utente, org, incorpora=_incorpora(), motivazione=args.motivazione)
                print(f"lotto creato: {lotto}; il livello di revisione lo sceglie il revisore (comando livello)")
            elif args.comando == "livello":
                atto = imposta_livello(conn, utente, org, args.lotto, livello_revisione=args.livello,
                                       motivazione=args.motivazione)
                print(f"livello di revisione registrato, atto {atto}")
            elif args.comando == "coda":
                for voce in coda_revisione(conn, utente, org, args.lotto)[: args.quante]:
                    margine = "-" if voce["margine"] is None else f"{voce['margine']:.3f}"
                    distanza = "-" if voce["distanza"] is None else f"{voce['distanza']:.3f}"
                    print(f"{voce['proposta_id']}  margine {margine}  distanza {distanza}  "
                          f"{voce['candidato']}  ->  {voce['task_proposto'] or '(nessun task vicino)'}")
            elif args.comando == "campione":
                campione = crea_campione_del_lotto(conn, utente, org, args.lotto, seme=args.seme,
                                                   versione_istruzioni=args.istruzioni, motivazione=args.motivazione)
                print(f"campione creato: {campione}")
            elif args.comando == "decidi":
                atto = decidi_lotto(conn, utente, org, args.lotto, rifiutate=_rifiutate(args.rifiutate),
                                    motivazione=args.motivazione)
                print(f"lotto deciso, atto {atto}")
            else:
                esito = applica_lotto(conn, utente, org, args.lotto, incorpora=_incorpora(),
                                      motivazione=args.motivazione)
                print(f"lotto applicato: {esito['collegate']} collegate, {esito['task_nuovi']} task nuovi, "
                      f"{esito['occorrenze_nuove']} occorrenze nuove")
        except (LookupError, ValueError, PermissionError, RuntimeError) as errore:
            raise SystemExit(f"errore ({type(errore).__name__}): {errore}") from None
        finally:
            configura_log(None)


if __name__ == "__main__":
    main()
