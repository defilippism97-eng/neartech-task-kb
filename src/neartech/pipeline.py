"""Pipeline dei documenti dalla piattaforma (fase 6, fetta 5): caricamento, stima, scomposizione, abbinamento.

1. L'amministratore tecnico carica un mansionario (.docx): il testo resta nello spazio dell'organizzazione
   (caricamenti) con un atto. Nessuna chiamata al modello.
2. La stima dei costi viene dal parametro di governance `prezzi_scomposizione` (prezzi del modello e rapporti
   di stima): senza un valore approvato la scomposizione non parte.
3. L'avvio è un atto con la stima nei dettagli; accoda un job per documento. Il lavoratore (scripts/worker.py)
   chiama il modello e salva le attività come candidati (neartech.scomposizione.carica_candidati).
4. La proposta di abbinamento e l'applicazione di un lotto deciso sono job anch'esse: l'embedding (bge-m3)
   gira nel lavoratore, non nel processo dell'API. Livello, campione, giudizi e decisione del lotto sono del
   revisore (neartech.abbinamento, neartech.campioni, neartech.metrica).

Nei job vanno solo identificativi: il testo e le motivazioni restano nello spazio e nel registro (ADR 0001).
"""

import hashlib
import math
import zipfile
import uuid
from collections.abc import Callable
from datetime import date
from typing import Any

import psycopg
from psycopg import sql

from neartech import campioni
from neartech.abbinamento import (
    MODELLO_EMBEDDING,
    REVISIONE_EMBEDDING,
    Incorpora,
    applica_lotto,
    coda_revisione,
    crea_campione_del_lotto,
    proponi_abbinamenti,
)
from neartech.coda import accoda
from neartech.governance import ParametroAssente, ParametroRitirato, parametro_vigente
from neartech.occorrenze import spazio_organizzazione
from neartech.permessi import richiedi
from neartech.registro import registra
from neartech.scomposizione import (
    MAX_ATTEMPTS,
    MAX_TOKENS,
    MODEL_ID,
    SYSTEM_PROMPT,
    DocumentoJob,
    _user_message,
    carica_candidati,
    proponi_attivita,
    ruolo_da_testo,
    testo_docx,
    titoli_attivi,
)

PARAMETRO_PREZZI = "prezzi_scomposizione"
ISTRUZIONI_ABBINAMENTO = "istruzioni-abbinamento-v1"  # docs/revisione/istruzioni-abbinamento-v1.md, approvate
TIPO_SCOMPOSIZIONE = "scomposizione_documento"
TIPO_PROPOSTA = "proposta_abbinamenti"
TIPO_APPLICAZIONE = "applicazione_lotto"
MASSIMO_FILE = 5_000_000  # byte di un .docx caricato: limite tecnico

Gestore = Callable[[psycopg.Connection, Any], None]


def _uuid(valore: str) -> str:
    return str(uuid.UUID(str(valore)))


def _blocca(conn: psycopg.Connection, chiave: str) -> None:
    conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (chiave,))


# --- stima -------------------------------------------------------------------------

def prezzi(conn: psycopg.Connection, org_id: str) -> dict[str, Any] | None:
    """Parametro vigente dei prezzi, validato; vuoto se non ce n'è uno approvato."""
    try:
        parametro = parametro_vigente(conn, PARAMETRO_PREZZI, org_id)
    except (ParametroAssente, ParametroRitirato):
        return None
    v = parametro.valore if isinstance(parametro.valore, dict) else {}
    chiavi = ("ingresso_eur_mtok", "uscita_eur_mtok", "caratteri_per_token", "uscita_su_ingresso")
    if v.get("modello") != MODEL_ID or not all(
        isinstance(v.get(k), (int, float)) and not isinstance(v.get(k), bool) and v[k] > 0 for k in chiavi
    ):
        raise ValueError(f"{PARAMETRO_PREZZI}: valore non valido per il modello {MODEL_ID}")
    return {"parametro_id": parametro.parametro_id, "versione": parametro.versione, "modello": MODEL_ID,
            **{k: v[k] for k in chiavi}}


