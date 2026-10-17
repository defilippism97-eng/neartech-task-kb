"""Importa le etichette silver v2 (giudizi di Haiku 5.5 su N e D) come valutazioni registrate.

Uso (DATABASE_URL dall'ambiente; serve gestire_dataset_centrale):
  python scripts/importa_etichette_silver.py --utente-sso S [--dry-run]

Legge docs/silver/dataset/task-silver.jsonl (id e titolo) e i file docs/silver/output/{N,D}-v2-run{1,2,3}-*.jsonl.
Ogni run è una campagna (silver-N-v2-run1, ...): i giudizi ripetuti delle run di stabilità restano campioni
distinti. Le righe fuori dal dataset (aree di responsabilità) si saltano. Nessuna chiamata all'API.
La rubrica 'bozza-3' si registra come bozza: non corrente e non approvata.
"""

import argparse
import json
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "src"))

from neartech.db import connect  # noqa: E402
from neartech.permessi import configura_log  # noqa: E402
from neartech.valutazioni import importa_giudizi_modello  # noqa: E402

DATASET = RADICE / "docs" / "silver" / "dataset" / "task-silver.jsonl"
USCITE = RADICE / "docs" / "silver" / "output"
VOCI = {"N": ("k1", "k2", "k3", "r"), "D": ("d1", "d2")}


def _jsonl(percorso: Path) -> list[dict]:
    return [json.loads(r) for r in percorso.read_text(encoding="utf-8").splitlines() if r.strip()]


def campagne() -> list[tuple[str, str, str, str, list[dict]]]:
    """(campagna, rubrica, modello, prompt, righe) per ogni file di run, in ordine stabile."""
    titoli = {r["id"]: r["titolo"] for r in _jsonl(DATASET)}
    risultato = []
    for asse in ("N", "D"):
        for percorso in sorted(USCITE.glob(f"{asse}-v2-run*-*.jsonl")):
            etichette = _jsonl(percorso)
            if not etichette:
                continue
            prima = etichette[0]
            righe = []
            for e in etichette:
                if e["id"] not in titoli:
                    continue
                motivazione = e.get("incertezza") if asse == "N" else f"fiducia: {e.get('fiducia')}"
                righe.append({"titolo": titoli[e["id"]], "valori": {v: e[v] for v in VOCI[asse]},
                              "motivazione": motivazione or None})
            risultato.append((f"silver-{prima['prompt']}-run{prima['run']}", prima["versione_rubrica"],
                              prima["modello"], prima["prompt"], righe))
    return risultato


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--utente-sso", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    elenco = campagne()
    for campagna, rubrica, modello, prompt, righe in elenco:
        print(f"{campagna}: {len(righe)} task, rubrica {rubrica}, modello {modello}")
    if args.dry_run:
        return
    with connect() as conn, connect() as conn_log:
        conn_log.autocommit = True
        configura_log(conn_log)
        try:
            riga = conn.execute("SELECT utente_id FROM utenti WHERE soggetto_sso = %s", (args.utente_sso,)).fetchone()
            if riga is None:
                raise SystemExit("utente sconosciuto")
            for campagna, rubrica, modello, prompt, righe in elenco:
                esito = importa_giudizi_modello(
                    conn, str(riga[0]), righe, campagna=campagna, rubrica=rubrica, modello=modello, prompt=prompt,
                    motivazione=f"importazione delle etichette silver {campagna} (giudizi di modello, rubrica in bozza)")
                print(f"{campagna}: {esito}")
        except (LookupError, ValueError, PermissionError) as errore:
            raise SystemExit(f"errore ({type(errore).__name__}): {errore}") from None
        finally:
            configura_log(None)


if __name__ == "__main__":
    main()
