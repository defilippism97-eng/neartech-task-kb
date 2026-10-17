"""Rotte dei lotti di abbinamento (fase 6, revisore): elenco e dettaglio, livello di revisione, campione,
giudizi sul campione, misura della precisione e decisione sul lotto."""

from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from neartech import pipeline
from neartech.abbinamento import LIVELLI, decidi_lotto, imposta_livello
from neartech.api.app import connessione, utente_corrente
from neartech.api.rotte.comune import Motivazione, organizzazione_consentita
from neartech.campioni import ESITI, registra_giudizio
from neartech.metrica import calcola_precisione

router = APIRouter(prefix="/api")


class Livello(BaseModel):
    livello: str = Field(pattern="^(" + "|".join(LIVELLI) + ")$")
    motivazione: str = Field(min_length=3, max_length=4000)


class EsitoCampione(BaseModel):
    posizione: int = Field(ge=1)
    esito: str = Field(pattern="^(" + "|".join(ESITI) + ")$")
    nota: str = Field(default="", max_length=4000)


class Decisione(BaseModel):
    rifiutate: list[str] = Field(default_factory=list, max_length=10000)
    motivazione: str = Field(min_length=3, max_length=4000)


@router.get("/organizzazioni/{codice}/lotti")
def elenco_lotti(codice: str, utente: str = Depends(utente_corrente),
                 conn: psycopg.Connection = Depends(connessione)) -> list[dict[str, Any]]:
    return pipeline.lotti(conn, utente, organizzazione_consentita(conn, utente, codice))


@router.get("/organizzazioni/{codice}/lotti/{lotto_id}")
def lotto(codice: str, lotto_id: str, utente: str = Depends(utente_corrente),
          conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Il lotto per il revisore: le coppie del campione (revisione cieca), poi la coda intera per decidere."""
    return pipeline.dettaglio_lotto(conn, utente, organizzazione_consentita(conn, utente, codice), lotto_id)


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/livello")
def livello(codice: str, lotto_id: str, corpo: Livello, request: Request, utente: str = Depends(utente_corrente),
            conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    atto = imposta_livello(conn, utente, organizzazione_consentita(conn, utente, codice), lotto_id,
                           livello_revisione=corpo.livello, motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"atto": atto}


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/campione")
def campione(codice: str, lotto_id: str, corpo: Motivazione, request: Request, utente: str = Depends(utente_corrente),
             conn: psycopg.Connection = Depends(connessione)) -> dict[str, str]:
    campione_id = pipeline.crea_campione(conn, utente, organizzazione_consentita(conn, utente, codice), lotto_id,
                                         motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"campione_id": campione_id}


def _campione_del_lotto(conn: psycopg.Connection, utente: str, org: str, lotto_id: str) -> str:
    campione_id = pipeline.dettaglio_lotto(conn, utente, org, lotto_id)["lotto"]["campione_id"]
    if campione_id is None:
        raise ValueError("il lotto non ha un campione")
    return campione_id


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/giudizi")
def giudica_campione(codice: str, lotto_id: str, corpo: EsitoCampione, request: Request,
                     utente: str = Depends(utente_corrente),
                     conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    org = organizzazione_consentita(conn, utente, codice)
    giudizio = registra_giudizio(conn, utente, _campione_del_lotto(conn, utente, org, lotto_id), corpo.posizione,
                                 corpo.esito, nota=corpo.nota or None,
                                 versione_istruzioni=pipeline.ISTRUZIONI_ABBINAMENTO)
    request.app.state.conferma(conn)
    return {"giudizio": giudizio}


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/misura")
def misura(codice: str, lotto_id: str, request: Request, utente: str = Depends(utente_corrente),
           conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    org = organizzazione_consentita(conn, utente, codice)
    esito = calcola_precisione(conn, utente, _campione_del_lotto(conn, utente, org, lotto_id))
    request.app.state.conferma(conn)
    return {"esito": esito.esito, "precisione": esito.precisione}


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/decisione")
def decidi(codice: str, lotto_id: str, corpo: Decisione, request: Request, utente: str = Depends(utente_corrente),
           conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    atto = decidi_lotto(conn, utente, organizzazione_consentita(conn, utente, codice), lotto_id,
                        rifiutate=corpo.rifiutate, motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"atto": atto}
