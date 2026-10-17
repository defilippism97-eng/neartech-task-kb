"""Semi della prova locale (scripts/prova_locale.py): dati sintetici, un modulo per corsia del cantiere.

Ogni modulo espone `semina(conn, ctx)`; `popola` li esegue nell'ordine di SEMI dentro la stessa connessione, con un
solo contesto (prova.comune.Contesto) che porta gli identificativi creati: organizzazione, utenti, ruoli, task,
parametri. Il seme di base crea ACME S.p.A.; quelli delle corsie (docs/piani/fase-6-cantiere.md) aggiungono i propri
dati senza toccare gli altri moduli né questo file.

Solo per il database temporaneo della prova: nessun seme usa DATABASE_URL o il database di produzione.
"""

import psycopg

from . import (
    amministrazione,
    ascolto,
    base,
    conoscenza,
    flusso,
    governo,
    questionari,
    revisione_lavoro,
    sito,
)
from .comune import Contesto, incorpora_prova

__all__ = ["SEMI", "Contesto", "incorpora_prova", "popola"]

SEMI = [
    base,
    amministrazione,
    conoscenza,
    flusso,
    revisione_lavoro,
    questionari,
    ascolto,
    governo,
    sito,
]


def popola(conn: psycopg.Connection) -> Contesto:
    """Esegue tutti i semi in ordine e restituisce il contesto riempito."""
    ctx = Contesto()
    for seme in SEMI:
        seme.semina(conn, ctx)
    return ctx