def stima_documento(testo: str, ruolo: str, titoli: list[str], p: dict[str, Any]) -> dict[str, float]:
    """Token e costo di una scomposizione: ingresso dal testo che il modello riceverà davvero, uscita in
    proporzione (al massimo MAX_TOKENS). Il costo massimo conta i tentativi ripetuti."""
    messaggio = _user_message(DocumentoJob(nome_file="", ruolo=ruolo, testo=testo, sha256=""), titoli)
    ingresso = math.ceil((len(SYSTEM_PROMPT) + len(messaggio)) / p["caratteri_per_token"])
    uscita = min(MAX_TOKENS, math.ceil(ingresso * p["uscita_su_ingresso"]))
    costo = (ingresso * p["ingresso_eur_mtok"] + uscita * p["uscita_eur_mtok"]) / 1_000_000
    return {"token_ingresso": ingresso, "token_uscita": uscita, "costo": round(costo, 4),
            "costo_massimo": round(costo * MAX_ATTEMPTS, 4)}


def _somma(stime: list[dict[str, float]]) -> dict[str, float]:
    return {k: (round(sum(s[k] for s in stime), 4) if k.startswith("costo") else sum(s[k] for s in stime))
            for k in ("token_ingresso", "token_uscita", "costo", "costo_massimo")}


# --- caricamento e avvio -----------------------------------------------------------

def carica_file(conn: psycopg.Connection, utente_id: str, org_id: str, nome_file: str, dati: bytes) -> dict[str, Any]:
    """Un mansionario nello spazio, con un atto. Lo stesso contenuto caricato di nuovo non si duplica."""
    org_id = _uuid(org_id)
    nome_file = nome_file.strip()[:255]
    if not nome_file.lower().endswith(".docx"):
        raise ValueError("serve un file .docx")
    if len(dati) > MASSIMO_FILE:
        raise ValueError("file troppo grande")
    with conn.transaction():
        # Il permesso prima di aprire il file: chi non può caricare non fa lavorare il server.
        richiedi(conn, utente_id, "gestire_dataset_centrale", org_id, risorsa="caricamento")
        try:
            testo = testo_docx(dati)
        except (zipfile.BadZipFile, KeyError, OSError, SyntaxError) as errore:  # zip o XML non validi, corpo assente
            raise ValueError("il file non è un .docx leggibile") from errore
        ruolo = ruolo_da_testo(testo)
        if not testo.strip() or not ruolo:
            raise ValueError("nel documento manca il titolo della posizione")
        sha = hashlib.sha256(dati).hexdigest()
        schema = spazio_organizzazione(conn, org_id)
        _blocca(conn, f"caricamento:{org_id}:{sha}")
        esistente = conn.execute(sql.SQL("SELECT caricamento_id FROM {}.caricamenti WHERE sha256 = %s").format(schema),
                                 (sha,)).fetchone()
        if esistente is not None:
            return {"caricamento_id": str(esistente[0]), "nuovo": False, "ruolo": ruolo}
        caricamento_id = str(uuid.uuid4())
        atto = registra(conn, autore_id=utente_id, tipo_oggetto="caricamento_file", oggetto_id=caricamento_id,
                        atto="proposta", motivazione="mansionario caricato dalla piattaforma", org_id=org_id,
                        dettagli={"caratteri": len(testo), "sha256": sha},
                        dettagli_riservati={"nome_file": nome_file, "ruolo": ruolo})
        conn.execute(
            sql.SQL("""INSERT INTO {}.caricamenti (caricamento_id, nome_file, sha256, ruolo, testo, caricato_da,
                                                    decisione_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""").format(schema),
            (caricamento_id, nome_file, sha, ruolo, testo, utente_id, atto),
        )
        return {"caricamento_id": caricamento_id, "nuovo": True, "ruolo": ruolo}


_STATI_JOB = {"queued": "in_coda", "running": "in_corso", "done": "fatto", "failed": "fallito"}


