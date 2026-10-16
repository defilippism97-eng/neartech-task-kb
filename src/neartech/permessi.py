"""Utenti, ruoli e permessi: l'unico punto in cui si decide se un'azione è consentita.

La matrice ruolo-azione sta in permessi_ruolo. Un ruolo globale vale per ogni
organizzazione; un ruolo di organizzazione solo per la propria. Ogni verifica
lascia una riga in log_accessi, consentita o negata.
"""

from datetime import datetime

import psycopg


class PermessoNegato(PermissionError):
    """L'utente non ha un ruolo valido che consenta l'azione."""


def crea_utente(conn: psycopg.Connection, soggetto_sso: str) -> str:
    return str(conn.execute(
        "INSERT INTO utenti (soggetto_sso) VALUES (%s) RETURNING utente_id", (soggetto_sso,)
    ).fetchone()[0])


def assegna_ruolo(
    conn: psycopg.Connection,
    utente_id: str,
    ruolo: str,
    org_id: str | None = None,
    *,
    assegnata_da: str | None = None,
    valida_dal: datetime | None = None,
    valida_al: datetime | None = None,
) -> str:
    return str(conn.execute(
        """INSERT INTO assegnazioni_ruolo (utente_id, ruolo, org_id, assegnata_da, valida_dal, valida_al)
           VALUES (%s, %s, %s, %s, COALESCE(%s, now()), %s)
           RETURNING assegnazione_id""",
        (utente_id, ruolo, org_id, assegnata_da, valida_dal, valida_al),
    ).fetchone()[0])


def puo(
    conn: psycopg.Connection,
    utente_id: str,
    azione: str,
    org_id: str | None = None,
    risorsa: str | None = None,
) -> bool:
    consentito = conn.execute(
        """SELECT EXISTS (
             SELECT 1
             FROM assegnazioni_ruolo a
             JOIN ruoli r ON r.codice = a.ruolo
             JOIN permessi_ruolo p ON p.ruolo = a.ruolo AND p.azione = %(azione)s
             WHERE a.utente_id = %(utente)s
               AND a.valida_dal <= now()
               AND (a.valida_al IS NULL OR a.valida_al > now())
               AND (r.ambito = 'globale'
                    OR (%(org)s::uuid IS NOT NULL AND a.org_id = %(org)s::uuid)))""",
        {"azione": azione, "utente": utente_id, "org": org_id},
    ).fetchone()[0]
    conn.execute(
        """INSERT INTO log_accessi (utente_id, org_id, azione, risorsa, esito)
           VALUES (%s, %s, %s, %s, %s)""",
        (utente_id, org_id, azione, risorsa, "consentito" if consentito else "negato"),
    )
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
