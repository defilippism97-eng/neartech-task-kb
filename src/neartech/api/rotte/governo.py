"""Rotte della corsia «governo» (fase 6, docs/piani/fase-6-cantiere.md): parametri, completamento degli indirizzi,
home dell'auditor, registro, vista del rappresentante.

Il modulo appartiene alla corsia governo: solo lei vi aggiunge rotte. Per ora è vuoto; il router è già incluso
nell'applicazione (neartech.api.rotte.ROUTERS), quindi una rotta aggiunta qui è subito servita. Gli aiuti condivisi
(organizzazione_consentita, Motivazione) stanno in neartech.api.rotte.comune.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api")
