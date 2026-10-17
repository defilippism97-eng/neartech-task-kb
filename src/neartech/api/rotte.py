"""Rotte dell'API (fase 6). Ogni rotta chiama il motore, che controlla i permessi e scrive gli atti."""

import base64
import binascii
from datetime import date
from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from neartech import pipeline
from neartech.abbinamento import LIVELLI, decidi_lotto, imposta_livello
from neartech.api.app import connessione, utente_corrente
from neartech.calcolo import calcola_organizzazione
from neartech.campioni import ESITI, registra_giudizio
from neartech.indirizzi_pesi import approva_profilo, proponi_profilo, stato_indirizzi, verifica_profilo
from neartech.metrica import calcola_precisione
from neartech.percorso import stato_percorso
from neartech.permessi import PermessoNegato, puo, ruoli_utente
from neartech.restituzione import RestituzioneSuperata, approva_restituzione, restituzione_organizzazione
from neartech.sperimentazione import avanzamento_sperimentazione
from neartech.valutazione_rubrica import coda_valutazione, registra_giudizio_rubrica, rubrica_corrente

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


class Motivazione(BaseModel):
    motivazione: str = Field(min_length=3, max_length=4000)


class Risposte(BaseModel):
    risposte: dict[str, int]
    nota: str = Field(default="", max_length=4000)


