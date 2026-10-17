"""Calcola gli embedding bge-m3 dei nodi delle tassonomie, nel formato letto da carica_tassonomie.py.

Produce nella cartella indicata:
  embeddings_index.jsonl        nodi O*NET e Atlante (ordine = righe di embeddings_bge_m3.npy)
  embeddings_bge_m3.npy         vettori float32, shape (n, 1024)
  embeddings_esco_index.jsonl   nodi ESCO
  embeddings_esco_bge_m3.npy    vettori float32, shape (m, 1024)

Il testo incorporato è solo l'etichetta del nodo, nella lingua della fonte.

Uso:
  python scripts/calcola_embedding.py --onet-zip ... --atlante-json ... --esco-csv-zip ... --out-dir ...
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from carica_tassonomie import atlante_rows, esco_rows, onet_rows  # noqa: E402

MODEL_NAME = "BAAI/bge-m3"
MODEL_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"  # stessa di neartech.crosswalk.EMBEDDING_REVISION
BATCH = 64


def _encode(model, texts: list[str]) -> np.ndarray:
    vecs = model.encode(texts, batch_size=BATCH, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vecs, dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--onet-zip", type=Path, required=True)
    ap.add_argument("--atlante-json", type=Path, required=True)
    ap.add_argument("--esco-csv-zip", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer

    args.out_dir.mkdir(parents=True, exist_ok=True)
    onet_atl = onet_rows(args.onet_zip) + atlante_rows(args.atlante_json)
    esco = esco_rows(args.esco_csv_zip)

    print(f"carico il modello {MODEL_NAME}", flush=True)
    model = SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION, device="cpu")

    for rows, stem in [(onet_atl, "embeddings"), (esco, "embeddings_esco")]:
        index = [{"scheme": r["scheme"], "code": r["code"], "lang": r["lang"]} for r in rows]
        vecs = []
        for start in range(0, len(rows), 1024):
            vecs.append(_encode(model, [r["label"] for r in rows[start : start + 1024]]))
            print(f"{stem}: {min(start + 1024, len(rows))}/{len(rows)}", flush=True)
        matrix = np.vstack(vecs)
        (args.out_dir / f"{stem}_index.jsonl").write_text(
            "\n".join(json.dumps(m, ensure_ascii=False) for m in index) + "\n", encoding="utf-8"
        )
        np.save(args.out_dir / f"{stem}_bge_m3.npy", matrix)
        print(f"{stem}: salvati {matrix.shape}", flush=True)


if __name__ == "__main__":
    main()
