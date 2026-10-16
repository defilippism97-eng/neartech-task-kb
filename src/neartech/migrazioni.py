"""Registro e applicazione delle migrazioni.

Ogni file applicato è registrato in public.migrazioni_applicate con l'hash del contenuto
(fine riga normalizzate, così il valore non cambia tra checkout Windows e Linux).
Una migrazione registrata non si modifica: se il file cambia, la verifica si ferma.
Le migrazioni dello spazio organizzazione si applicano con search_path sullo schema
dell'organizzazione, seguito da public.
"""

import hashlib
from collections.abc import Iterable
from pathlib import Path

import psycopg
from psycopg import sql

RADICE_DB = Path(__file__).resolve().parents[2] / "db"
CARTELLA_CONDIVISA = RADICE_DB / "migrations"
CARTELLA_ORGANIZZAZIONE = RADICE_DB / "migrations_org"
SCHEMA_CONDIVISO = "public"


class MigrazioneModificata(RuntimeError):
    """Un file di migrazione già applicato è stato modificato."""


def hash_migrazione(percorso: Path) -> str:
    contenuto = percorso.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(contenuto).hexdigest()


def _registro_presente(conn: psycopg.Connection) -> bool:
    return conn.execute("SELECT to_regclass('public.migrazioni_applicate')").fetchone()[0] is not None


def _registrate(conn: psycopg.Connection, schema: str) -> dict[str, str]:
    if not _registro_presente(conn):
        return {}
    return dict(conn.execute(
        "SELECT nome, hash_sha256 FROM public.migrazioni_applicate WHERE schema_destinazione = %s",
        (schema,),
    ).fetchall())


def da_applicare(conn: psycopg.Connection, cartella: Path, schema: str = SCHEMA_CONDIVISO) -> list[Path]:
    """Elenca i file non ancora registrati. Sola lettura."""
    registrate = _registrate(conn, schema)
    file = sorted(cartella.glob("*.sql"))
    for percorso in file:
        atteso = registrate.get(percorso.name)
        if atteso is not None and atteso != hash_migrazione(percorso):
            raise MigrazioneModificata(f"{percorso.name} è cambiata dopo l'applicazione in {schema}")
    return [p for p in file if p.name not in registrate]


def registra_senza_eseguire(
    conn: psycopg.Connection, percorsi: Iterable[Path], schema: str = SCHEMA_CONDIVISO
) -> None:
    """Registra migrazioni già applicate a mano, senza eseguirle."""
    for percorso in percorsi:
        conn.execute(
            """INSERT INTO public.migrazioni_applicate (schema_destinazione, nome, hash_sha256)
               VALUES (%s, %s, %s)""",
            (schema, percorso.name, hash_migrazione(percorso)),
        )


def applica(conn: psycopg.Connection, cartella: Path, schema: str = SCHEMA_CONDIVISO) -> list[Path]:
    """Applica in ordine i file non registrati, ciascuno nella propria transazione."""
    eseguite: list[Path] = []
    in_attesa: list[Path] = []
    for percorso in da_applicare(conn, cartella, schema):
        with conn.transaction():
            precedente = conn.execute("SELECT current_setting('search_path')").fetchone()[0]
            if schema != SCHEMA_CONDIVISO:
                percorso_ricerca = sql.SQL("{}, public").format(sql.Identifier(schema)).as_string(conn)
                conn.execute("SELECT set_config('search_path', %s, true)", (percorso_ricerca,))
            conn.execute(percorso.read_text(encoding="utf-8"))
            conn.execute("SELECT set_config('search_path', %s, true)", (precedente,))
            in_attesa.append(percorso)
            # Le migrazioni che precedono la creazione del registro vengono registrate appena esiste.
            if _registro_presente(conn):
                registra_senza_eseguire(conn, in_attesa, schema)
                in_attesa.clear()
        eseguite.append(percorso)
    return eseguite
