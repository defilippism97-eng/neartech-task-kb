"""Caricamento di una tassonomia (L0) da CSV.

Colonne attese: scheme, code, label, lang, parent_code.
Il caricamento è idempotente: la stessa versione dello stesso file non
duplica nulla. Se una versione esistente cambia contenuto (hash diverso)
il caricamento si ferma: la versione va incrementata, non sovrascritta.
"""

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TypeVar

import psycopg

from neartech.models import TaxonomyNodeIn

BATCH_SIZE = 500
_T = TypeVar("_T")

# Lo schema del genitore di ciascun livello Atlante: il risultato atteso sta sotto l'ADA,
# l'attività sotto il risultato atteso. Senza questa mappa il genitore non verrebbe trovato.
PARENT_SCHEME = {"ATLANTE_RA": "ATLANTE_ADA", "ATLANTE_ATTIVITA": "ATLANTE_RA"}


def _chunks(items: list[_T], size: int) -> Iterator[list[_T]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


@dataclass(frozen=True)
class TaxonomyLoadResult:
    source_id: str
    nodes_inserted: int
    nodes_total: int


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_nodes(path: Path) -> list[TaxonomyNodeIn]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [
            TaxonomyNodeIn(**{k: (v or None) if k == "parent_code" else v for k, v in row.items()})
            for row in csv.DictReader(fh)
        ]


def load_taxonomy(
    conn: psycopg.Connection,
    path: Path,
    *,
    name: str,
    version: str,
    license: str,
    uri: str | None = None,
) -> TaxonomyLoadResult:
    nodes = _read_nodes(path)
    content_hash = _file_hash(path)

    with conn.transaction():
        row = conn.execute(
            """
            INSERT INTO sources (kind, name, version, uri, license, content_hash)
            VALUES ('taxonomy', %s, %s, %s, %s, %s)
            ON CONFLICT (name, version) DO NOTHING
            RETURNING source_id
            """,
            (name, version, uri, license, content_hash),
        ).fetchone()

        if row is None:
            row = conn.execute(
                "SELECT source_id, content_hash FROM sources WHERE name = %s AND version = %s",
                (name, version),
            ).fetchone()
            if row[1] != content_hash:
                raise ValueError(
                    f"{name} {version} è già caricata con contenuto diverso: "
                    "incrementa la versione invece di sovrascriverla"
                )
            source_id = row[0]
        else:
            source_id = row[0]

        inserted = 0
        # Scritture a blocchi: una riga per nodo sarebbe troppo lenta su collegamenti remoti.
        for chunk in _chunks(nodes, BATCH_SIZE):
            values = ", ".join(["(%s, %s, %s, %s, %s)"] * len(chunk))
            params = [v for n in chunk for v in (n.scheme.value, n.code, n.label, n.lang, source_id)]
            cur = conn.execute(
                f"""
                INSERT INTO taxonomy_nodes (scheme, code, label, lang, source_id)
                VALUES {values}
                ON CONFLICT (scheme, code, lang, source_id) DO NOTHING
                """,
                params,
            )
            inserted += cur.rowcount

        # Seconda passata: i genitori si collegano dopo che tutti i nodi esistono.
        links = [
            {
                "scheme": n.scheme.value,
                "code": n.code,
                "lang": n.lang,
                "parent_scheme": PARENT_SCHEME.get(n.scheme.value, n.scheme.value),
                "parent_code": n.parent_code,
            }
            for n in nodes
            if n.parent_code
        ]
        for chunk in _chunks(links, BATCH_SIZE):
            conn.execute(
                """
                UPDATE taxonomy_nodes child
                SET parent_id = parent.node_id
                FROM json_to_recordset(%s::json)
                       AS l(scheme text, code text, lang text, parent_scheme text, parent_code text)
                JOIN taxonomy_nodes parent
                  ON parent.scheme = l.parent_scheme AND parent.code = l.parent_code
                WHERE child.scheme = l.scheme AND child.code = l.code AND child.lang = l.lang
                  AND child.source_id = %s AND parent.source_id = child.source_id
                """,
                (json.dumps(chunk), source_id),
            )

        total = conn.execute(
            "SELECT count(*) FROM taxonomy_nodes WHERE source_id = %s", (source_id,)
        ).fetchone()[0]

    return TaxonomyLoadResult(source_id=str(source_id), nodes_inserted=inserted, nodes_total=total)
