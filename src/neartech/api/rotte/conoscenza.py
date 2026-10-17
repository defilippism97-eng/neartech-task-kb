"""Rotte della corsia «conoscenza» (fase 6, docs/piani/fase-6-cantiere.md): base di conoscenza.

Il modulo appartiene alla corsia conoscenza: solo lei vi aggiunge rotte. Per ora è vuoto; il router è già incluso
nell'applicazione (neartech.api.rotte.ROUTERS), quindi una rotta aggiunta qui è subito servita. Gli aiuti condivisi
(organizzazione_consentita, Motivazione) stanno in neartech.api.rotte.comune.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api")
