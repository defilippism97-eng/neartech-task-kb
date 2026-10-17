"""Rotte dell'API (fase 6). Ogni rotta chiama il motore, che controlla i permessi e scrive gli atti."""

from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from neartech.api.app import connessione, utente_corrente
from neartech.percorso import stato_percorso
from neartech.permessi import PermessoNegato, puo, ruoli_utente
from neartech.restituzione import RestituzioneSuperata, approva_restituzione, restituzione_organizzazione
from neartech.sperimentazione import avanzamento_sperimentazione

router = APIRouter(prefix="/api")


def _organizzazione(conn: psycopg.Connection, utente: str, codice: str) -> str:
    """Organizzazione del codice, solo per chi può leggerla: un codice inesistente e uno non consentito danno la
    stessa risposta (403), così l'API non rivela quali organizzazioni esistono."""
    riga = conn.execute("SELECT org_id FROM organizations WHERE codice = %s", (codice,)).fetchone()
    if riga is None or not puo(conn, utente, "leggere", str(riga[0]), risorsa=f"organizzazione:{codice}"):
        raise PermessoNegato("organizzazione non consentita")
    return str(riga[0])


@router.get("/salute")
def salute() -> dict[str, str]:
    return {"stato": "ok"}


@router.get("/ambiente")
def ambiente(request: Request) -> dict[str, Any]:
    """Che accesso mostrare. L'accesso di sviluppo si dichiara solo se è attivo."""
    impostazioni = request.app.state.impostazioni
    risposta: dict[str, Any] = {"sso": impostazioni.oidc is not None}
    if impostazioni.accesso_sviluppo:
        risposta["accesso_sviluppo"] = True
    return risposta


@router.get("/io")
def io(utente: str = Depends(utente_corrente), conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    soggetto = conn.execute("SELECT soggetto_sso FROM utenti WHERE utente_id = %s", (utente,)).fetchone()[0]
    return {"utente_id": utente, "soggetto": soggetto, "ruoli": ruoli_utente(conn, utente)}


@router.get("/organizzazioni/{codice}/panoramica")
def panoramica(codice: str, utente: str = Depends(utente_corrente),
               conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Restituzione vigente e avanzamento della sperimentazione: la home del comitato guida."""
    org = _organizzazione(conn, utente, codice)
    restituzione = restituzione_organizzazione(conn, utente, org)
    avanzamento = avanzamento_sperimentazione(conn, utente, org)
    return {"restituzione": restituzione, "avanzamento": avanzamento,
            "percorso": stato_percorso(conn, utente, org, restituzione=restituzione, avanzamento=avanzamento)}


@router.get("/organizzazioni")
def organizzazioni(utente: str = Depends(utente_corrente),
                   conn: psycopg.Connection = Depends(connessione)) -> list[dict[str, str]]:
    """Organizzazioni che l'utente può leggere: per la home e per chi ha un ruolo globale."""
    righe = conn.execute("SELECT org_id, codice, name FROM organizations WHERE codice IS NOT NULL ORDER BY name").fetchall()
    return [{"codice": codice, "nome": nome} for org, codice, nome in righe
            if puo(conn, utente, "leggere", str(org), risorsa=f"organizzazione:{codice}")]


class Approvazione(BaseModel):
    impronta: str = Field(pattern=r"^[0-9a-f]{64}$")
    motivazione: str = Field(min_length=3, max_length=4000)


@router.post("/organizzazioni/{codice}/restituzione/approvazione")
def approva(codice: str, corpo: Approvazione, request: Request, utente: str = Depends(utente_corrente),
            conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Il comitato approva la restituzione che ha letto, identificata dalla sua impronta. Il motore la ricostruisce
    sotto il lock del calcolo e la rifiuta se nel frattempo è cambiata."""
    org = _organizzazione(conn, utente, codice)
    attuale = restituzione_organizzazione(conn, utente, org)
    if attuale["impronta"] != corpo.impronta:
        raise RestituzioneSuperata("i risultati sono cambiati dopo la lettura")
    atto = approva_restituzione(conn, utente, org, attuale, motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"atto": atto, "impronta": corpo.impronta}