def _caricamenti(conn: psycopg.Connection, schema: sql.Identifier) -> list[dict[str, Any]]:
    """Documenti caricati con lo stato dell'ultimo avvio e i candidati estratti."""
    righe = conn.execute(
        sql.SQL("""SELECT c.caricamento_id, c.nome_file, c.ruolo, c.testo, c.caricato_il, j.status, j.ultimo_errore,
                          (SELECT count(*) FROM {0}.candidati k JOIN {0}.documenti d USING (documento_id)
                           WHERE d.sha256 = c.sha256)
                   FROM {0}.caricamenti c
                   LEFT JOIN LATERAL (SELECT a.job_id FROM {0}.avvii_scomposizione a
                                      WHERE a.caricamento_id = c.caricamento_id
                                      ORDER BY a.avviato_il DESC LIMIT 1) a ON true
                   LEFT JOIN public.jobs j ON j.job_id = a.job_id
                   ORDER BY c.caricato_il, c.nome_file""").format(schema),
    ).fetchall()
    return [{"caricamento_id": str(r[0]), "nome_file": r[1], "ruolo": r[2], "testo": r[3], "caricato_il": r[4],
             "stato": _STATI_JOB.get(r[5], "da_avviare"), "errore": r[6], "candidati": r[7]} for r in righe]


def avvia_scomposizione(
    conn: psycopg.Connection, utente_id: str, org_id: str, caricamenti: list[str], *, motivazione: str,
) -> dict[str, Any]:
    """Conferma la stima e accoda la scomposizione dei documenti indicati (da avviare o falliti).
    Un atto per l'avvio, con stima, parametro dei prezzi e modello; un job per documento."""
    org_id = _uuid(org_id)
    scelti = {_uuid(c) for c in caricamenti}
    if not scelti:
        raise ValueError("nessun documento scelto")
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_dataset_centrale", org_id, risorsa="scomposizione")
        schema = spazio_organizzazione(conn, org_id)
        _blocca(conn, f"scomposizione:{org_id}")
        p = prezzi(conn, org_id)
        if p is None:
            raise ValueError(f"manca il parametro approvato {PARAMETRO_PREZZI}: la stima dei costi viene prima")
        documenti = {c["caricamento_id"]: c for c in _caricamenti(conn, schema)}
        if scelti - set(documenti):
            raise LookupError("documento non caricato")
        if any(documenti[c]["stato"] not in ("da_avviare", "fallito") for c in scelti):
            raise ValueError("documento già avviato")
        titoli = titoli_attivi(conn)
        stime = {c: stima_documento(documenti[c]["testo"], documenti[c]["ruolo"], titoli, p) for c in sorted(scelti)}
        totale = _somma(list(stime.values()))
        avvio_id = str(uuid.uuid4())
        atto = registra(conn, autore_id=utente_id, tipo_oggetto="scomposizione_documenti", oggetto_id=avvio_id,
                        atto="approvazione", motivazione=motivazione, org_id=org_id,
                        dettagli={"documenti": len(stime), "modello": MODEL_ID, "parametro_prezzi": p["parametro_id"],
                                  **{f"stima_{k}": v for k, v in totale.items()}})
        for caricamento_id in stime:
            job = accoda(conn, TIPO_SCOMPOSIZIONE, {"org_id": org_id, "caricamento_id": caricamento_id,
                                                    "utente_id": utente_id, "atto": atto}, org_id=org_id)
            conn.execute(sql.SQL("""INSERT INTO {}.avvii_scomposizione (job_id, caricamento_id, decisione_id)
                                    VALUES (%s, %s, %s)""").format(schema), (job, caricamento_id, atto))
        return {"atto": atto, "documenti": len(stime), **totale}


def _job_attivo(conn: psycopg.Connection, org_id: str, tipo: str, lotto_id: str | None = None) -> bool:
    return conn.execute(
        """SELECT EXISTS (SELECT 1 FROM jobs WHERE org_id = %s AND kind = %s AND status IN ('queued', 'running')
                          AND (%s::text IS NULL OR payload ->> 'lotto_id' = %s::text))""",
        (org_id, tipo, lotto_id, lotto_id),
    ).fetchone()[0]


