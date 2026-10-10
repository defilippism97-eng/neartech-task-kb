"""Caricamento di una tassonomia (L0) da CSV.

Colonne attese: scheme, code, label, lang, parent_code.
Il caricamento è idempotente: la stessa versione dello stesso file non
duplica nulla. Se una versione esistente cambia contenuto (hash diverso)
il caricamento si ferma: la versione va incrementata, non sovrascritta.
"""

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

import psycopg

from neartech.models import TaxonomyNodeIn


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
        for node in nodes:
            cur = conn.execute(
                """
                INSERT INTO taxonomy_nodes (scheme, code, label, lang, source_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (scheme, code, lang, source_id) DO NOTHING
                """,
                (node.scheme.value, node.code, node.label, node.lang, source_id),
            )
            inserted += cur.rowcount

        # Seconda passata: i genitori si collegano dopo che tutti i nodi esistono.
        for node in nodes:
            if node.parent_code:
                conn.execute(
                    """
                    UPDATE taxonomy_nodes child
                    SET parent_id = parent.node_id
                    FROM taxonomy_nodes parent
                    WHERE child.scheme = %s AND child.code = %s AND child.lang = %s
                      AND child.source_id = %s
                      AND parent.scheme = child.scheme AND parent.code = %s
                      AND parent.source_id = child.source_id
                    """,
                    (node.scheme.value, node.code, node.lang, source_id, node.parent_code),
                )

        total = conn.execute(
            "SELECT count(*) FROM taxonomy_nodes WHERE source_id = %s", (source_id,)
        ).fetchone()[0]

    return TaxonomyLoadResult(source_id=str(source_id), nodes_inserted=inserted, nodes_total=total)
