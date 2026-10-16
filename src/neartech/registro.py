"""Registro delle decisioni: scrittura degli atti e verifica della catena di hash.

Posizione, ora e hash li assegna il database (migrazione 0009). Le righe non si
modificano: una correzione è un atto nuovo con corregge_id.

La catena rende visibile una riga alterata. Non basta contro chi cancella le ultime
righe o ricalcola tutta la catena: per questo l'auditor conserva fuori dal database
l'ancora (posizione e hash dell'ultima riga, ancora_catena) e la passa a verifica_catena.

Testi delle organizzazioni (ADR 0004): per un atto di un'organizzazione con spazio, la motivazione
e i dettagli testuali (dettagli_riservati) stanno in org_<codice>.testi_atti; nel registro condiviso
restano il marcatore, i dettagli strutturali (codici, versioni, valori) e l'hash del testo, che la
catena protegge. verifica_testi confronta lo spazio con l'hash.
"""

import hashlib
import json
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

HASH_INIZIALE = "0" * 64
MARCATORE_SPAZIO = "nello spazio dell'organizzazione"  # stesso valore nella migrazione 0025


def hash_testo(motivazione: str, dettagli: dict[str, Any]) -> str:
    serializzato = json.dumps({"dettagli": dettagli, "motivazione": motivazione},
                              sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serializzato.encode("utf-8")).hexdigest()


def spazio(conn: psycopg.Connection, org_id: str) -> sql.Identifier | None:
    """Schema dell'organizzazione, o None se non ne ha uno (organizzazioni precedenti agli spazi)."""
    riga = conn.execute(
        "SELECT 'org_' || codice, to_regnamespace('org_' || codice) FROM organizations WHERE org_id = %s",
        (org_id,),
    ).fetchone()
    if riga is None or riga[0] is None:
        return None
    if riga[1] is None:
        raise LookupError(f"lo spazio {riga[0]} non esiste")
    return sql.Identifier(riga[0])


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
    dettagli_riservati: dict[str, Any] | None = None,
    corregge_id: int | None = None,
) -> int:
    """Scrittura di basso livello. Chi chiama ha già verificato i permessi (governance, permessi, stato_task).

    dettagli: valori strutturali, restano nel registro condiviso. dettagli_riservati: testo libero,
    nello spazio dell'organizzazione insieme alla motivazione.
    """
    if not motivazione.strip():
        raise ValueError("motivazione obbligatoria")
    dettagli = dict(dettagli or {})
    riservati = dict(dettagli_riservati or {})
    schema = spazio(conn, org_id) if org_id is not None else None
    if schema is None:
        # Atti comuni, o organizzazioni senza spazio: tutto nel registro condiviso.
        testo_pubblico, dettagli_pubblici = motivazione, {**dettagli, **riservati}
    else:
        testo_pubblico, dettagli_pubblici = MARCATORE_SPAZIO, {**dettagli, "hash_testo": hash_testo(motivazione, riservati)}
    decisione_id = conn.execute(
        """INSERT INTO registro_decisioni
             (org_id, tipo_oggetto, oggetto_id, atto, autore_id, motivazione, dettagli, corregge_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING decisione_id""",
        (org_id, tipo_oggetto, oggetto_id, atto, autore_id, testo_pubblico, Jsonb(dettagli_pubblici), corregge_id),
    ).fetchone()[0]
    if schema is not None:
        conn.execute(
            sql.SQL("INSERT INTO {}.testi_atti (decisione_id, motivazione, dettagli) VALUES (%s, %s, %s)")
            .format(schema),
            (decisione_id, motivazione, Jsonb(riservati)),
        )
    return decisione_id


def verifica_testi(conn: psycopg.Connection, org_id: str) -> list[tuple[int, str]]:
    """Atti dell'organizzazione il cui testo nello spazio manca o non corrisponde all'hash nel registro."""
    schema = spazio(conn, org_id)
    if schema is None:
        return []
    problemi = []
    for decisione_id, hash_registrato, motivazione, dettagli in conn.execute(
        sql.SQL("""SELECT r.decisione_id, r.dettagli ->> 'hash_testo', t.motivazione, t.dettagli
                   FROM registro_decisioni r LEFT JOIN {}.testi_atti t USING (decisione_id)
                   WHERE r.org_id = %s AND r.motivazione = %s ORDER BY r.posizione""").format(schema),
        (org_id, MARCATORE_SPAZIO),
    ):
        if motivazione is None:
            problemi.append((decisione_id, "testo mancante"))
        elif hash_testo(motivazione, dettagli) != hash_registrato:
            problemi.append((decisione_id, "hash diverso"))
    return problemi


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