def avvia_proposta(conn: psycopg.Connection, utente_id: str, org_id: str, *, motivazione: str) -> dict[str, Any]:
    """Accoda la proposta di abbinamento dei candidati non ancora proposti: un lotto nuovo."""
    org_id = _uuid(org_id)
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_dataset_centrale", org_id, risorsa="abbinamento")
        schema = spazio_organizzazione(conn, org_id)
        _blocca(conn, f"abbinamento:{org_id}")
        if _job_attivo(conn, org_id, TIPO_PROPOSTA):
            raise ValueError("una proposta è già in coda")
        if not _da_proporre(conn, schema):
            raise ValueError("nessun candidato da proporre")
        atto = registra(conn, autore_id=utente_id, tipo_oggetto="richiesta_proposta_abbinamenti",
                        oggetto_id=str(uuid.uuid4()), atto="proposta", motivazione=motivazione, org_id=org_id)
        job = accoda(conn, TIPO_PROPOSTA, {"org_id": org_id, "utente_id": utente_id, "atto": atto}, org_id=org_id)
        return {"atto": atto, "job_id": job}


def avvia_applicazione(
    conn: psycopg.Connection, utente_id: str, org_id: str, lotto_id: str, *, motivazione: str,
) -> dict[str, Any]:
    """Accoda l'applicazione di un lotto deciso dal revisore."""
    org_id, lotto_id = _uuid(org_id), _uuid(lotto_id)
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_dataset_centrale", org_id, risorsa=f"lotto_abbinamento:{lotto_id}")
        _blocca(conn, f"lotto_abbinamento:{lotto_id}")
        lotto = next((x for x in _lotti(conn, org_id) if x["lotto_id"] == lotto_id), None)
        if lotto is None:
            raise LookupError("lotto inesistente")
        if lotto["stato"] != "deciso":
            raise ValueError("il lotto non è da applicare")
        atto = registra(conn, autore_id=utente_id, tipo_oggetto="richiesta_applicazione_lotto", oggetto_id=lotto_id,
                        atto="proposta", motivazione=motivazione, org_id=org_id)
        job = accoda(conn, TIPO_APPLICAZIONE, {"org_id": org_id, "lotto_id": lotto_id, "utente_id": utente_id,
                                               "atto": atto}, org_id=org_id)
        return {"atto": atto, "job_id": job}


# --- lavoratore --------------------------------------------------------------------

def gestori(*, client: Any | None, incorpora: Incorpora | None) -> dict[str, Gestore]:
    """Gestori dei job della pipeline per scripts/worker.py. Senza client (chiave del modello) la scomposizione non
    si registra; senza embedding non si registrano proposta e applicazione: quei job restano in coda."""

    def scomponi(conn: psycopg.Connection, payload: dict[str, Any]) -> None:
        schema = spazio_organizzazione(conn, payload["org_id"])
        riga = conn.execute(sql.SQL("SELECT nome_file, ruolo, testo, sha256 FROM {}.caricamenti WHERE caricamento_id = %s")
                            .format(schema), (payload["caricamento_id"],)).fetchone()
        if riga is None:
            raise LookupError("caricamento inesistente")
        doc = DocumentoJob(nome_file=riga[0], ruolo=riga[1], testo=riga[2], sha256=riga[3])
        attivita = proponi_attivita(client, doc, titoli_attivi(conn))
        carica_candidati(conn, payload["utente_id"], doc, attivita, org_id=payload["org_id"], modalita="modello",
                         motivazione=f"scomposizione avviata con l'atto {payload['atto']}")

    def proponi(conn: psycopg.Connection, payload: dict[str, Any]) -> None:
        proponi_abbinamenti(conn, payload["utente_id"], payload["org_id"], incorpora=incorpora,
                            motivazione=f"proposta richiesta con l'atto {payload['atto']}")

    def applica(conn: psycopg.Connection, payload: dict[str, Any]) -> None:
        applica_lotto(conn, payload["utente_id"], payload["org_id"], payload["lotto_id"], incorpora=incorpora,
                      motivazione=f"applicazione richiesta con l'atto {payload['atto']}")

    registrati: dict[str, Gestore] = {}
    if client is not None:
        registrati[TIPO_SCOMPOSIZIONE] = scomponi
    if incorpora is not None:
        registrati |= {TIPO_PROPOSTA: proponi, TIPO_APPLICAZIONE: applica}
    return registrati


