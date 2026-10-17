"""Set di controllo del prompt del Canonicalizer (CLAUDE.md: prima di nuove esecuzioni).

Ripete le chiamate della prima esecuzione sui task di riferimento di un campione di fusioni già
giudicato da persone: stesso task, stessi vicini registrati in fusioni_proposte, prompt e modello
attuali. Confronta le decisioni nuove con i giudizi umani (parziali contati come il parametro
regola_parziali vigente: oggi errori) e con le decisioni della prima esecuzione.

Uso (DATABASE_URL in sola lettura; chiave del modello da NEARTECH_ANTHROPIC_API_KEY):
  python scripts/controllo_canonicalizer.py --campione 86199f1e-... --uscita docs/revisione/controllo/x.jsonl

Nessuna scrittura nel database: le decisioni del controllo vanno nel file (una riga per vicino giudicato)
e il riepilogo in <uscita>.riepilogo.json. Il file non contiene testo del cliente: titoli canonici e
motivazioni del modello.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech import canonicalizer  # noqa: E402
from neartech.canonicalizer import CanonicalizerError, Vicino, giudica  # noqa: E402
from neartech.db import connect  # noqa: E402


class _ClienteConConsumo:
    """Conta i token di ogni chiamata, tentativi ripetuti compresi."""

    def __init__(self, client):
        self._client = client
        self.chiamate = self.ingresso = self.uscita = 0
        self.messages = self

    def create(self, **kwargs):
        risposta = self._client.messages.create(**kwargs)
        self.chiamate += 1
        self.ingresso += risposta.usage.input_tokens
        self.uscita += risposta.usage.output_tokens
        return risposta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--campione", required=True)
    parser.add_argument("--uscita", required=True)
    args = parser.parse_args()
    uscita, riepilogo_file = Path(args.uscita), Path(args.uscita + ".riepilogo.json")
    for percorso in (uscita, riepilogo_file):
        if percorso.exists():
            raise SystemExit(f"il file {percorso} esiste già: scegliere un altro nome")
    api_key = os.environ.get("NEARTECH_ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("NEARTECH_ANTHROPIC_API_KEY non configurata")
    client = _ClienteConConsumo(anthropic.Anthropic(api_key=api_key))

    with connect() as conn:
        conn.read_only = True
        # Coppie del campione con l'ultimo giudizio umano di ciascun elemento.
        coppie = {(str(r[0]), str(r[1])): r[2] for r in conn.execute(
            """SELECT f.task_id, f.altro_task_id, g.esito
               FROM elementi_campione e
               JOIN fusioni_proposte f ON f.proposal_id = (e.riferimento ->> 'proposal_id')::uuid
               JOIN LATERAL (SELECT esito FROM giudizi_revisione g
                             WHERE g.campione_id = e.campione_id AND g.posizione = e.posizione
                             ORDER BY g.giudizio_id DESC LIMIT 1) g ON true
               WHERE e.campione_id = %s""", (args.campione,)).fetchall()}
        if not coppie:
            raise SystemExit("campione senza coppie giudicate")
        regola = conn.execute(
            "SELECT valore ->> 'valore' FROM parametri_vigenti WHERE codice = 'regola_parziali' AND org_id IS NULL"
        ).fetchone()[0]
        titoli = {str(r[0]): r[1] for r in conn.execute("SELECT task_id, title_it FROM canonical_tasks")}
        riferimenti = sorted({a for a, _ in coppie}, key=lambda t: titoli[t])
        righe, falliti = [], []
        for i, riferimento in enumerate(riferimenti, start=1):
            prima = conn.execute(
                """SELECT altro_task_id, decisione FROM fusioni_proposte WHERE task_id = %s
                   ORDER BY altro_task_id""", (riferimento,)).fetchall()
            vicini = [Vicino(str(v), titoli[str(v)], 0) for v, _ in prima]
            try:
                giudizi = giudica(client, titoli[riferimento], vicini)
            except CanonicalizerError as errore:
                falliti.append(riferimento)
                print(f"[{i}/{len(riferimenti)}] ERRORE: {errore}", flush=True)
                continue
            decisione_prima = {str(v): d for v, d in prima}
            for vicino, decisione, motivazione in giudizi:
                righe.append({
                    "task_id": riferimento, "altro_task_id": vicino.task_id,
                    "titolo": titoli[riferimento], "titolo_altro": vicino.titolo,
                    "decisione_v1": decisione_prima[vicino.task_id], "decisione_v2": decisione,
                    "motivazione_v2": motivazione,
                    "giudizio_umano": coppie.get((riferimento, vicino.task_id)),
                })
            print(f"[{i}/{len(riferimenti)}] fatto", flush=True)

    # Precisione delle proposte "stessa_attivita" del prompt nuovo sulle coppie giudicate da persone.
    giudicate = [r for r in righe if r["giudizio_umano"]]
    proposte_v2 = [r for r in giudicate if r["decisione_v2"] == "stessa_attivita"]
    def successo(esito: str) -> bool | None:
        if esito == "parziale":
            return {"errore": False, "corretto": True}.get(regola)  # 'escluso': fuori dal conteggio
        return esito == "corretto"
    contate = [r for r in proposte_v2 if successo(r["giudizio_umano"]) is not None]
    corrette = sum(successo(r["giudizio_umano"]) for r in contate)
    riepilogo = {
        "campione": args.campione, "model_name": canonicalizer.MODEL_ID, "prompt_hash": canonicalizer.prompt_hash(),
        "regola_parziali": regola, "chiamate": client.chiamate, "token_ingresso": client.ingresso,
        "token_uscita": client.uscita, "task_falliti": falliti,
        "coppie_giudicate": len(giudicate),
        "esiti_umani": {e: sum(r["giudizio_umano"] == e for r in giudicate) for e in ("corretto", "parziale", "errato")},
        "v2_stessa_attivita": len(proposte_v2),
        "v2_precisione": round(corrette / len(contate), 4) if contate else None,
        "corrette_mantenute": sum(r["decisione_v2"] == "stessa_attivita" for r in giudicate
                                  if r["giudizio_umano"] == "corretto"),
        "non_corrette_respinte": {e: sum(r["decisione_v2"] == "diversa" for r in giudicate if r["giudizio_umano"] == e)
                                  for e in ("parziale", "errato")},
        "altre_coppie": len(righe) - len(giudicate),
        "altre_da_diversa_a_stessa": sum(1 for r in righe if not r["giudizio_umano"]
                                         and r["decisione_v1"] == "diversa" and r["decisione_v2"] == "stessa_attivita"),
    }
    uscita.parent.mkdir(parents=True, exist_ok=True)
    with open(uscita, "x", encoding="utf-8") as f:
        f.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in righe))
    with open(riepilogo_file, "x", encoding="utf-8") as f:
        f.write(json.dumps(riepilogo, ensure_ascii=False, indent=2))
    print(json.dumps(riepilogo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
