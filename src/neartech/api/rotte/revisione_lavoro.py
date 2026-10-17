"""Rotte della corsia «revisione_lavoro» (fase 6, docs/piani/fase-6-cantiere.md): lavoro del revisore: giudizi sulla
rubrica, lotti, coda unificata, somiglianze, ritaratura.

Il modulo appartiene alla corsia revisione_lavoro: solo lei vi aggiunge rotte. Per ora è vuoto; il router è già
incluso nell'applicazione (neartech.api.rotte.ROUTERS), quindi una rotta aggiunta qui è subito servita. Gli aiuti
condivisi (organizzazione_consentita, Motivazione) stanno in neartech.api.rotte.comune.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api")
