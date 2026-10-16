"""Utenti, ruoli e permessi: l'unico punto in cui si decide se un'azione è consentita.

La matrice ruolo-azione sta in permessi_ruolo. Un ruolo globale vale per ogni
organizzazione; un ruolo di organizzazione solo per la propria. Ogni verifica
lascia una riga in log_accessi, consentita o negata.

Il log dei rifiuti deve sopravvivere all'annullamento della transazione di chi chiama:
il livello che serve le richieste (API, script) configura una connessione dedicata in
autocommit con configura_log. Senza configurazione il log usa la connessione di chi
chiama, e un rollback lo annulla insieme al resto.
"""

import uuid
from datetime import datetime

import psycopg

from neartech.registro import registra

_connessione_log: psycopg.Connection | None = None


class PermessoNegato(PermissionError):
    """L'utente non ha un ruolo valido che consenta l'azione."""


class AmministratoreGiaPresente(RuntimeError):
    """Esiste già un amministratore tecnico attivo: il bootstrap non si ripete."""


class UltimoAmministratore(RuntimeError):
    """Chiudere l'assegnazione lascerebbe il sistema senza amministratore tecnico."""


_ADMIN_ATTIVI = """
    SELECT count(DISTINCT utente_id) FROM assegnazioni_ruolo
    WHERE ruolo = 'amministratore_tecnico' AND valida_dal <= now()
      AND (valida_al IS NULL OR valida_al > now())
"""


def _canonico(identificativo: str) -> str:
    """Forma canonica di un uuid passato da chi chiama (minuscole, con trattini)."""
    return str(uuid.UUID(str(identificativo)))


def configura_log(connessione: psycopg.Connection | None) -> None:
    """Connessione in autocommit dedicata al log di accesso; None torna alla connessione di chi chiama."""
    global _connessione_log
    _connessione_log = connessione


def _uuid_valido(valore: str) -> bool:
    try:
        uuid.UUID(str(valore))
    except ValueError:
        return False
    return True


def _scrivi_log(
    conn: psycopg.Connection, utente_id: str | None, org_id: str | None, azione: str, risorsa: str | None, esito: str
) -> None:
    (_connessione_log or conn).execute(
        """INSERT INTO log_accessi (utente_id, org_id, azione, risorsa, esito)
           VALUES (%s, %s, %s, %s, %s)""",
        (utente_id, org_id, azione, risorsa, esito),
    )


def crea_utente(conn: psycopg.Connection, soggetto_sso: str) -> str:
    """Crea l'utente senza alcun ruolo: da solo non conferisce permessi."""
    return str(conn.execute(
        "INSERT INTO utenti (soggetto_sso) VALUES (%s) RETURNING utente_id", (soggetto_sso,)
    ).fetchone()[0])


def puo(
    conn: psycopg.Connection,
    utente_id: str,
    azione: str,
    org_id: str | None = None,
    risorsa: str | None = None,
) -> bool:
    utente_noto = _uuid_valido(utente_id) and conn.execute(
        "SELECT EXISTS (SELECT 1 FROM utenti WHERE utente_id = %s::uuid)", (str(utente_id),)
    ).fetchone()[0]
    if org_id is not None and not (_uuid_valido(org_id) and conn.execute(
        "SELECT EXISTS (SELECT 1 FROM organizations WHERE org_id = %s::uuid)", (str(org_id),)
    ).fetchone()[0]):
        # Organizzazione sconosciuta: negato, e nel log va nella risorsa, non nella chiave esterna.
        _scrivi_log(conn, str(utente_id) if utente_noto else None, None, azione,
                    f"organizzazione sconosciuta:{org_id}", "negato")
        return False
    consentito = bool(utente_noto) and conn.execute(
        """SELECT EXISTS (
             SELECT 1
             FROM assegnazioni_ruolo a
             JOIN ruoli r ON r.codice = a.ruolo
             JOIN permessi_ruolo p ON p.ruolo = a.ruolo AND p.azione = %(azione)s
             WHERE a.utente_id = %(utente)s::uuid
               AND a.valida_dal <= now()
               AND (a.valida_al IS NULL OR a.valida_al > now())
               AND (r.ambito = 'globale'
                    OR (%(org)s::uuid IS NOT NULL AND a.org_id = %(org)s::uuid)))""",
        {"azione": azione, "utente": str(utente_id), "org": org_id},
    ).fetchone()[0]
    _scrivi_log(conn, str(utente_id) if utente_noto else None, org_id, azione, risorsa,
                "consentito" if consentito else "negato")
    return consentito


def richiedi(
    conn: psycopg.Connection,
    utente_id: str,
    azione: str,
    org_id: str | None = None,
    risorsa: str | None = None,
) -> None:
    if not puo(conn, utente_id, azione, org_id, risorsa):
        raise PermessoNegato(f"azione '{azione}' non consentita")


