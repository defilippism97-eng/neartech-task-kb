"""Etichettatura silver dei task con un modello Claude.

Uso:
    python scripts/etichetta_silver.py --asse N --run 1 --limite 10
    python scripts/etichetta_silver.py --asse D --run 1 --dry-run

La chiave viene letta da NEARTECH_ANTHROPIC_API_KEY. Non viene mai stampata.
Ogni riga valida viene salvata con i metadati in docs/silver/output/.
"""

import argparse
import datetime
import json
import os
import pathlib
import sys

RADICE = pathlib.Path(__file__).resolve().parent.parent
PACCHETTO = RADICE / "docs" / "silver" / "pacchetto-gemini.md"
DATASET = RADICE / "docs" / "silver" / "dataset" / "task-silver.jsonl"
OUTPUT = RADICE / "docs" / "silver" / "output"

MODELLO = "claude-haiku-5-5"
VERSIONE_RUBRICA = "bozza-3"
DIMENSIONE_LOTTO = 10
MAX_TOKEN_RISPOSTA = 4000
PROMPT = "v2"

SCALA = {
    "N": {"k1", "k2", "k3", "r"},
    "D": {"d1", "d2"},
}
FIDUCIA = {"alta", "media", "bassa"}


def carica_task(limite):
    righe = [json.loads(r) for r in DATASET.read_text(encoding="utf-8").splitlines() if r.strip()]
    return righe[:limite] if limite else righe


def lotti(task, dimensione):
    for i in range(0, len(task), dimensione):
        yield task[i:i + dimensione]


def testo_lotto(asse, lotto):
    corpo = [f"Asse da valutare: {asse}. Usa solo le regole e le rubriche di questo asse."]
    corpo.append("Task (id, titolo, nota di contesto):")
    for t in lotto:
        corpo.append(json.dumps(t, ensure_ascii=False))
    corpo.append("Rispondi solo con una riga JSONL per task, nel formato indicato nelle istruzioni.")
    return "\n".join(corpo)


def valida_riga(asse, riga, ids_attesi):
    """Restituisce (dati, errore). Un solo errore per riga."""
    try:
        d = json.loads(riga)
    except json.JSONDecodeError as e:
        return None, f"JSON non valido: {e}"
    if d.get("id") not in ids_attesi:
        return None, f"id sconosciuto: {d.get('id')}"
    if d.get("asse") != asse:
        return None, f"asse errato: {d.get('asse')}"
    for campo in SCALA[asse]:
        v = d.get(campo)
        if not isinstance(v, int) or not 0 <= v <= 4:
            return None, f"{campo} fuori scala: {v}"
    if asse == "D":
        if not isinstance(d.get("riserva_legge"), bool):
            return None, "riserva_legge non booleana"
        if d.get("fiducia") not in FIDUCIA:
            return None, f"fiducia non valida: {d.get('fiducia')}"
    return d, None


def etichetta(client, asse, lotto, system):
    risposta = client.messages.create(
        model=MODELLO,
        max_tokens=MAX_TOKEN_RISPOSTA,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": testo_lotto(asse, lotto)}],
    )
    testo = "".join(b.text for b in risposta.content if b.type == "text")
    return testo, risposta.usage


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--asse", choices=["N", "D"], required=True)
    p.add_argument("--run", type=int, default=1)
    p.add_argument("--limite", type=int, default=0, help="numero di task (0 = tutti)")
    p.add_argument("--dry-run", action="store_true", help="non chiama l'API")
    a = p.parse_args()

    system = PACCHETTO.read_text(encoding="utf-8")
    task = carica_task(a.limite)
    blocchi = list(lotti(task, DIMENSIONE_LOTTO))

    if a.dry_run:
        print(f"asse {a.asse}, run {a.run}: {len(task)} task in {len(blocchi)} lotti (modello {MODELLO})")
        print(f"caratteri del pacchetto: {len(system)}")
        return 0

    chiave = os.environ.get("NEARTECH_ANTHROPIC_API_KEY")
    if not chiave:
        print("NEARTECH_ANTHROPIC_API_KEY non impostata nella sessione. Riapri il terminale.", file=sys.stderr)
        return 1

    import anthropic

    client = anthropic.Anthropic(api_key=chiave)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    data = datetime.date.today().isoformat()
    file_out = OUTPUT / f"{a.asse}-{PROMPT}-run{a.run}-{data}.jsonl"
    errori = OUTPUT / f"{a.asse}-{PROMPT}-run{a.run}-{data}.errori.txt"

    tot_in = tot_out = tot_cache = 0
    ok = 0
    with file_out.open("w", encoding="utf-8") as fo, errori.open("w", encoding="utf-8") as fe:
        for n, lotto in enumerate(blocchi, 1):
            ids = {t["id"] for t in lotto}
            testo, uso = etichetta(client, a.asse, lotto, system)
            tot_in += uso.input_tokens
            tot_out += uso.output_tokens
            tot_cache += getattr(uso, "cache_read_input_tokens", 0) or 0
            visti = set()
            for riga in testo.splitlines():
                if not riga.strip():
                    continue
                dati, err = valida_riga(a.asse, riga, ids)
                if err:
                    fe.write(f"lotto {n}: {err} | {riga[:200]}\n")
                    continue
                visti.add(dati["id"])
                dati.update({
                    "modello": MODELLO,
                    "versione_rubrica": VERSIONE_RUBRICA,
                    "prompt": f"{a.asse}-{PROMPT}",
                    "run": a.run,
                    "data": data,
                })
                fo.write(json.dumps(dati, ensure_ascii=False) + "\n")
                ok += 1
            for mancante in sorted(ids - visti):
                fe.write(f"lotto {n}: nessuna risposta valida per {mancante}\n")
            print(f"lotto {n}/{len(blocchi)} fatto: {len(visti)}/{len(ids)} valide")

    print(f"righe valide: {ok}. Output: {file_out.name}. Errori: {errori.name}")
    print(f"token input {tot_in}, di cui letti da cache {tot_cache}, output {tot_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


