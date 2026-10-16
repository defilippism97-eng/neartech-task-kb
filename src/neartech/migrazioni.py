"""Registro e applicazione delle migrazioni.

Ogni file applicato è registrato in public.migrazioni_applicate con l'hash del contenuto
(fine riga normalizzate, così il valore non cambia tra checkout Windows e Linux).
Una migrazione registrata non si modifica: se il file cambia, la verifica si ferma.
Le migrazioni dello spazio organizzazione si applicano con search_path sullo schema
dell'organizzazione, seguito da public.

Un database migrato a mano prima del registro (produzione: 0002-0006) si allinea con
inizializza_registro, che crea il registro e vi segna le migrazioni indicate.
"""

import hashlib
import re
from collections.abc import Iterable
from pathlib import Path

import psycopg
from psycopg import sql

RADICE_DB = Path(__file__).resolve().parents[2] / "db"
CARTELLA_CONDIVISA = RADICE_DB / "migrations"
CARTELLA_ORGANIZZAZIONE = RADICE_DB / "migrations_org"
SCHEMA_CONDIVISO = "public"
MIGRAZIONE_REGISTRO = "0007_registro_migrazioni.sql"

_NOME = re.compile(r"^\d{4}_[a-z0-9_]+\.sql$")
# Chiave del lock di sessione che impedisce due applicazioni contemporanee.
_LOCK_MIGRAZIONI = 7_301_142


class MigrazioneModificata(RuntimeError):
    """Un file di migrazione già applicato è stato modificato."""


class SchemaAssente(LookupError):
    """Lo schema di destinazione non esiste: gli oggetti finirebbero in public."""


def hash_migrazione(percorso: Path) -> str:
    contenuto = percorso.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(contenuto).hexdigest()


def percorso_migrazione(nome: str, cartella: Path = CARTELLA_CONDIVISA) -> Path:
    """Percorso di una migrazione esistente, dato il solo nome del file."""
    if not _NOME.fullmatch(nome):
        raise ValueError(f"nome di migrazione non valido: {nome!r}")
    percorso = cartella / nome
    if not percorso.is_file():
        raise ValueError(f"migrazione inesistente: {nome}")
    return percorso


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
    """Registra migrazioni già applicate, senza eseguirle. Il registro deve esistere."""
    for percorso in percorsi:
        conn.execute(
            """INSERT INTO public.migrazioni_applicate (schema_destinazione, nome, hash_sha256)
               VALUES (%s, %s, %s)""",
            (schema, percorso.name, hash_migrazione(percorso)),
        )


def inizializza_registro(conn: psycopg.Connection, gia_applicate: Iterable[str]) -> None:
    """Crea il registro (0007) su un database migrato a mano e vi segna le migrazioni indicate."""
    nomi = list(gia_applicate)
    successive = [nome for nome in nomi if nome >= MIGRAZIONE_REGISTRO]
    if successive:
        raise ValueError(f"solo migrazioni precedenti al registro: {', '.join(successive)}")
    percorsi = [percorso_migrazione(nome) for nome in nomi]
    registro = percorso_migrazione(MIGRAZIONE_REGISTRO)
    with conn.transaction():
        if _registro_presente(conn):
            raise RuntimeError("il registro delle migrazioni esiste già")
        conn.execute(registro.read_text(encoding="utf-8"))
        registra_senza_eseguire(conn, [*percorsi, registro])


def applica(conn: psycopg.Connection, cartella: Path, schema: str = SCHEMA_CONDIVISO) -> list[Path]:
    """Applica in ordine i file non registrati.

    Ogni file gira in conn.transaction(): una transazione propria se la connessione è in
    autocommit, un savepoint se chi chiama ha già una transazione aperta (in quel caso
    il commit finale è di chi chiama). Un lock impedisce due applicazioni contemporanee
    sullo stesso database: di transazione se chi chiama ne ha una aperta, altrimenti di
    sessione, rilasciato alla fine. Uno schema di organizzazione deve esistere.
    """
    if schema != SCHEMA_CONDIVISO and conn.execute(
        "SELECT to_regnamespace(%s)", (schema,)
    ).fetchone()[0] is None:
        raise SchemaAssente(f"lo schema {schema} non esiste")
    eseguite: list[Path] = []
    if conn.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS:
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK_MIGRAZIONI,))
        _applica_in_ordine(conn, cartella, schema, eseguite)
        return eseguite
    conn.execute("SELECT pg_advisory_lock(%s)", (_LOCK_MIGRAZIONI,))
    try:
        _applica_in_ordine(conn, cartella, schema, eseguite)
    finally:
        # Con la transazione in errore il lock si libera alla chiusura della connessione.
        if conn.info.transaction_status != psycopg.pq.TransactionStatus.INERROR:
            conn.execute("SELECT pg_advisory_unlock(%s)", (_LOCK_MIGRAZIONI,))
    return eseguite


def _applica_in_ordine(conn: psycopg.Connection, cartella: Path, schema: str, eseguite: list[Path]) -> None:
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
