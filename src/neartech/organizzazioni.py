"""Organizzazioni e loro spazio (ADR 0001).

Ogni organizzazione ha uno schema org_<codice> con il testo del cliente; il dataset
condiviso resta in public. Il codice è validato prima di arrivare al database, perché
diventa il nome di uno schema.
"""

import re

import psycopg
from psycopg import sql

from neartech.migrazioni import CARTELLA_ORGANIZZAZIONE, applica
from neartech.permessi import richiedi

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
        crea_spazio(conn, org_id, codice)
        return org_id


def crea_spazio(conn: psycopg.Connection, org_id: str, codice: str) -> str:
    """Assegna il codice a un'organizzazione esistente e crea il suo schema. Chi chiama verifica i permessi."""
    schema = schema_organizzazione(codice)
    conn.execute("UPDATE organizations SET codice = %s WHERE org_id = %s", (codice, org_id))
    conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    applica(conn, CARTELLA_ORGANIZZAZIONE, schema)
    return schema


def aggiorna_spazi(conn: psycopg.Connection) -> dict[str, list[str]]:
    """Applica a ogni spazio le migrazioni di organizzazione mancanti.

    Operazione di manutenzione dello schema, come scripts/migra.py: la esegue chi gestisce
    le migrazioni con il ruolo di database proprietario, non un utente dell'applicazione.
    """
    esito: dict[str, list[str]] = {}
    for (codice,) in conn.execute(
        "SELECT codice FROM organizations WHERE codice IS NOT NULL ORDER BY codice"
    ).fetchall():
        schema = schema_organizzazione(codice)
        esito[schema] = [p.name for p in applica(conn, CARTELLA_ORGANIZZAZIONE, schema)]
    return esito
