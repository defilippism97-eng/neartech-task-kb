"""Rotte degli indirizzi (fase 6): questionario, profilo di pesi proposto, approvazione e verifica."""

from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from neartech.api.app import connessione, utente_corrente
from neartech.api.rotte.comune import Motivazione, organizzazione_consentita
from neartech.indirizzi_pesi import approva_profilo, proponi_profilo, stato_indirizzi, verifica_profilo

router = APIRouter(prefix="/api")


class Risposte(BaseModel):
    risposte: dict[str, int]
    nota: str = Field(default="", max_length=4000)


@router.get("/organizzazioni/{codice}/indirizzi")
def indirizzi(codice: str, utente: str = Depends(utente_corrente),
              conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Questionario degli indirizzi, ultimo profilo proposto, controlli ed effetto sui task."""
    return stato_indirizzi(conn, utente, organizzazione_consentita(conn, utente, codice))


@router.post("/organizzazioni/{codice}/indirizzi/risposte")
def rispondi(codice: str, corpo: Risposte, request: Request, utente: str = Depends(utente_corrente),
             conn: psycopg.Connection = Depends(connessione)) -> dict[str, str]:
    profilo = proponi_profilo(conn, utente, organizzazione_consentita(conn, utente, codice), corpo.risposte,
                              nota=corpo.nota)
    request.app.state.conferma(conn)
    return {"profile_id": profilo}


@router.post("/organizzazioni/{codice}/indirizzi/{profile_id}/approvazione")
def approva_indirizzi(codice: str, profile_id: str, corpo: Motivazione, request: Request,
                      utente: str = Depends(utente_corrente),
                      conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    atto = approva_profilo(conn, utente, organizzazione_consentita(conn, utente, codice), profile_id,
                           motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"atto": atto}


@router.post("/organizzazioni/{codice}/indirizzi/{profile_id}/verifica")
def verifica_indirizzi(codice: str, profile_id: str, corpo: Motivazione, request: Request,
                       utente: str = Depends(utente_corrente),
                       conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    atto = verifica_profilo(conn, utente, organizzazione_consentita(conn, utente, codice), profile_id,
                            motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"atto": atto}
