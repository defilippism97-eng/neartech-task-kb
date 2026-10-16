"""Registro delle decisioni: scrittura degli atti e verifica della catena di hash.

Posizione, ora e hash li assegna il database (migrazione 0009). Le righe non si
modificano: una correzione è un atto nuovo con corregge_id.

La catena rende visibile una riga alterata. Non basta contro chi cancella le ultime
righe o ricalcola tutta la catena: per questo l'auditor conserva fuori dal database
l'ancora (posizione e hash dell'ultima riga, ancora_catena) e la passa a verifica_catena.
"""

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

HASH_INIZIALE = "0" * 64


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
    """Scrittura di basso livello. Chi chiama ha già verificato i permessi (governance, permessi, stato_task)."""
    return conn.execute(
        """INSERT INTO registro_decisioni
             (org_id, tipo_oggetto, oggetto_id, atto, autore_id, motivazione, dettagli, corregge_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING decisione_id""",
        (org_id, tipo_oggetto, oggetto_id, atto, autore_id, motivazione, Jsonb(dettagli or {}), corregge_id),
    ).fetchone()[0]


def ancora_catena(conn: psycopg.Connection) -> tuple[int, str]:
    """Posizione e hash dell'ultima riga, da conservare fuori dal database."""
    riga = conn.execute(
        "SELECT posizione, hash FROM registro_decisioni ORDER BY posizione DESC LIMIT 1"
    ).fetchone()
    return (riga[0], riga[1]) if riga else (0, HASH_INIZIALE)


def verifica_catena(conn: psycopg.Connection, *, ancora: tuple[int, str] | None = None) -> int | None:
    """Ricalcola la catena. Restituisce la prima posizione alterata o mancante, o None se è integra.

    Con un'ancora, verifica anche che la riga ancorata esista ancora con lo stesso hash.
    """
    precedente = HASH_INIZIALE
    ancora_trovata = ancora is None or ancora[0] == 0
    with conn.transaction(), conn.cursor(name="verifica_catena") as cursore:
        cursore.execute(
            """SELECT posizione, hash, hash_precedente, registro_hash(r)
               FROM registro_decisioni r ORDER BY posizione"""
        )
        for posizione, hash_salvato, hash_precedente, ricalcolato in cursore:
            if hash_precedente != precedente or hash_salvato != ricalcolato:
                return posizione
            if ancora is not None and posizione == ancora[0]:
                if hash_salvato != ancora[1]:
                    return posizione
                ancora_trovata = True
            precedente = hash_salvato
    return None if ancora_trovata else ancora[0]