def incorpora_bge_m3() -> Incorpora:
    """bge-m3 in locale, caricato alla prima chiamata; vettori normalizzati come per i task del dataset.
    Serve l'ambiente .venv-embedding (docs/sviluppo.md)."""
    caricato = []

    def incorpora(titoli: list[str]):
        if not caricato:
            from sentence_transformers import SentenceTransformer
            caricato.append(SentenceTransformer(MODELLO_EMBEDDING, revision=REVISIONE_EMBEDDING, device="cpu"))
        return caricato[0].encode(titoli, batch_size=64, normalize_embeddings=True).tolist()

    incorpora.modello = MODELLO_EMBEDDING
    return incorpora


# --- stato per le schermate --------------------------------------------------------

def _da_proporre(conn: psycopg.Connection, schema: sql.Identifier) -> int:
    return conn.execute(
        sql.SQL("""SELECT count(*) FROM {0}.candidati c WHERE NOT EXISTS
                   (SELECT 1 FROM {0}.proposte_abbinamento p WHERE p.candidato_id = c.candidato_id)""").format(schema),
    ).fetchone()[0]


def _lotti(conn: psycopg.Connection, org_id: str) -> list[dict[str, Any]]:
    """Lotti dal più recente, con il passo in cui si trovano. Sola lettura: i permessi li verifica chi chiama."""
    schema = spazio_organizzazione(conn, org_id)
    righe = conn.execute(
        sql.SQL("""SELECT l.lotto_id, l.creato_il, count(p.proposta_id), count(p.task_id), v.livello_revisione,
                          bool_or(d.proposta_id IS NOT NULL), bool_or(a.proposta_id IS NOT NULL),
                          c.campione_id, c.dimensione,
                          (SELECT count(DISTINCT g.posizione) FROM giudizi_revisione g
                           WHERE g.campione_id = c.campione_id),
                          (SELECT m.esito FROM misure_precisione m WHERE m.campione_id = c.campione_id
                           ORDER BY m.calcolata_il DESC LIMIT 1)
                   FROM {0}.lotti_abbinamento l
                   LEFT JOIN {0}.proposte_abbinamento p USING (lotto_id)
                   LEFT JOIN {0}.livelli_lotto v USING (lotto_id)
                   LEFT JOIN {0}.decisioni_abbinamento d USING (proposta_id)
                   LEFT JOIN {0}.applicazioni_abbinamento a USING (proposta_id)
                   LEFT JOIN campioni_revisione c ON c.org_id = %s AND c.tipo_proposta = 'abbinamento'
                                                 AND c.filtro ->> 'lotto' = l.lotto_id::text
                   GROUP BY l.lotto_id, l.creato_il, v.livello_revisione, c.campione_id, c.dimensione
                   ORDER BY l.creato_il DESC""").format(schema),
        (org_id,),
    ).fetchall()
    risultato = []
    for (lotto, creato, proposte, con_task, livello, deciso, applicato, campione, dimensione, giudicati,
         esito_misura) in righe:
        if applicato:
            stato = "applicato"
        elif deciso:
            stato = "in_applicazione" if _job_attivo(conn, org_id, TIPO_APPLICAZIONE, str(lotto)) else "deciso"
        elif livello is None:
            stato = "da_impostare"
        elif livello == "nulla" or not con_task or esito_misura is not None:
            stato = "da_decidere"
        elif campione is None:
            stato = "da_campionare"
        else:
            stato = "da_giudicare" if giudicati < dimensione else "da_misurare"
        risultato.append({"lotto_id": str(lotto), "creato_il": creato, "proposte": proposte, "con_task": con_task,
                          "livello": livello, "stato": stato, "campione_id": str(campione) if campione else None,
                          "dimensione_campione": dimensione, "giudicati": giudicati or 0,
                          "esito_misura": esito_misura})
    return risultato


