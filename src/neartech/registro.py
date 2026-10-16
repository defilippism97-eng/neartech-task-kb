"""Registro delle decisioni: scrittura degli atti e verifica della catena di hash.

Posizione, ora e hash li assegna il database (migrazione 0009). Le righe non si
modificano: una correzione è un atto nuovo con corregge_id.
"""

from typing import Any

import psycopg
from psycopg.types.json import Jsonb


def registra(
    conn: psycopg.Connection,
    *,
    autore_id: str,
    tipo_oggetto: str,
    oggetto_id: str,
    atto: str,
    motivazione: str,
    org_id: str | None = None,
    dettagli: dict[str, Any] | None = None,
    corregge_id: int | None = None,
) -> int:
    return conn.execute(
        """INSERT INTO registro_decisioni
             (org_id, tipo_oggetto, oggetto_id, atto, autore_id, motivazione, dettagli, corregge_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING decisione_id""",
        (org_id, tipo_oggetto, oggetto_id, atto, autore_id, motivazione, Jsonb(dettagli or {}), corregge_id),
    ).fetchone()[0]


def verifica_catena(conn: psycopg.Connection) -> int | None:
    """Ricalcola la catena. Restituisce la prima posizione alterata, o None se è integra."""
    precedente = "0" * 64
    for posizione, hash_salvato, hash_precedente, ricalcolato in conn.execute(
        """SELECT posizione, hash, hash_precedente, registro_hash(r)
           FROM registro_decisioni r ORDER BY posizione"""
    ):
        if hash_precedente != precedente or hash_salvato != ricalcolato:
            return posizione
        precedente = hash_salvato
    return None
