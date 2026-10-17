"""Applicazione web della piattaforma (fase 6, ADR 0007).

Uno strato sottile sopra il motore: ogni rotta chiama funzioni di neartech, che controllano i permessi
(richiedi) e scrivono gli atti nel registro. Qui stanno solo accesso, sessione, connessioni e traduzione degli
errori in risposte HTTP.

- Una connessione per richiesta, aperta solo dopo aver letto la sessione, senza conferma implicita: solo le
  rotte che scrivono confermano, con app.state.conferma (nei test non conferma nulla). Il log di accesso usa una
  connessione dedicata in autocommit (permessi.configura_log): un rifiuto resta registrato anche se la richiesta
  si annulla.
- Sessione in cookie firmato con utente_id e ora di inizio (durata massima assoluta); HttpOnly, SameSite=Lax,
  Secure e prefisso __Host- fuori dallo sviluppo.
- Le richieste che cambiano qualcosa (API e accesso) devono portare l'intestazione X-Neartech-Richiesta: un sito
  esterno non può aggiungerla senza un preflight CORS, che l'applicazione non concede.
- Solo gli host ammessi (TrustedHostMiddleware): in sviluppo localhost, altrove l'indirizzo pubblico.
- Gli errori tornano al client con messaggi fissi; il dettaglio resta nel log del server.
"""

import logging
import secrets
import time
from collections.abc import Callable, Iterator
from contextlib import asynccontextmanager
from pathlib import Path

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from neartech.api.config import Impostazioni
from neartech.db import connect
from neartech.governance import DecisioneGiaPresa, ParametroAssente
from neartech.metrica import CampioneIncompleto, DisaccordoRevisori
from neartech.permessi import PermessoNegato, configura_log
from neartech.restituzione import RestituzioneSuperata

INTESTAZIONE_RICHIESTA = "X-Neartech-Richiesta"
METODI_SICURI = ("GET", "HEAD", "OPTIONS")
log = logging.getLogger("neartech.api")

# Errore del motore -> (stato HTTP, messaggio fisso per il client).
ERRORI: list[tuple[type[Exception], int, str]] = [
    (psycopg.errors.LockNotAvailable, 503, "calcolo in corso: riprova tra qualche istante"),
    (PermessoNegato, 403, "operazione non consentita"),
    (RestituzioneSuperata, 409, "i risultati sono cambiati dopo la lettura"),
    (DecisioneGiaPresa, 409, "decisione già presa"),
    (CampioneIncompleto, 409, "il campione non è ancora tutto giudicato"),
    (DisaccordoRevisori, 409, "i revisori non concordano su alcuni elementi"),
    (ParametroAssente, 409, "manca un parametro approvato"),
    (LookupError, 404, "non trovato"),
    (ValueError, 422, "dati non validi"),
]


def connessione(request: Request) -> Iterator[psycopg.Connection]:
    """Connessione della richiesta. Tutto ciò che non è confermato esplicitamente si annulla alla fine."""
    conn = request.app.state.connetti()
    try:
        # Una richiesta non aspetta all'infinito un calcolo in corso: dopo l'attesa risponde 503.
        conn.execute("SET lock_timeout = '10s'")
        yield conn
    finally:
        try:
            conn.rollback()
        finally:
            conn.close()


def _utente_in_sessione(request: Request) -> str:
    """Utente della sessione, senza toccare il database: chi non ha una sessione valida non apre connessioni."""
    utente = request.session.get("utente_id")
    iniziata = request.session.get("iniziata_il", 0)
    durata = request.app.state.impostazioni.durata_sessione_ore * 3600
    if not utente or not isinstance(iniziata, (int, float)) or time.time() - iniziata > durata:
        request.session.clear()
        raise HTTPException(status_code=401, detail="accesso richiesto")
    return str(utente)


def utente_corrente(request: Request, utente: str = Depends(_utente_in_sessione),
                    conn: psycopg.Connection = Depends(connessione)) -> str:
    if conn.execute("SELECT 1 FROM utenti WHERE utente_id = %s::uuid", (utente,)).fetchone() is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="accesso richiesto")
    return utente


def apri_sessione(request: Request, utente_id: str) -> None:
    request.session.clear()
    request.session["utente_id"] = utente_id
    request.session["iniziata_il"] = int(time.time())


