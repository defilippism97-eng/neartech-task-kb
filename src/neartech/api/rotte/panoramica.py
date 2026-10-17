"""Rotte della panoramica (fase 6): home del comitato guida, ricalcolo e approvazione della restituzione."""

from datetime import date
from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from neartech.api.app import connessione, utente_corrente
from neartech.api.rotte.comune import organizzazione_consentita
from neartech.calcolo import calcola_organizzazione
from neartech.percorso import stato_percorso
from neartech.restituzione import RestituzioneSuperata, approva_restituzione, restituzione_organizzazione
from neartech.sperimentazione import avanzamento_sperimentazione

router = APIRouter(prefix="/api")


@router.get("/organizzazioni/{codice}/panoramica")
def panoramica(codice: str, utente: str = Depends(utente_corrente),
               conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Restituzione vigente e avanzamento della sperimentazione: la home del comitato guida."""
    org = organizzazione_consentita(conn, utente, codice)
    restituzione = restituzione_organizzazione(conn, utente, org)
    avanzamento = avanzamento_sperimentazione(conn, utente, org)
    return {"restituzione": restituzione, "avanzamento": avanzamento,
            "percorso": stato_percorso(conn, utente, org, restituzione=restituzione, avanzamento=avanzamento)}


@router.post("/organizzazioni/{codice}/calcolo")
def ricalcola(codice: str, request: Request, utente: str = Depends(utente_corrente),
              conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    """Ricalcolo con la configurazione vigente (amministratore tecnico). Seme dalla data: ripetibile nel giorno."""
    esito = calcola_organizzazione(conn, utente, organizzazione_consentita(conn, utente, codice),
                                   seme=int(date.today().strftime("%Y%m%d")))
    request.app.state.conferma(conn)
    return esito


class Approvazione(BaseModel):
    impronta: str = Field(pattern=r"^[0-9a-f]{64}$")
    motivazione: str = Field(min_length=3, max_length=4000)


@router.post("/organizzazioni/{codice}/restituzione/approvazione")
def approva(codice: str, corpo: Approvazione, request: Request, utente: str = Depends(utente_corrente),
            conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Il comitato approva la restituzione che ha letto, identificata dalla sua impronta. Il motore la ricostruisce
    sotto il lock del calcolo e la rifiuta se nel frattempo è cambiata."""
    org = organizzazione_consentita(conn, utente, codice)
    attuale = restituzione_organizzazione(conn, utente, org)
    if attuale["impronta"] != corpo.impronta:
        raise RestituzioneSuperata("i risultati sono cambiati dopo la lettura")
    atto = approva_restituzione(conn, utente, org, attuale, motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"atto": atto, "impronta": corpo.impronta}
