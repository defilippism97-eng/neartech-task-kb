"""Inserimento di evidenze normalizzate (L1/L3) collegate a un nodo di tassonomia.

Ogni evidenza porta fonte, versione, data di osservazione e punteggio su 0–4.
Le evidenze non si sovrascrivono: ogni osservazione è una riga nuova.
"""

import psycopg

from neartech.models import EvidenceIn


def add_evidence(conn: psycopg.Connection, ev: EvidenceIn) -> str:
    if ev.node_scheme is None or ev.node_code is None:
        raise ValueError("un'evidenza deve riferirsi a un nodo di tassonomia (node_scheme, node_code)")

    with conn.transaction():
        src = conn.execute(
            "SELECT source_id FROM sources WHERE name = %s AND version = %s",
            (ev.source_name, ev.source_version),
        ).fetchone()
        if src is None:
            raise ValueError(f"fonte non registrata: {ev.source_name} {ev.source_version}")

        node = conn.execute(
            """
            SELECT node_id FROM taxonomy_nodes
            WHERE scheme = %s AND code = %s
            ORDER BY lang LIMIT 1
            """,
            (ev.node_scheme.value, ev.node_code),
        ).fetchone()
        if node is None:
            raise ValueError(f"nodo non trovato: {ev.node_scheme.value} {ev.node_code}")

        row = conn.execute(
            """
            INSERT INTO evidence_items
              (source_id, evidence_type, node_id, dimension, raw_value, score_0_4, quality, observed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING evidence_id
            """,
            (
                src[0], ev.evidence_type, node[0], ev.dimension,
                ev.raw_value, ev.score_0_4, ev.quality, ev.observed_at,
            ),
        ).fetchone()
    return str(row[0])
