"""Rotte della pipeline dei documenti (fase 6, amministratore tecnico): caricamento dei mansionari, scomposizione,
proposta degli abbinamenti e applicazione dei lotti decisi."""

import base64
import binascii
from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from neartech import pipeline
from neartech.api.app import connessione, utente_corrente
from neartech.api.rotte.comune import Motivazione, organizzazione_consentita

router = APIRouter(prefix="/api")


class File(BaseModel):
    nome_file: str = Field(min_length=6, max_length=255)
    contenuto: str = Field(max_length=4 * pipeline.MASSIMO_FILE // 3 + 4)  # base64 del .docx


class Avvio(BaseModel):
    caricamenti: list[str] = Field(min_length=1, max_length=200)
    motivazione: str = Field(min_length=3, max_length=4000)


@router.get("/organizzazioni/{codice}/documenti")
def documenti(codice: str, utente: str = Depends(utente_corrente),
              conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Mansionari caricati con stato e stima, candidati da proporre, lotti e lavori in coda."""
    return pipeline.stato_pipeline(conn, utente, organizzazione_consentita(conn, utente, codice))


@router.post("/organizzazioni/{codice}/documenti")
def carica(codice: str, corpo: File, request: Request, utente: str = Depends(utente_corrente),
           conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    try:
        dati = base64.b64decode(corpo.contenuto, validate=True)
    except binascii.Error as errore:
        raise ValueError("contenuto non in base64") from errore
    esito = pipeline.carica_file(conn, utente, organizzazione_consentita(conn, utente, codice), corpo.nome_file, dati)
    request.app.state.conferma(conn)
    return esito


@router.post("/organizzazioni/{codice}/documenti/scomposizione")
def scomponi(codice: str, corpo: Avvio, request: Request, utente: str = Depends(utente_corrente),
             conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Conferma la stima dei costi e accoda la scomposizione: le chiamate al modello le fa il lavoratore."""
    esito = pipeline.avvia_scomposizione(conn, utente, organizzazione_consentita(conn, utente, codice),
                                         corpo.caricamenti, motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return esito


@router.post("/organizzazioni/{codice}/abbinamenti/proposta")
def proponi(codice: str, corpo: Motivazione, request: Request, utente: str = Depends(utente_corrente),
            conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    esito = pipeline.avvia_proposta(conn, utente, organizzazione_consentita(conn, utente, codice),
                                    motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return esito


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/applicazione")
def applica(codice: str, lotto_id: str, corpo: Motivazione, request: Request, utente: str = Depends(utente_corrente),
            conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    esito = pipeline.avvia_applicazione(conn, utente, organizzazione_consentita(conn, utente, codice), lotto_id,
                                        motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return esito
