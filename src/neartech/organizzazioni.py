"""Organizzazioni e loro spazio (ADR 0001).

Ogni organizzazione ha uno schema org_<codice> con il testo del cliente; il dataset
condiviso resta in public. Il codice è validato prima di arrivare al database, perché
diventa il nome di uno schema, e si assegna una sola volta (trigger della migrazione 0015).
Lo spazio si crea solo da funzioni che verificano i permessi: crea_organizzazione e
neartech.spostamento.sposta_testo_cliente.
"""

import re

import psycopg
from psycopg import sql

from neartech.migrazioni import CARTELLA_ORGANIZZAZIONE, applica
from neartech.permessi import richiedi
from neartech.registro import registra

_CODICE = re.compile(r"^[a-z][a-z0-9_]{1,40}$")


class CodiceNonValido(ValueError):
    """Il codice dell'organizzazione non rispetta il formato ammesso."""


def schema_organizzazione(codice: str) -> str:
    if not _CODICE.fullmatch(codice):
        raise CodiceNonValido(f"codice non valido: {codice!r}")
    return f"org_{codice}"


def crea_organizzazione(
    conn: psycopg.Connection, utente_id: str, *, nome: str, codice: str, settore: str | None = None
) -> str:
    schema_organizzazione(codice)
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_organizzazioni", risorsa=f"organizzazione:{codice}")
        org_id = str(conn.execute(
            "INSERT INTO organizations (name, sector) VALUES (%s, %s) RETURNING org_id", (nome, settore)
        ).fetchone()[0])
        _crea_spazio(conn, org_id, codice)
        registra(conn, autore_id=utente_id, tipo_oggetto="organizzazione", oggetto_id=org_id,
                 atto="approvazione", motivazione="creazione dell'organizzazione e del suo spazio",
                 org_id=org_id, dettagli={"codice": codice})
        return org_id


def _crea_spazio(conn: psycopg.Connection, org_id: str, codice: str) -> str:
    """Assegna il codice a un'organizzazione che non ne ha uno e crea il suo schema.

    Interna: chi chiama ha già verificato i permessi e ha una transazione aperta.
    """
    schema = schema_organizzazione(codice)
    riga = conn.execute("SELECT codice FROM organizations WHERE org_id = %s FOR UPDATE", (org_id,)).fetchone()
    if riga is None:
        raise LookupError(f"organizzazione {org_id} inesistente")
    if riga[0] is not None:
        raise ValueError(f"l'organizzazione ha già lo spazio org_{riga[0]}")
    conn.execute("UPDATE organizations SET codice = %s WHERE org_id = %s AND codice IS NULL", (codice, org_id))
    conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    applica(conn, CARTELLA_ORGANIZZAZIONE, schema)
    return schema


def aggiorna_spazi(conn: psycopg.Connection) -> dict[str, list[str]]:
    """Applica a ogni spazio esistente le migrazioni di organizzazione mancanti.

    Operazione di manutenzione dello schema, come scripts/migra.py: la esegue chi gestisce
    le migrazioni con il ruolo di database proprietario, non un utente dell'applicazione.
    Gli spazi rimossi (uscita del cliente) non hanno più lo schema e vengono saltati.
    """
    esito: dict[str, list[str]] = {}
    for (codice,) in conn.execute(
        "SELECT codice FROM organizations WHERE codice IS NOT NULL ORDER BY codice"
    ).fetchall():
        schema = schema_organizzazione(codice)
        if conn.execute("SELECT to_regnamespace(%s)", (schema,)).fetchone()[0] is None:
            continue
        esito[schema] = [p.name for p in applica(conn, CARTELLA_ORGANIZZAZIONE, schema)]
    return esito
