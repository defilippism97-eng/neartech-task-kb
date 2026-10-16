"""Parametri di governance, indirizzi del comitato guida e segnalazioni dei revisori.

Ogni proposta e ogni decisione passa da neartech.permessi e lascia un atto nel
registro. Le versioni non si modificano; lo stato si ricava dal registro.
Nessun valore di default nel codice: un parametro non approvato non esiste.

Ritiro: ritirare la versione vigente lascia il parametro senza valore. Non si torna
alla versione precedente né al valore comune NEARTECH: serve una decisione nuova.
"""

import hashlib
import uuid
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from neartech.permessi import richiedi
from neartech.registro import registra


class ParametroAssente(LookupError):
    """Nessuna versione approvata e vigente per il parametro."""


class ParametroRitirato(ParametroAssente):
    """L'organizzazione ha ritirato la versione vigente e non ne ha approvata una nuova."""


class DecisioneGiaPresa(RuntimeError):
    """La versione è già stata approvata o rifiutata, o non si può ritirare."""


@dataclass(frozen=True)
class Parametro:
    parametro_id: str
    codice: str
    org_id: str | None
    versione: int
    valore: Any
    approvazione_id: int


@dataclass(frozen=True)
class Indirizzo:
    indirizzo_id: str
    org_id: str
    codice: str
    versione: int
    testo: str
    ambito: str
    approvazione_id: int


# Tipo di oggetto nel registro -> (tabella, colonna chiave, permesso per decidere)
_OGGETTI = {
    "parametro": ("parametri_governance", "parametro_id", "approvare_parametro"),
    "indirizzo": ("indirizzi_comitato", "indirizzo_id", "approvare_indirizzo"),
}

# Separatore fra testo e ambito nell'hash del contenuto di un indirizzo (stesso valore in verifica_contenuti).
_SEPARATORE = "\x1f"


def _hash_indirizzo(testo: str, ambito: str) -> str:
    return hashlib.sha256(f"{testo}{_SEPARATORE}{ambito}".encode()).hexdigest()


def _blocca(conn: psycopg.Connection, chiave: str) -> None:
    conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (chiave,))


def _prossima_versione(conn: psycopg.Connection, tabella: str, codice: str, org_id: str | None) -> int:
    _blocca(conn, f"versione:{tabella}:{codice}:{org_id}")
    return conn.execute(
        sql.SQL("SELECT COALESCE(max(versione), 0) + 1 FROM {} WHERE codice = %s AND org_id IS NOT DISTINCT FROM %s")
        .format(sql.Identifier(tabella)),
        (codice, org_id),
    ).fetchone()[0]


def _decidi(
    conn: psycopg.Connection, utente_id: str, tipo: str, oggetto_id: str, atto: str, motivazione: str
) -> int:
    tabella, chiave, permesso = _OGGETTI[tipo]
    oggetto_id = str(uuid.UUID(str(oggetto_id)))
    with conn.transaction():
        riga = conn.execute(
            sql.SQL("SELECT org_id, codice, versione FROM {} WHERE {} = %s")
            .format(sql.Identifier(tabella), sql.Identifier(chiave)),
            (oggetto_id,),
        ).fetchone()
        if riga is None:
            raise LookupError(f"{tipo} {oggetto_id} inesistente")
        org_id = str(riga[0]) if riga[0] is not None else None
        codice, versione = riga[1], riga[2]
        if tipo == "parametro" and org_id is None:
            permesso = "approvare_parametro_comune"  # parametri NEARTECH comuni: metodologia, sezione 9
        richiedi(conn, utente_id, permesso, org_id, risorsa=f"{tipo}:{oggetto_id}")
        _blocca(conn, f"decisione:{tipo}:{oggetto_id}")
        if atto == "approvazione":
            # Lo stesso lock delle nuove versioni: nessuna versione nuova si inserisce durante il controllo.
            _blocca(conn, f"versione:{tabella}:{codice}:{org_id}")
            superata = conn.execute(
                sql.SQL("""SELECT EXISTS (
                             SELECT 1 FROM {} t JOIN stato_oggetti_governance s
                               ON s.tipo_oggetto = %s AND s.oggetto_id = t.{}::text
                             WHERE t.codice = %s AND t.org_id IS NOT DISTINCT FROM %s AND t.versione > %s
                               AND s.ultimo_atto IN ('approvazione', 'ritiro'))""")
                .format(sql.Identifier(tabella), sql.Identifier(chiave)),
                (tipo, codice, org_id, versione),
            ).fetchone()[0]
            if superata:
                raise DecisioneGiaPresa(f"{tipo} {oggetto_id}: esiste una versione successiva già decisa")
        ultimo = conn.execute(
            "SELECT ultimo_atto FROM stato_oggetti_governance WHERE tipo_oggetto = %s AND oggetto_id = %s",
            (tipo, str(oggetto_id)),
        ).fetchone()
        ultimo_atto = ultimo[0] if ultimo else None
        if atto in ("approvazione", "rifiuto") and ultimo_atto is not None:
            raise DecisioneGiaPresa(f"{tipo} {oggetto_id}: già {ultimo_atto}")
        if atto == "ritiro" and ultimo_atto != "approvazione":
            raise DecisioneGiaPresa(f"{tipo} {oggetto_id}: si ritira solo una versione approvata")
        return registra(conn, autore_id=utente_id, tipo_oggetto=tipo, oggetto_id=str(oggetto_id),
                        atto=atto, motivazione=motivazione, org_id=org_id)


