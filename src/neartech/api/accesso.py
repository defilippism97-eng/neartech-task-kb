"""Accesso alla piattaforma (ADR 0007).

SSO aziendale con OpenID Connect (codice di autorizzazione con PKCE; stato e nonce gestiti da authlib): il
soggetto SSO dell'utente è "<fornitore>|<sub>" e deve già esistere in utenti (gli utenti li crea l'amministratore
tecnico; nessuna registrazione automatica). Dell'identità si usa solo `sub`. In sviluppo, e solo da localhost, si
può entrare indicando un soggetto esistente, con una richiesta POST che porta l'intestazione della piattaforma.
"""

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

import psycopg
from neartech.api.app import apri_sessione, connessione, reindirizza_accesso_fallito

router = APIRouter(prefix="/accesso")


def _client(request: Request):
    impostazioni = request.app.state.impostazioni
    if impostazioni.oidc is None:
        raise HTTPException(status_code=404, detail="SSO non configurato")
    oauth = getattr(request.app.state, "oauth", None)
    if oauth is None:
        from authlib.integrations.starlette_client import OAuth
        oauth = OAuth()
        oauth.register(name="sso", server_metadata_url=impostazioni.oidc.metadati,
                       client_id=impostazioni.oidc.client_id, client_secret=impostazioni.oidc.client_secret,
                       client_kwargs={"scope": "openid", "code_challenge_method": "S256"})
        request.app.state.oauth = oauth
    return oauth.sso


def _utente_per_soggetto(conn: psycopg.Connection, soggetto: str) -> str | None:
    riga = conn.execute("SELECT utente_id FROM utenti WHERE soggetto_sso = %s", (soggetto,)).fetchone()
    return None if riga is None else str(riga[0])


@router.get("/entra")
async def entra(request: Request):
    impostazioni = request.app.state.impostazioni
    # Il ritorno viene dall'indirizzo pubblico configurato, non dall'intestazione Host della richiesta.
    ritorno = f"{impostazioni.url_pubblica.rstrip('/')}/accesso/ritorno" if impostazioni.url_pubblica \
        else str(request.url_for("ritorno"))
    return await _client(request).authorize_redirect(request, ritorno)


@router.get("/ritorno", name="ritorno")
async def ritorno(request: Request, conn: psycopg.Connection = Depends(connessione)):
    try:
        token = await _client(request).authorize_access_token(request)
    except OAuthError:
        return reindirizza_accesso_fallito()
    sub = (token.get("userinfo") or {}).get("sub")
    soggetto = f"{request.app.state.impostazioni.oidc.nome}|{sub}"
    # La query è sincrona: fuori dal ciclo degli eventi, per non fermare le altre richieste.
    utente = await run_in_threadpool(_utente_per_soggetto, conn, soggetto) if sub else None
    if utente is None:
        return reindirizza_accesso_fallito()
    apri_sessione(request, utente)
    return RedirectResponse("/", status_code=303)


class AccessoSviluppo(BaseModel):
    soggetto: str = Field(min_length=1, max_length=200)


@router.post("/sviluppo")
def sviluppo(corpo: AccessoSviluppo, request: Request, conn: psycopg.Connection = Depends(connessione)):
    impostazioni = request.app.state.impostazioni
    client = request.client.host if request.client else ""
    if not impostazioni.accesso_sviluppo or impostazioni.ambiente != "sviluppo" \
            or client not in impostazioni.client_sviluppo:
        raise HTTPException(status_code=404)
    utente = _utente_per_soggetto(conn, corpo.soggetto)
    if utente is None:
        raise HTTPException(status_code=403, detail="utente non abilitato alla piattaforma")
    apri_sessione(request, utente)
    return {"entrato": True}


@router.post("/esci")
def esci(request: Request):
    request.session.clear()
    return {"uscito": True}
