"""Rotte della corsia «flusso» (fase 6, docs/piani/fase-6-cantiere.md): lavori di ricalcolo, fase di verifica,
storico e stampa delle restituzioni, reversibilità della pipeline dei documenti.

Il modulo appartiene alla corsia flusso: solo lei vi aggiunge rotte. Per ora è vuoto; il router è già incluso
nell'applicazione (neartech.api.rotte.ROUTERS), quindi una rotta aggiunta qui è subito servita. Gli aiuti condivisi
(organizzazione_consentita, Motivazione) stanno in neartech.api.rotte.comune.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api")