# --- parametri -------------------------------------------------------------------

def proponi_parametro(
    conn: psycopg.Connection,
    utente_id: str,
    *,
    codice: str,
    valore: Any,
    descrizione: str,
    motivazione: str,
    org_id: str | None,
) -> str:
    org_id = str(uuid.UUID(str(org_id))) if org_id is not None else None
    with conn.transaction():
        azione = "proporre_parametro_comune" if org_id is None else "proporre_parametro"
        richiedi(conn, utente_id, azione, org_id, risorsa=f"parametro:{codice}")
        parametro_id = str(uuid.uuid4())
        versione = _prossima_versione(conn, "parametri_governance", codice, org_id)
        proposta = registra(
            conn, autore_id=utente_id, tipo_oggetto="parametro", oggetto_id=parametro_id, atto="proposta",
            motivazione=motivazione, org_id=org_id,
            dettagli={"codice": codice, "versione": versione, "valore": valore},
        )
        conn.execute(
            """INSERT INTO parametri_governance
                 (parametro_id, codice, org_id, versione, valore, descrizione, proposta_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (parametro_id, codice, org_id, versione, Jsonb(valore), descrizione, proposta),
        )
        return parametro_id


def approva_parametro(conn: psycopg.Connection, utente_id: str, parametro_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "parametro", parametro_id, "approvazione", motivazione)


def rifiuta_parametro(conn: psycopg.Connection, utente_id: str, parametro_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "parametro", parametro_id, "rifiuto", motivazione)


def ritira_parametro(conn: psycopg.Connection, utente_id: str, parametro_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "parametro", parametro_id, "ritiro", motivazione)



def parametro_vigente(conn: psycopg.Connection, codice: str, org_id: str | None) -> Parametro:
    """Versione vigente per l'organizzazione; se l'organizzazione non ne ha mai decisa una, quella comune.

    Una sola query: la scelta fra valore proprio, ritiro e valore comune vede un'unica fotografia.
    """
    riga = conn.execute(
        """WITH proprio AS (
             SELECT parametro_id, codice, org_id, versione, valore, approvazione_id
             FROM parametri_vigenti WHERE codice = %(codice)s AND org_id = %(org)s::uuid
           ), deciso_proprio AS (
             SELECT 1 FROM parametri_governance p
             JOIN stato_oggetti_governance s
               ON s.tipo_oggetto = 'parametro' AND s.oggetto_id = p.parametro_id::text
             WHERE p.codice = %(codice)s AND p.org_id = %(org)s::uuid
               AND s.ultimo_atto IN ('approvazione', 'ritiro')
           ), comune AS (
             SELECT parametro_id, codice, org_id, versione, valore, approvazione_id
             FROM parametri_vigenti WHERE codice = %(codice)s AND org_id IS NULL
           )
           SELECT 'proprio', * FROM proprio
           UNION ALL
           SELECT 'ritirato', NULL, NULL, NULL, NULL, NULL, NULL
           WHERE NOT EXISTS (SELECT 1 FROM proprio) AND EXISTS (SELECT 1 FROM deciso_proprio)
           UNION ALL
           SELECT 'comune', * FROM comune
           WHERE NOT EXISTS (SELECT 1 FROM proprio) AND NOT EXISTS (SELECT 1 FROM deciso_proprio)""",
        {"codice": codice, "org": org_id},
    ).fetchone()
    if riga is None:
        raise ParametroAssente(f"nessun valore approvato per '{codice}'")
    if riga[0] == "ritirato":
        raise ParametroRitirato(f"'{codice}' ritirato dall'organizzazione, nessuna versione nuova approvata")
    return Parametro(str(riga[1]), riga[2], str(riga[3]) if riga[3] else None, riga[4], riga[5], riga[6])


# --- indirizzi del comitato -------------------------------------------------------

def proponi_indirizzo(
    conn: psycopg.Connection,
    utente_id: str,
    *,
    org_id: str,
    codice: str,
    testo: str,
    ambito: str,
    motivazione: str,
) -> str:
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "proporre_indirizzo", org_id, risorsa=f"indirizzo:{codice}")
        indirizzo_id = str(uuid.uuid4())
        versione = _prossima_versione(conn, "indirizzi_comitato", codice, org_id)
        proposta = registra(
            conn, autore_id=utente_id, tipo_oggetto="indirizzo", oggetto_id=indirizzo_id, atto="proposta",
            motivazione=motivazione, org_id=org_id,
            dettagli={"codice": codice, "versione": versione, "hash_contenuto": _hash_indirizzo(testo, ambito)},
        )
        conn.execute(
            """INSERT INTO indirizzi_comitato (indirizzo_id, org_id, codice, versione, testo, ambito, proposta_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (indirizzo_id, org_id, codice, versione, testo, ambito, proposta),
        )
        return indirizzo_id


def approva_indirizzo(conn: psycopg.Connection, utente_id: str, indirizzo_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "indirizzo", indirizzo_id, "approvazione", motivazione)


def rifiuta_indirizzo(conn: psycopg.Connection, utente_id: str, indirizzo_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "indirizzo", indirizzo_id, "rifiuto", motivazione)


def ritira_indirizzo(conn: psycopg.Connection, utente_id: str, indirizzo_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "indirizzo", indirizzo_id, "ritiro", motivazione)


def indirizzi_vigenti(conn: psycopg.Connection, org_id: str) -> list[Indirizzo]:
    return [
        Indirizzo(str(r[0]), str(r[1]), r[2], r[3], r[4], r[5], r[6])
        for r in conn.execute(
            """SELECT indirizzo_id, org_id, codice, versione, testo, ambito, approvazione_id
               FROM indirizzi_vigenti WHERE org_id = %s ORDER BY codice""",
            (org_id,),
        )
    ]


def verifica_contenuti(conn: psycopg.Connection) -> list[tuple[str, str]]:
    """Confronta parametri e indirizzi con quanto registrato nella loro proposta. Restituisce le discordanze."""
    return [
        (r[0], str(r[1]))
        for r in conn.execute(
            """SELECT 'parametro', p.parametro_id
               FROM parametri_governance p JOIN registro_decisioni r ON r.decisione_id = p.proposta_id
               WHERE r.dettagli -> 'valore' IS DISTINCT FROM p.valore
                  OR r.org_id IS DISTINCT FROM p.org_id
                  OR r.dettagli ->> 'codice' IS DISTINCT FROM p.codice
                  OR (r.dettagli ->> 'versione')::int IS DISTINCT FROM p.versione
               UNION ALL
               SELECT 'indirizzo', i.indirizzo_id
               FROM indirizzi_comitato i JOIN registro_decisioni r ON r.decisione_id = i.proposta_id
               WHERE r.dettagli ->> 'hash_contenuto' IS DISTINCT FROM
                     encode(sha256(convert_to(i.testo || chr(31) || i.ambito, 'UTF8')), 'hex')
                  OR r.org_id IS DISTINCT FROM i.org_id
                  OR r.dettagli ->> 'codice' IS DISTINCT FROM i.codice
                  OR (r.dettagli ->> 'versione')::int IS DISTINCT FROM i.versione
               ORDER BY 1, 2"""
        )
    ]


# --- segnalazioni dei revisori ---------------------------------------------------

def segnala(
    conn: psycopg.Connection,
    utente_id: str,
    *,
    org_id: str,
    tipo_oggetto: str,
    oggetto_id: str,
    motivazione: str,
    dettagli: dict[str, Any] | None = None,
) -> int:
    """Segnalazione di un revisore, visibile a comitato guida, auditor e rappresentanti.

    Per parametri e indirizzi l'oggetto deve appartenere all'organizzazione del revisore.
    I dettagli stanno nello schema condiviso: mai testo del cliente (ADR 0001).
    """
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "segnalare", org_id, risorsa=f"{tipo_oggetto}:{oggetto_id}")
        if tipo_oggetto in _OGGETTI:
            oggetto_id = str(uuid.UUID(str(oggetto_id)))
            tabella, chiave, _ = _OGGETTI[tipo_oggetto]
            proprio = conn.execute(
                sql.SQL("SELECT EXISTS (SELECT 1 FROM {} WHERE {}::text = %s AND org_id = %s)")
                .format(sql.Identifier(tabella), sql.Identifier(chiave)),
                (str(oggetto_id), org_id),
            ).fetchone()[0]
            if not proprio:
                raise LookupError(f"{tipo_oggetto} {oggetto_id} non appartiene all'organizzazione")
        return registra(conn, autore_id=utente_id, tipo_oggetto=tipo_oggetto, oggetto_id=str(oggetto_id),
                        atto="segnalazione", motivazione=motivazione, org_id=org_id, dettagli=dettagli)