class LogResiliente:
    """Connessione del log di accesso che si riapre da sola: Neon chiude le connessioni inattive, e un log morto
    renderebbe impossibile ogni controllo dei permessi fino al riavvio. Un tentativo di riconnessione, poi errore."""

    def __init__(self, connetti: Callable[[], psycopg.Connection]):
        self._connetti = connetti
        self._conn: psycopg.Connection | None = None

    def execute(self, *argomenti):
        for tentativo in (1, 2):
            try:
                if self._conn is None or self._conn.closed or self._conn.broken:
                    self._conn = self._connetti()
                    self._conn.autocommit = True
                return self._conn.execute(*argomenti)
            except psycopg.OperationalError:
                self.close()
                if tentativo == 2:
                    raise
        return None

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None


def _gestore(stato: int, messaggio: str) -> Callable:
    async def gestisci(request: Request, errore: Exception) -> JSONResponse:
        log.info("%s %s -> %s (%s: %s)", request.method, request.url.path, stato, type(errore).__name__, errore)
        return JSONResponse(status_code=stato, content={"detail": messaggio})
    return gestisci


def _intestazioni(risposta, impostazioni: Impostazioni, percorso: str) -> None:
    risposta.headers["X-Content-Type-Options"] = "nosniff"
    risposta.headers["Referrer-Policy"] = "same-origin"
    risposta.headers["X-Frame-Options"] = "DENY"
    risposta.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    risposta.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    risposta.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; object-src 'none'; "
        "base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
    if impostazioni.cookie_sicuro:
        risposta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if percorso.startswith(("/api/", "/accesso/")):
        risposta.headers["Cache-Control"] = "no-store"  # testi dell'organizzazione: mai in cache


def crea_app(impostazioni: Impostazioni, *, connetti: Callable[[], psycopg.Connection] = connect,
             log_dedicato: bool = True) -> FastAPI:
    @asynccontextmanager
    async def ciclo(app: FastAPI):
        conn_log = None
        if log_dedicato:
            conn_log = LogResiliente(connetti)
            configura_log(conn_log)
        try:
            yield
        finally:
            if conn_log is not None:
                configura_log(None)
                conn_log.close()

    app = FastAPI(title="Neartech", lifespan=ciclo, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.impostazioni = impostazioni
    app.state.connetti = connetti
    app.state.conferma = lambda conn: conn.commit()

    for classe, stato, messaggio in ERRORI:
        app.add_exception_handler(classe, _gestore(stato, messaggio))

    @app.middleware("http")
    async def protezioni(request: Request, call_next):
        percorso = request.url.path
        if percorso.startswith(("/api/", "/accesso/")) and request.method not in METODI_SICURI \
                and request.headers.get(INTESTAZIONE_RICHIESTA) != "1":
            risposta = JSONResponse(status_code=403, content={"detail": "richiesta senza intestazione della piattaforma"})
        else:
            risposta = await call_next(request)
        _intestazioni(risposta, impostazioni, percorso)
        return risposta

    chiave = impostazioni.chiave_sessione or secrets.token_urlsafe(32)  # in sviluppo: una chiave per avvio
    app.add_middleware(SessionMiddleware, secret_key=chiave, session_cookie=impostazioni.nome_cookie,
                       same_site="lax", https_only=impostazioni.cookie_sicuro,
                       max_age=impostazioni.durata_sessione_ore * 3600)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(impostazioni.host))

    from neartech.api import accesso, rotte
    app.include_router(accesso.router)
    app.include_router(rotte.router)

    if impostazioni.cartella_web is not None:
        _servi_frontend(app, impostazioni.cartella_web)
    return app


def _servi_frontend(app: FastAPI, cartella: Path) -> None:
    """Frontend compilato: file statici e, per ogni altro percorso fuori da /api, la pagina dell'applicazione.
    Mai file nascosti o mappe dei sorgenti."""
    cartella = cartella.resolve()
    indice = cartella / "index.html"
    if not indice.is_file():
        raise ValueError(f"nella cartella del frontend manca index.html: {cartella}")
    if (cartella / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=cartella / "assets"), name="assets")

    @app.get("/{percorso:path}", include_in_schema=False)
    async def pagina(percorso: str):
        if percorso.startswith(("api/", "accesso/")):
            raise HTTPException(status_code=404)
        nome = Path(percorso).name
        if percorso and "\x00" not in percorso and not nome.startswith(".") and not nome.endswith(".map"):
            file = (cartella / percorso).resolve()
            if file.is_file() and file.is_relative_to(cartella):
                return FileResponse(file)
        return FileResponse(indice)


def reindirizza_accesso_fallito() -> RedirectResponse:
    return RedirectResponse("/?accesso=non-riuscito", status_code=303)
