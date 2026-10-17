"""Rotte dell'API (fase 6), un modulo per area. Ogni rotta chiama il motore, che controlla i permessi e scrive gli
atti.

Aree già costruite: base, panoramica, indirizzi, revisione, documenti, lotti. Moduli delle corsie del cantiere
(docs/piani/fase-6-cantiere.md), ciascuno di una sola corsia: amministrazione, conoscenza, flusso,
revisione_lavoro, questionari, ascolto, governo, sito. Gli aiuti condivisi stanno in comune.

ROUTERS elenca tutti i router in un ordine fisso: l'applicazione li include tutti (neartech.api.app.crea_app),
quindi una corsia aggiunge rotte nel proprio modulo senza toccare questo file.
"""

from neartech.api.rotte import (
    amministrazione,
    ascolto,
    base,
    conoscenza,
    documenti,
    flusso,
    governo,
    indirizzi,
    lotti,
    panoramica,
    questionari,
    revisione,
    revisione_lavoro,
    sito,
)

ROUTERS = [
    base.router,
    panoramica.router,
    indirizzi.router,
    revisione.router,
    documenti.router,
    lotti.router,
    amministrazione.router,
    conoscenza.router,
    flusso.router,
    revisione_lavoro.router,
    questionari.router,
    ascolto.router,
    governo.router,
    sito.router,
]
