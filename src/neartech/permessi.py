"""Utenti, ruoli e permessi: l'unico punto in cui si decide se un'azione è consentita.

La matrice ruolo-azione sta in permessi_ruolo. Un ruolo globale vale per ogni
organizzazione; un ruolo di organizzazione solo per la propria. Ogni verifica
lascia una riga in log_accessi, consentita o negata.

La validità delle assegnazioni si valuta con statement_timestamp(), non con now() (inizio
della transazione): una revoca confermata da un'altra sessione vale subito anche per le
transazioni già aperte. I controlli dopo un lock presuppongono READ COMMITTED.

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


# Validità di un'assegnazione: una sola definizione, la funzione SQL assegnazione_valida (migrazione 0018).
_ADMIN_ATTIVI = """
    SELECT count(DISTINCT a.utente_id) FROM assegnazioni_ruolo a
    WHERE a.ruolo = 'amministratore_tecnico' AND assegnazione_valida(a)
"""
_LOCK_AMMINISTRATORI = "SELECT pg_advisory_xact_lock(hashtext('inizializza_amministratore'))"


def _canonico(identificativo: str) -> str:
    """Forma canonica di un uuid passato da chi chiama (minuscole, con trattini)."""
    return str(uuid.UUID(str(identificativo)))


def _canonico_o_none(identificativo: str | None) -> str | None:
    """Forma canonica, o None se il valore non è un uuid: a SQL arriva solo la forma canonica."""
    try:
        return _canonico(identificativo)
    except (ValueError, TypeError, AttributeError):
        return None


def configura_log(connessione: psycopg.Connection | None) -> None:
    """Connessione in autocommit dedicata al log di accesso; None torna alla connessione di chi chiama."""
    global _connessione_log
    _connessione_log = connessione


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
    utente = _canonico_o_none(utente_id)
    utente_noto = utente is not None and conn.execute(
        "SELECT EXISTS (SELECT 1 FROM utenti WHERE utente_id = %s::uuid)", (utente,)
    ).fetchone()[0]
    utente_log = utente if utente_noto else None
    org = _canonico_o_none(org_id) if org_id is not None else None
    if org_id is not None and not (org is not None and conn.execute(
        "SELECT EXISTS (SELECT 1 FROM organizations WHERE org_id = %s::uuid)", (org,)
    ).fetchone()[0]):
        # Organizzazione sconosciuta o malformata: negato, e nel log va nella risorsa.
        _scrivi_log(conn, utente_log, None, azione, f"organizzazione sconosciuta:{str(org_id)[:80]}", "negato")
        return False
    consentito = bool(utente_noto) and conn.execute(
        """SELECT EXISTS (
             SELECT 1
             FROM assegnazioni_ruolo a
             JOIN ruoli r ON r.codice = a.ruolo
             JOIN permessi_ruolo p ON p.ruolo = a.ruolo AND p.azione = %(azione)s
             WHERE a.utente_id = %(utente)s::uuid
               AND assegnazione_valida(a)
               AND (r.ambito = 'globale'
                    OR (%(org)s::uuid IS NOT NULL AND a.org_id = %(org)s::uuid)))""",
        {"azione": azione, "utente": utente, "org": org},
    ).fetchone()[0]
    _scrivi_log(conn, utente_log, org, azione, risorsa, "consentito" if consentito else "negato")
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
        conn.execute(_LOCK_AMMINISTRATORI)
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
                 dettagli={"utente_id": _canonico(utente_id), "ruolo": ruolo})
        return assegnazione


def chiudi_assegnazione(conn: psycopg.Connection, assegnazione_id: str, *, chiusa_da: str, motivazione: str) -> None:
    assegnazione_id = _canonico(assegnazione_id)
    with conn.transaction():
        ruolo = conn.execute(
            "SELECT ruolo FROM assegnazioni_ruolo WHERE assegnazione_id = %s", (assegnazione_id,)
        ).fetchone()
        if ruolo is None:
            raise LookupError(f"assegnazione {assegnazione_id} inesistente")
        if ruolo[0] == "amministratore_tecnico":
            # Lock prima del controllo del permesso: chi viene revocato mentre aspetta non chiude.
            conn.execute(_LOCK_AMMINISTRATORI)
        riga = conn.execute(
            """SELECT a.org_id, a.utente_id, assegnazione_valida(a)
               FROM assegnazioni_ruolo a WHERE a.assegnazione_id = %s FOR UPDATE""",
            (assegnazione_id,),
        ).fetchone()
        org_id = str(riga[0]) if riga[0] else None
        richiedi(conn, chiusa_da, "gestire_utenti", org_id, risorsa=f"assegnazione:{assegnazione_id}")
        if not riga[2]:
            raise LookupError(f"assegnazione {assegnazione_id} già chiusa o scaduta")
        if ruolo[0] == "amministratore_tecnico":
            altri = conn.execute(
                _ADMIN_ATTIVI + " AND a.utente_id <> %s", (riga[1],)
            ).fetchone()[0]
            if altri == 0:
                raise UltimoAmministratore("serve almeno un altro amministratore tecnico attivo")
        chiusa = conn.execute(
            """UPDATE assegnazioni_ruolo a SET valida_al = statement_timestamp(), chiusa_da = %s
               WHERE a.assegnazione_id = %s AND assegnazione_valida(a)""",
            (chiusa_da, assegnazione_id),
        ).rowcount
        if chiusa != 1:
            raise LookupError(f"assegnazione {assegnazione_id} già chiusa o scaduta")
        registra(conn, autore_id=chiusa_da, tipo_oggetto="assegnazione_ruolo", oggetto_id=str(assegnazione_id),
                 atto="ritiro", motivazione=motivazione, org_id=org_id)
