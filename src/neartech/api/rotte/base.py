"""Rotte di base dell'API (fase 6): salute, ambiente, utente corrente, organizzazioni visibili."""

from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request

from neartech.api.app import connessione, utente_corrente
from neartech.permessi import puo, ruoli_utente

router = APIRouter(prefix="/api")


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


@router.get("/organizzazioni")
def organizzazioni(utente: str = Depends(utente_corrente),
                   conn: psycopg.Connection = Depends(connessione)) -> list[dict[str, str]]:
    """Organizzazioni che l'utente può leggere: per la home e per chi ha un ruolo globale."""
    righe = conn.execute("SELECT org_id, codice, name FROM organizations WHERE codice IS NOT NULL ORDER BY name").fetchall()
    return [{"codice": codice, "nome": nome} for org, codice, nome in righe
            if puo(conn, utente, "leggere", str(org), risorsa=f"organizzazione:{codice}")]