def stato_pipeline(conn: psycopg.Connection, utente_id: str, org_id: str) -> dict[str, Any]:
    """Schermata dell'amministratore: documenti con stato e stima, candidati da proporre, lotti, lavori."""
    org_id = _uuid(org_id)
    richiedi(conn, utente_id, "gestire_dataset_centrale", org_id, risorsa="pipeline")
    schema = spazio_organizzazione(conn, org_id)
    p = prezzi(conn, org_id)
    titoli = titoli_attivi(conn) if p is not None else []
    documenti, stime = [], []
    for c in _caricamenti(conn, schema):
        testo = c.pop("testo")
        c["caratteri"] = len(testo)
        da_stimare = p is not None and c["stato"] in ("da_avviare", "fallito")
        c["stima"] = stima_documento(testo, c["ruolo"], titoli, p) if da_stimare else None
        if c["stima"]:
            stime.append(c["stima"])
        documenti.append(c)
    lavori = conn.execute(
        """SELECT job_id, kind, status, attempts, ultimo_errore, created_at FROM jobs
           WHERE org_id = %s AND kind = ANY(%s) ORDER BY created_at DESC LIMIT 20""",
        (org_id, [TIPO_SCOMPOSIZIONE, TIPO_PROPOSTA, TIPO_APPLICAZIONE]),
    ).fetchall()
    return {
        "prezzi": p, "documenti": documenti, "stima_da_avviare": _somma(stime) if stime else None,
        "candidati_da_proporre": _da_proporre(conn, schema),
        "proposta_in_coda": _job_attivo(conn, org_id, TIPO_PROPOSTA),
        "lotti": _lotti(conn, org_id),
        "lavori": [{"job_id": str(r[0]), "tipo": r[1], "stato": _STATI_JOB[r[2]], "tentativi": r[3], "errore": r[4],
                    "creato_il": r[5]} for r in lavori],
    }


def lotti(conn: psycopg.Connection, utente_id: str, org_id: str) -> list[dict[str, Any]]:
    org_id = _uuid(org_id)
    richiedi(conn, utente_id, "leggere", org_id, risorsa="lotti_abbinamento")
    return _lotti(conn, org_id)


def dettaglio_lotto(conn: psycopg.Connection, utente_id: str, org_id: str, lotto_id: str) -> dict[str, Any]:
    """Il lotto per il revisore. Revisione cieca: finché la misura del campione non c'è, si vedono solo le coppie
    del campione, senza distanze né ordine di ambiguità; dopo, la coda intera per decidere le esclusioni."""
    org_id, lotto_id = _uuid(org_id), _uuid(lotto_id)
    richiedi(conn, utente_id, "leggere", org_id, risorsa=f"lotto_abbinamento:{lotto_id}")
    lotto = next((x for x in _lotti(conn, org_id) if x["lotto_id"] == lotto_id), None)
    if lotto is None:
        raise LookupError("lotto inesistente")
    campione = None
    if lotto["campione_id"]:
        elementi = campioni.esporta_campione(conn, utente_id, lotto["campione_id"])
        miei = dict(conn.execute(
            """SELECT DISTINCT ON (posizione) posizione, esito FROM giudizi_revisione
               WHERE campione_id = %s AND revisore_id = %s ORDER BY posizione, giudizio_id DESC""",
            (lotto["campione_id"], utente_id),
        ).fetchall())
        misura = conn.execute(
            """SELECT n_elementi, n_corretti, n_parziali, n_errati, precisione, esito FROM misure_precisione
               WHERE campione_id = %s ORDER BY calcolata_il DESC LIMIT 1""", (lotto["campione_id"],),
        ).fetchone()
        campione = {"elementi": [e | {"mio_esito": miei.get(e["posizione"])} for e in elementi],
                    "istruzioni": ISTRUZIONI_ABBINAMENTO,
                    "misura": dict(zip(("n_elementi", "n_corretti", "n_parziali", "n_errati", "precisione", "esito"),
                                       misura)) if misura else None}
    visibile = lotto["stato"] in ("da_decidere", "deciso", "in_applicazione", "applicato")
    return {"lotto": lotto, "campione": campione,
            "proposte": coda_revisione(conn, utente_id, org_id, lotto_id) if visibile else None}


def crea_campione(conn: psycopg.Connection, utente_id: str, org_id: str, lotto_id: str, *, motivazione: str) -> str:
    """Campione del lotto con la quota registrata, seme dalla data (ripetibile nel giorno)."""
    return crea_campione_del_lotto(conn, utente_id, org_id, lotto_id, seme=int(date.today().strftime("%Y%m%d")),
                                   versione_istruzioni=ISTRUZIONI_ABBINAMENTO, motivazione=motivazione)
