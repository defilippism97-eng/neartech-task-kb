"""Carica nel database le tassonomie (O*NET, Atlante, ESCO) e i loro embedding.

Uso:
  DATABASE_URL=postgresql://... python scripts/carica_tassonomie.py \
      --onet-zip onet_31_0_text.zip --atlante-json adaCompleto.json \
      --esco-csv-zip esco_classification_it_csv.zip \
      --embeddings-dir kb_work/out

Ogni fonte è una versione registrata in `sources`: il caricamento è idempotente e
si ferma se la stessa versione è già presente con contenuto diverso.
Le licenze vanno registrate prima del caricamento: qui si passa il riferimento
che il responsabile ha confermato.
"""

import argparse
import csv
import io
import json
import tempfile
import zipfile
from pathlib import Path

import numpy as np

from neartech.db import connect
from neartech.taxonomy import BATCH_SIZE, load_taxonomy

LICENZA_CONFERMATA = "confermata dal responsabile del progetto (2026-10-10); testo della licenza da allegare"


def write_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["scheme", "code", "label", "lang", "parent_code"])
        w.writeheader()
        w.writerows(rows)


def onet_rows(zip_path: Path) -> list[dict]:
    with zipfile.ZipFile(zip_path) as z:
        name = next(n for n in z.namelist() if n.endswith("Task Statements.txt"))
        with z.open(name) as f:
            return [
                {"scheme": "ONET_TASK", "code": r["Task ID"], "label": r["Task"].strip(),
                 "lang": "en", "parent_code": ""}
                for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
            ]


def atlante_rows(json_path: Path) -> list[dict]:
    ada_list = json.loads(json_path.read_text(encoding="utf-8-sig"))["result"]
    rows, seen_ra, seen_at = [], set(), set()
    for ada in ada_list:
        rows.append({"scheme": "ATLANTE_ADA", "code": ada["codice_ada"], "label": ada["titolo_ada"].strip(),
                     "lang": "it", "parent_code": ""})
        for ra in ada["risultati_attesi"]:
            if ra["codice_risultato"] not in seen_ra:
                seen_ra.add(ra["codice_risultato"])
                rows.append({"scheme": "ATLANTE_RA", "code": ra["codice_risultato"],
                             "label": ra["titolo_risultato"].strip(), "lang": "it",
                             "parent_code": ada["codice_ada"]})
            for at in ra.get("attivita", []):
                # Un'attività può comparire sotto più risultati: il primo è il genitore.
                if at["id_attivita"] not in seen_at:
                    seen_at.add(at["id_attivita"])
                    rows.append({"scheme": "ATLANTE_ATTIVITA", "code": at["id_attivita"],
                                 "label": at["titolo_attivita"].strip(), "lang": "it",
                                 "parent_code": ra["codice_risultato"]})
    return rows


def esco_rows(zip_path: Path) -> list[dict]:
    rows = []
    with zipfile.ZipFile(zip_path) as z:
        for fname, scheme in [("occupations_it.csv", "ESCO_OCC"), ("skills_it.csv", "ESCO_SKILL")]:
            with z.open(fname) as f:
                for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")):
                    rows.append({"scheme": scheme, "code": r["conceptUri"].rsplit("/", 1)[-1],
                                 "label": r["preferredLabel"].strip(), "lang": "it", "parent_code": ""})
    return rows


def load_source(conn, rows: list[dict], *, name: str, version: str, uri: str, tmp: Path):
    path = tmp / f"{name.replace(' ', '_')}_{version.replace(' ', '_')}.csv"
    write_csv(rows, path)
    res = load_taxonomy(conn, path, name=name, version=version, license=LICENZA_CONFERMATA, uri=uri)
    print(f"{name} {version}: inseriti {res.nodes_inserted}, totali {res.nodes_total}", flush=True)


def load_embeddings(conn, embeddings_dir: Path, model: str) -> None:
    index = [json.loads(l) for l in (embeddings_dir / "embeddings_index.jsonl").read_text(encoding="utf-8").splitlines()]
    vecs = np.load(embeddings_dir / "embeddings_bge_m3.npy").astype(np.float32)
    esco = [json.loads(l) for l in (embeddings_dir / "embeddings_esco_index.jsonl").read_text(encoding="utf-8").splitlines()]
    esco_vecs = np.load(embeddings_dir / "embeddings_esco_bge_m3.npy").astype(np.float32)
    pairs = list(zip(index, vecs)) + list(zip(esco, esco_vecs))

    # Scritture a blocchi: vedi BATCH_SIZE in taxonomy.py.
    with conn.transaction():
        for start in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[start : start + BATCH_SIZE]
            records = [
                {"scheme": meta["scheme"], "code": meta["code"], "lang": meta["lang"],
                 "vec": "[" + ",".join(f"{x:.6f}" for x in vec) + "]"}
                for meta, vec in batch
            ]
            payload = json.dumps(records)
            found = conn.execute(
                """SELECT count(*) FROM json_to_recordset(%s::json) AS v(scheme text, code text, lang text, vec text)
                   JOIN taxonomy_nodes n ON n.scheme = v.scheme AND n.code = v.code AND n.lang = v.lang""",
                (payload,),
            ).fetchone()[0]
            if found != len(batch):
                raise ValueError(f"nodi mancanti per gli embedding: attesi {len(batch)}, trovati {found}")
            conn.execute(
                """INSERT INTO taxonomy_embeddings (node_id, model_name, vec)
                   SELECT n.node_id, %s, v.vec::vector
                   FROM json_to_recordset(%s::json) AS v(scheme text, code text, lang text, vec text)
                   JOIN taxonomy_nodes n ON n.scheme = v.scheme AND n.code = v.code AND n.lang = v.lang
                   ON CONFLICT (node_id, model_name) DO NOTHING""",
                (model, payload),
            )
    print(f"embedding {model}: {len(pairs)} vettori", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--onet-zip", type=Path, required=True)
    ap.add_argument("--atlante-json", type=Path, required=True)
    ap.add_argument("--esco-csv-zip", type=Path, required=True)
    ap.add_argument("--embeddings-dir", type=Path, required=True)
    args = ap.parse_args()

    with connect() as conn, tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        load_source(conn, onet_rows(args.onet_zip), name="O*NET", version="31.0",
                    uri="https://www.onetcenter.org/database.html", tmp=tmp)
        load_source(conn, atlante_rows(args.atlante_json), name="Atlante del Lavoro INAPP",
                    version="API v2 snapshot 2026-10-10", uri="https://atlantelavoro.inapp.org/api/v2", tmp=tmp)
        load_source(conn, esco_rows(args.esco_csv_zip), name="ESCO", version="1.2.1",
                    uri="https://esco.ec.europa.eu", tmp=tmp)
        load_embeddings(conn, args.embeddings_dir, "BAAI/bge-m3")
        conn.commit()


if __name__ == "__main__":
    main()