def inizializza_amministratore(conn: psycopg.Connection, soggetto_sso: str) -> str:
    """Primo amministratore tecnico, senza chi lo concede. Ammesso solo se non ce n'è uno attivo."""
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('inizializza_amministratore'))")
        if conn.execute(_ADMIN_ATTIVI).fetchone()[0] > 0:
            raise AmministratoreGiaPresente("esiste già un amministratore tecnico attivo")
        utente_id = crea_utente(conn, soggetto_sso)
        assegnazione = str(conn.execute(
            """INSERT INTO assegnazioni_ruolo (utente_id, ruolo) VALUES (%s, 'amministratore_tecnico')
               RETURNING assegnazione_id""",
            (utente_id,),
        ).fetchone()[0])
        registra(conn, autore_id=utente_id, tipo_oggetto="assegnazione_ruolo", oggetto_id=assegnazione,
                 atto="approvazione", motivazione="amministratore tecnico iniziale",
                 dettagli={"utente_id": utente_id, "ruolo": "amministratore_tecnico"})
        return utente_id


def assegna_ruolo(
    conn: psycopg.Connection,
    utente_id: str,
    ruolo: str,
    org_id: str | None = None,
    *,
    assegnata_da: str,
    valida_al: datetime | None = None,
    motivazione: str = "assegnazione di ruolo",
) -> str:
    if ruolo == "amministratore_tecnico" and valida_al is not None:
        raise ValueError("l'amministratore tecnico non si assegna a termine")
    org_id = _canonico(org_id) if org_id is not None else None
    with conn.transaction():
        richiedi(conn, assegnata_da, "gestire_utenti", org_id, risorsa=f"ruolo:{ruolo}")
        assegnazione = str(conn.execute(
            """INSERT INTO assegnazioni_ruolo (utente_id, ruolo, org_id, assegnata_da, valida_al)
               VALUES (%s, %s, %s, %s, %s) RETURNING assegnazione_id""",
            (utente_id, ruolo, org_id, assegnata_da, valida_al),
        ).fetchone()[0])
        registra(conn, autore_id=assegnata_da, tipo_oggetto="assegnazione_ruolo", oggetto_id=assegnazione,
                 atto="approvazione", motivazione=motivazione, org_id=org_id,
                 dettagli={"utente_id": str(utente_id), "ruolo": ruolo})
        return assegnazione


def chiudi_assegnazione(conn: psycopg.Connection, assegnazione_id: str, *, chiusa_da: str, motivazione: str) -> None:
    assegnazione_id = _canonico(assegnazione_id)
    with conn.transaction():
        riga = conn.execute(
            """SELECT org_id, ruolo, utente_id,
                      chiusa_da IS NULL AND (valida_al IS NULL OR valida_al > now()) AS valida
               FROM assegnazioni_ruolo WHERE assegnazione_id = %s""",
            (assegnazione_id,),
        ).fetchone()
        if riga is None:
            raise LookupError(f"assegnazione {assegnazione_id} inesistente")
        org_id = str(riga[0]) if riga[0] else None
        richiedi(conn, chiusa_da, "gestire_utenti", org_id, risorsa=f"assegnazione:{assegnazione_id}")
        if not riga[3]:
            raise LookupError(f"assegnazione {assegnazione_id} già chiusa o scaduta")
        if riga[1] == "amministratore_tecnico":
            # Stesso lock del bootstrap: due chiusure contemporanee non lasciano il sistema senza amministratore.
            # Gli amministratori non hanno scadenza (migrazione 0016): conta chi resta, persona per persona.
            conn.execute("SELECT pg_advisory_xact_lock(hashtext('inizializza_amministratore'))")
            altri = conn.execute(
                _ADMIN_ATTIVI + " AND utente_id <> %s", (riga[2],)
            ).fetchone()[0]
            if altri == 0:
                raise UltimoAmministratore("serve almeno un altro amministratore tecnico attivo")
        chiusa = conn.execute(
            """UPDATE assegnazioni_ruolo SET valida_al = now(), chiusa_da = %s
               WHERE assegnazione_id = %s AND chiusa_da IS NULL AND (valida_al IS NULL OR valida_al > now())""",
            (chiusa_da, assegnazione_id),
        ).rowcount
        if chiusa != 1:
            raise LookupError(f"assegnazione {assegnazione_id} già chiusa o scaduta")
        registra(conn, autore_id=chiusa_da, tipo_oggetto="assegnazione_ruolo", oggetto_id=str(assegnazione_id),
                 atto="ritiro", motivazione=motivazione, org_id=org_id)