@router.get("/organizzazioni/{codice}/indirizzi")
def indirizzi(codice: str, utente: str = Depends(utente_corrente),
              conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Questionario degli indirizzi, ultimo profilo proposto, controlli ed effetto sui task."""
    return stato_indirizzi(conn, utente, _organizzazione(conn, utente, codice))


@router.post("/organizzazioni/{codice}/indirizzi/risposte")
def rispondi(codice: str, corpo: Risposte, request: Request, utente: str = Depends(utente_corrente),
             conn: psycopg.Connection = Depends(connessione)) -> dict[str, str]:
    profilo = proponi_profilo(conn, utente, _organizzazione(conn, utente, codice), corpo.risposte, nota=corpo.nota)
    request.app.state.conferma(conn)
    return {"profile_id": profilo}


@router.post("/organizzazioni/{codice}/indirizzi/{profile_id}/approvazione")
def approva_indirizzi(codice: str, profile_id: str, corpo: Motivazione, request: Request,
                      utente: str = Depends(utente_corrente),
                      conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    atto = approva_profilo(conn, utente, _organizzazione(conn, utente, codice), profile_id, motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"atto": atto}


@router.post("/organizzazioni/{codice}/indirizzi/{profile_id}/verifica")
def verifica_indirizzi(codice: str, profile_id: str, corpo: Motivazione, request: Request,
                       utente: str = Depends(utente_corrente),
                       conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    atto = verifica_profilo(conn, utente, _organizzazione(conn, utente, codice), profile_id, motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"atto": atto}


@router.post("/organizzazioni/{codice}/calcolo")
def ricalcola(codice: str, request: Request, utente: str = Depends(utente_corrente),
              conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    """Ricalcolo con la configurazione vigente (amministratore tecnico). Seme dalla data: ripetibile nel giorno."""
    esito = calcola_organizzazione(conn, utente, _organizzazione(conn, utente, codice),
                                   seme=int(date.today().strftime("%Y%m%d")))
    request.app.state.conferma(conn)
    return esito


class Giudizio(BaseModel):
    task_id: str
    voce: str
    valore: int
    nota: str = Field(default="", max_length=4000)


@router.get("/organizzazioni/{codice}/revisione")
def revisione(codice: str, utente: str = Depends(utente_corrente),
              conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Coda del revisore (dal task meno certo) con i testi della rubrica corrente."""
    org = _organizzazione(conn, utente, codice)
    return {"rubrica": rubrica_corrente(conn), "coda": coda_valutazione(conn, utente, org)}


@router.post("/organizzazioni/{codice}/revisione/giudizi")
def giudica(codice: str, corpo: Giudizio, request: Request, utente: str = Depends(utente_corrente),
            conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    atto = registra_giudizio_rubrica(conn, utente, _organizzazione(conn, utente, codice), corpo.task_id, corpo.voce,
                                     corpo.valore, nota=corpo.nota)
    request.app.state.conferma(conn)
    return {"atto": atto}


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


# --- pipeline dei documenti (amministratore tecnico) ----------------------------------

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
    return pipeline.stato_pipeline(conn, utente, _organizzazione(conn, utente, codice))


@router.post("/organizzazioni/{codice}/documenti")
def carica(codice: str, corpo: File, request: Request, utente: str = Depends(utente_corrente),
           conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    try:
        dati = base64.b64decode(corpo.contenuto, validate=True)
    except binascii.Error as errore:
        raise ValueError("contenuto non in base64") from errore
    esito = pipeline.carica_file(conn, utente, _organizzazione(conn, utente, codice), corpo.nome_file, dati)
    request.app.state.conferma(conn)
    return esito


@router.post("/organizzazioni/{codice}/documenti/scomposizione")
def scomponi(codice: str, corpo: Avvio, request: Request, utente: str = Depends(utente_corrente),
             conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Conferma la stima dei costi e accoda la scomposizione: le chiamate al modello le fa il lavoratore."""
    esito = pipeline.avvia_scomposizione(conn, utente, _organizzazione(conn, utente, codice), corpo.caricamenti,
                                         motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return esito


@router.post("/organizzazioni/{codice}/abbinamenti/proposta")
def proponi(codice: str, corpo: Motivazione, request: Request, utente: str = Depends(utente_corrente),
            conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    esito = pipeline.avvia_proposta(conn, utente, _organizzazione(conn, utente, codice), motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return esito


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/applicazione")
def applica(codice: str, lotto_id: str, corpo: Motivazione, request: Request, utente: str = Depends(utente_corrente),
            conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    esito = pipeline.avvia_applicazione(conn, utente, _organizzazione(conn, utente, codice), lotto_id,
                                        motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return esito


# --- lotti di abbinamento (revisore) --------------------------------------------------

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
    return pipeline.lotti(conn, utente, _organizzazione(conn, utente, codice))


@router.get("/organizzazioni/{codice}/lotti/{lotto_id}")
def lotto(codice: str, lotto_id: str, utente: str = Depends(utente_corrente),
          conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    """Il lotto per il revisore: le coppie del campione (revisione cieca), poi la coda intera per decidere."""
    return pipeline.dettaglio_lotto(conn, utente, _organizzazione(conn, utente, codice), lotto_id)


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/livello")
def livello(codice: str, lotto_id: str, corpo: Livello, request: Request, utente: str = Depends(utente_corrente),
            conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    atto = imposta_livello(conn, utente, _organizzazione(conn, utente, codice), lotto_id,
                           livello_revisione=corpo.livello, motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"atto": atto}


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/campione")
def campione(codice: str, lotto_id: str, corpo: Motivazione, request: Request, utente: str = Depends(utente_corrente),
             conn: psycopg.Connection = Depends(connessione)) -> dict[str, str]:
    campione_id = pipeline.crea_campione(conn, utente, _organizzazione(conn, utente, codice), lotto_id,
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
    org = _organizzazione(conn, utente, codice)
    giudizio = registra_giudizio(conn, utente, _campione_del_lotto(conn, utente, org, lotto_id), corpo.posizione,
                                 corpo.esito, nota=corpo.nota or None,
                                 versione_istruzioni=pipeline.ISTRUZIONI_ABBINAMENTO)
    request.app.state.conferma(conn)
    return {"giudizio": giudizio}


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/misura")
def misura(codice: str, lotto_id: str, request: Request, utente: str = Depends(utente_corrente),
           conn: psycopg.Connection = Depends(connessione)) -> dict[str, Any]:
    org = _organizzazione(conn, utente, codice)
    esito = calcola_precisione(conn, utente, _campione_del_lotto(conn, utente, org, lotto_id))
    request.app.state.conferma(conn)
    return {"esito": esito.esito, "precisione": esito.precisione}


@router.post("/organizzazioni/{codice}/lotti/{lotto_id}/decisione")
def decidi(codice: str, lotto_id: str, corpo: Decisione, request: Request, utente: str = Depends(utente_corrente),
           conn: psycopg.Connection = Depends(connessione)) -> dict[str, int]:
    atto = decidi_lotto(conn, utente, _organizzazione(conn, utente, codice), lotto_id, rifiutate=corpo.rifiutate,
                        motivazione=corpo.motivazione)
    request.app.state.conferma(conn)
    return {"atto": atto}
