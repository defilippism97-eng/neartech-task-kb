"""Rotte della revisione (fase 6): coda del revisore e giudizi sulla rubrica."""

from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from neartech.api.app import connessione, utente_corrente
from neartech.api.rotte.comune import organizzazione_consentita
from neartech.valutazione_rubrica import coda_valutazione, registra_giudizio_rubrica, rubrica_corrente

router = APIRouter(prefix="/api")


class Giudizio(BaseModel):
    task_id: str
    voce: str
    valore: int
    nota: str = Field(default="", max_length=4000)


@router.get("/organizzazioni/{codice}/revisione")
def revisione(codice: str, utente: str = Depends(utente_corrente),
              conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Coda del revisore (dal task meno certo) con i testi della rubrica corrente."""
    org = organizzazione_consentita(conn, utente, codice)
    return {"rubrica": rubrica_corrente(conn), "coda": coda_valutazione(conn, utente, org)}


@router.post("/organizzazioni/{codice}/revisione/giudizi")
def giudica(codice: str, corpo: Giudizio, request: Request, utente: str = Depends(utente_corrente),
            conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    atto = registra_giudizio_rubrica(conn, utente, organizzazione_consentita(conn, utente, codice), corpo.task_id,
                                     corpo.voce, corpo.valore, nota=corpo.nota)
    request.app.state.conferma(conn)
    return {"atto": atto}
