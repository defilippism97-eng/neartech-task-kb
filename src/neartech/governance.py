"""Parametri di governance, indirizzi del comitato guida e segnalazioni dei revisori.

Ogni proposta e ogni decisione passa da neartech.permessi e lascia un atto nel
registro. Le versioni non si modificano; lo stato si ricava dal registro.
Nessun valore di default nel codice: un parametro non approvato non esiste.
"""

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


def _prossima_versione(conn: psycopg.Connection, tabella: str, codice: str, org_id: str | None) -> int:
    return conn.execute(
        sql.SQL("SELECT COALESCE(max(versione), 0) + 1 FROM {} WHERE codice = %s AND org_id IS NOT DISTINCT FROM %s")
        .format(sql.Identifier(tabella)),
        (codice, org_id),
    ).fetchone()[0]


def _decidi(
    conn: psycopg.Connection, utente_id: str, tipo: str, oggetto_id: str, atto: str, motivazione: str
) -> int:
    tabella, chiave, permesso = _OGGETTI[tipo]
    riga = conn.execute(
        sql.SQL("SELECT org_id FROM {} WHERE {} = %s").format(sql.Identifier(tabella), sql.Identifier(chiave)),
        (oggetto_id,),
    ).fetchone()
    if riga is None:
        raise LookupError(f"{tipo} {oggetto_id} inesistente")
    org_id = str(riga[0]) if riga[0] is not None else None
    richiedi(conn, utente_id, permesso, org_id, risorsa=f"{tipo}:{oggetto_id}")
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
    richiedi(conn, utente_id, "proporre_parametro", org_id, risorsa=f"parametro:{codice}")
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
    """Versione vigente per l'organizzazione; in mancanza, quella NEARTECH comune."""
    for org in ([org_id, None] if org_id is not None else [None]):
        riga = conn.execute(
            """SELECT parametro_id, codice, org_id, versione, valore, approvazione_id
               FROM parametri_vigenti WHERE codice = %s AND org_id IS NOT DISTINCT FROM %s""",
            (codice, org),
        ).fetchone()
        if riga is not None:
            return Parametro(str(riga[0]), riga[1], str(riga[2]) if riga[2] else None, riga[3], riga[4], riga[5])
    raise ParametroAssente(f"nessun valore approvato per '{codice}'")


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
    richiedi(conn, utente_id, "proporre_indirizzo", org_id, risorsa=f"indirizzo:{codice}")
    indirizzo_id = str(uuid.uuid4())
    versione = _prossima_versione(conn, "indirizzi_comitato", codice, org_id)
    proposta = registra(
        conn, autore_id=utente_id, tipo_oggetto="indirizzo", oggetto_id=indirizzo_id, atto="proposta",
        motivazione=motivazione, org_id=org_id, dettagli={"codice": codice, "versione": versione},
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
    """Segnalazione di un revisore, visibile a comitato guida, auditor e rappresentanti."""
    richiedi(conn, utente_id, "segnalare", org_id, risorsa=f"{tipo_oggetto}:{oggetto_id}")
    return registra(conn, autore_id=utente_id, tipo_oggetto=tipo_oggetto, oggetto_id=str(oggetto_id),
                    atto="segnalazione", motivazione=motivazione, org_id=org_id, dettagli=dettagli)
