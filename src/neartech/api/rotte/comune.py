"""Aiuti condivisi dalle rotte dell'API (fase 6): li usano più aree.

Qui sta solo ciò che serve a più di un modulo di rotte. Un'area che ha bisogno di un nuovo aiuto condiviso lo
aggiunge in fondo, in un blocco separato e con il nome della corsia (docs/piani/fase-6-cantiere.md).
"""

import psycopg
from pydantic import BaseModel, Field

from neartech.permessi import PermessoNegato, puo


def organizzazione_consentita(conn: psycopg.Connection, utente: str, codice: str) -> str:
    """Organizzazione del codice, solo per chi può leggerla: un codice inesistente e uno non consentito danno la
    stessa risposta (403), così l'API non rivela quali organizzazioni esistono."""
    riga = conn.execute("SELECT org_id FROM organizations WHERE codice = %s", (codice,)).fetchone()
    if riga is None or not puo(conn, utente, "leggere", str(riga[0]), risorsa=f"organizzazione:{codice}"):
        raise PermessoNegato("organizzazione non consentita")
    return str(riga[0])


class Motivazione(BaseModel):
    motivazione: str = Field(min_length=3, max_length=4000)
