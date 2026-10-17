"""Campioni di revisione e giudizi delle persone sulle proposte del sistema (fase 2).

Un campione estrae elementi da un insieme di proposte (crosswalk verso le tassonomie,
fusioni del Canonicalizer; in fase 3 gli abbinamenti) con un criterio registrato: tutti,
oppure casuale con seme. Il revisore vede la proposta senza la motivazione né la fonte
del modello (revisione cieca). Ogni giudizio è un record; un ripensamento è un record nuovo.
Gli elementi contengono solo identificativi del dataset condiviso, mai testo del cliente,
più la fotografia del modello e del prompt che hanno prodotto la proposta.
Non va confuso con crosswalk.registra_giudizio, che registra i giudizi del modello.
La nota del revisore è testo libero: sta nello spazio dell'organizzazione (note_giudizi), e nel giudizio
in public resta la sua impronta con la chiave dello spazio (ADR 0004, migrazione 0028).
"""

import random
import uuid
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from neartech.permessi import richiedi
from neartech.registro import chiave_spazio, impronta, registra, spazio

ESITI = ("corretto", "parziale", "errato")
CRITERI = ("tutte", "casuale")
# Filtri ammessi per tipo di proposta -> colonna della tabella di origine (nomi fissi, mai dal chiamante).
_FILTRI = {
    "fusione": {"decisione": "decisione"},
    "crosswalk": {"relation": "relation"},
}
_ESITI_CROSSWALK = {"ok": "corretto", "parziale": "parziale", "no": "errato"}

Elemento = tuple[dict[str, str], dict[str, str]]  # (riferimento, origine)


class ElementoMancante(LookupError):
    """Una proposta del campione non esiste più (per esempio dopo una fusione di task)."""

    def __init__(self, posizioni: list[int]):
        super().__init__(f"proposte non più presenti alle posizioni {posizioni}")
        self.posizioni = posizioni


class GiaImportato(RuntimeError):
    """Il campione già rivisto è stato importato in precedenza."""


def popolazione(conn: psycopg.Connection, tipo: str, filtro: dict[str, Any]) -> list[Elemento]:
    """Proposte candidate, in ordine stabile per identificativo. Sola lettura."""
    if tipo not in _FILTRI:
        raise ValueError(f"tipo di proposta non gestito: {tipo!r}")
    sconosciuti = set(filtro) - set(_FILTRI[tipo])
    if sconosciuti:
        raise ValueError(f"filtri non ammessi per {tipo}: {sorted(sconosciuti)}")
    condizioni = " AND ".join(f"{_FILTRI[tipo][chiave]} = %({chiave})s" for chiave in sorted(filtro)) or "true"
    if tipo == "fusione":
        righe = conn.execute(
            f"""SELECT proposal_id, model_name, prompt_hash FROM fusioni_proposte
                WHERE {condizioni} ORDER BY proposal_id""",
            filtro,
        ).fetchall()
        return [({"proposal_id": str(r[0])}, {"model_name": r[1], "prompt_hash": r[2]}) for r in righe]
    righe = conn.execute(
        f"""SELECT task_id, node_id, model_name, prompt_hash FROM task_mappings
            WHERE {condizioni} ORDER BY task_id, node_id""",
        filtro,
    ).fetchall()
    return [({"task_id": str(r[0]), "node_id": str(r[1])}, {"model_name": r[2], "prompt_hash": r[3]})
            for r in righe]


def _salva_campione(
    conn: psycopg.Connection,
    utente_id: str,
    *,
    org_id: str,
    tipo: str,
    filtro: dict[str, Any],
    criterio: str,
    seme: int | None,
    popolazione_totale: int,
    elementi: list[Elemento],
    versione_istruzioni: str,
    motivazione: str,
    dettagli: dict[str, Any] | None = None,
    dettagli_riservati: dict[str, Any] | None = None,
) -> str:
    campione_id = str(uuid.uuid4())
    decisione = registra(
        conn, autore_id=utente_id, tipo_oggetto="campione_revisione", oggetto_id=campione_id,
        atto="approvazione", motivazione=motivazione, org_id=org_id,
        dettagli={"tipo": tipo, "filtro": filtro, "criterio": criterio, "seme": seme,
                  "popolazione": popolazione_totale, "dimensione": len(elementi), **(dettagli or {})},
        dettagli_riservati=dettagli_riservati,
    )
    conn.execute(
        """INSERT INTO campioni_revisione
             (campione_id, org_id, tipo_proposta, filtro, criterio, seme, popolazione, dimensione,
              versione_istruzioni, decisione_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (campione_id, org_id, tipo, Jsonb(filtro), criterio, seme, popolazione_totale, len(elementi),
         versione_istruzioni, decisione),
    )
    for posizione, (riferimento, origine) in enumerate(elementi, start=1):
        conn.execute(
            "INSERT INTO elementi_campione (campione_id, posizione, riferimento, origine) VALUES (%s, %s, %s, %s)",
            (campione_id, posizione, Jsonb(riferimento), Jsonb(origine)),
        )
    return campione_id


def crea_campione(
    conn: psycopg.Connection,
    utente_id: str,
    *,
    org_id: str,
    tipo: str,
    filtro: dict[str, Any],
    criterio: str,
    versione_istruzioni: str,
    motivazione: str,
    dimensione: int | None = None,
    seme: int | None = None,
) -> str:
    """Estrae il campione e lo registra. 'tutte' prende l'intera popolazione; 'casuale' richiede dimensione e seme."""
    if criterio not in CRITERI:
        raise ValueError(f"criterio sconosciuto: {criterio!r}")
    if criterio == "tutte" and (dimensione is not None or seme is not None):
        raise ValueError("con il criterio 'tutte' dimensione e seme non si indicano")
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_campioni", org_id, risorsa=f"campione:{tipo}")
        candidati = popolazione(conn, tipo, filtro)
        if not candidati:
            raise ValueError("la popolazione delle proposte è vuota")
        if criterio == "tutte":
            scelti = candidati
        else:
            if dimensione is None or seme is None:
                raise ValueError("il campione casuale richiede dimensione e seme")
            if not 0 < dimensione <= len(candidati):
                raise ValueError(f"dimensione {dimensione} fuori dalla popolazione di {len(candidati)}")
            scelti = random.Random(seme).sample(candidati, dimensione)
        return _salva_campione(conn, utente_id, org_id=org_id, tipo=tipo, filtro=filtro, criterio=criterio,
                               seme=seme, popolazione_totale=len(candidati), elementi=scelti,
                               versione_istruzioni=versione_istruzioni, motivazione=motivazione)


def _campione(conn: psycopg.Connection, campione_id: str) -> tuple[str, str, int, str]:
    riga = conn.execute(
        """SELECT org_id, tipo_proposta, dimensione, versione_istruzioni
           FROM campioni_revisione WHERE campione_id = %s""",
        (campione_id,),
    ).fetchone()
    if riga is None:
        raise LookupError(f"campione {campione_id} inesistente")
    return str(riga[0]), riga[1], riga[2], riga[3]


def esporta_campione(conn: psycopg.Connection, utente_id: str, campione_id: str) -> list[dict[str, Any]]:
    """Elementi da rivedere, senza motivazione, modello o versione del prompt (revisione cieca).

    Se una proposta del campione non esiste più l'esportazione si ferma: il revisore deve vedere
    tutti gli elementi che la misura conterà.
    """
    campione_id = str(uuid.UUID(str(campione_id)))
    org_id, tipo, dimensione, _ = _campione(conn, campione_id)
    richiedi(conn, utente_id, "leggere", org_id, risorsa=f"campione:{campione_id}")
    if tipo == "fusione":
        righe = conn.execute(
            """SELECT e.posizione, a.title_it, b.title_it, f.decisione
               FROM elementi_campione e
               JOIN fusioni_proposte f ON f.proposal_id = (e.riferimento ->> 'proposal_id')::uuid
               JOIN canonical_tasks a ON a.task_id = f.task_id
               JOIN canonical_tasks b ON b.task_id = f.altro_task_id
               WHERE e.campione_id = %s ORDER BY e.posizione""",
            (campione_id,),
        ).fetchall()
        esportati = [
            {"posizione": r[0], "task_a": r[1], "task_b": r[2],
             "proposta": "stessa attività" if r[3] == "stessa_attivita" else "attività diverse"}
            for r in righe
        ]
    else:
        righe = conn.execute(
            """SELECT e.posizione, t.title_it, n.scheme, n.code, n.label, m.relation
               FROM elementi_campione e
               JOIN task_mappings m ON m.task_id = (e.riferimento ->> 'task_id')::uuid
                                   AND m.node_id = (e.riferimento ->> 'node_id')::uuid
               JOIN canonical_tasks t ON t.task_id = m.task_id
               JOIN taxonomy_nodes n ON n.node_id = m.node_id
               WHERE e.campione_id = %s ORDER BY e.posizione""",
            (campione_id,),
        ).fetchall()
        esportati = [
            {"posizione": r[0], "task": r[1], "nodo": f"{r[2]} {r[3]}: {r[4]}", "proposta": f"relazione {r[5]}"}
            for r in righe
        ]
    if len(esportati) != dimensione:
        presenti = {r["posizione"] for r in esportati}
        raise ElementoMancante([p for p in range(1, dimensione + 1) if p not in presenti])
    return esportati


def registra_giudizio(
    conn: psycopg.Connection,
    revisore_id: str,
    campione_id: str,
    posizione: int,
    esito: str,
    *,
    nota: str | None,
    versione_istruzioni: str,
) -> int:
    if esito not in ESITI:
        raise ValueError(f"esito sconosciuto: {esito!r}")
    campione_id = str(uuid.UUID(str(campione_id)))
    with conn.transaction():
        org_id, _, _, versione_campione = _campione(conn, campione_id)
        richiedi(conn, revisore_id, "giudicare_task", org_id, risorsa=f"campione:{campione_id}:{posizione}")
        if versione_istruzioni != versione_campione:
            raise ValueError(f"il campione usa le istruzioni {versione_campione!r}, non {versione_istruzioni!r}")
        schema, hash_nota = None, None
        if nota is not None and nota.strip():
            schema = spazio(conn, org_id)
            if schema is None:
                raise LookupError(f"l'organizzazione {org_id} non ha uno spazio: la nota non ha dove stare")
            hash_nota = impronta(chiave_spazio(conn, schema), nota)
        giudizio_id = conn.execute(
            """INSERT INTO giudizi_revisione
                 (campione_id, posizione, esito, hash_nota, revisore_id, versione_istruzioni)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING giudizio_id""",
            (campione_id, posizione, esito, hash_nota, revisore_id, versione_istruzioni),
        ).fetchone()[0]
        if schema is not None:
            conn.execute(
                sql.SQL("INSERT INTO {}.note_giudizi (giudizio_id, nota) VALUES (%s, %s)").format(schema),
                (giudizio_id, nota),
            )
        return giudizio_id


def importa_revisioni_crosswalk(
    conn: psycopg.Connection, revisore_id: str, *, org_id: str, campione: str,
    popolazione_originale: int | None = None,
    versione_istruzioni: str = "revisione-crosswalk-2026-10-11",
) -> str:
    """Porta un campione già rivisto in revisioni_crosswalk nel modello generale di campioni e giudizi.

    Chi importa dichiara di essere il revisore originale: i giudizi portano il suo identificativo,
    e il nome registrato all'epoca resta nei dettagli dell'atto. popolazione_originale è il numero
    di relazioni da cui il campione era stato estratto; se manca si registra la dimensione.
    """
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, revisore_id, "gestire_campioni", org_id, risorsa=f"importazione:{campione}")
        conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"importazione:{campione}",))
        if conn.execute(
            """SELECT EXISTS (SELECT 1 FROM campioni_revisione
                              WHERE tipo_proposta = 'crosswalk' AND criterio = 'importato'
                                AND filtro ->> 'campione' = %s)""",
            (campione,),
        ).fetchone()[0]:
            raise GiaImportato(f"il campione {campione!r} è già stato importato")
        righe = conn.execute(
            """SELECT r.task_id, r.node_id, r.esito, r.nota, r.revisore, m.model_name, m.prompt_hash
               FROM revisioni_crosswalk r
               LEFT JOIN task_mappings m ON m.task_id = r.task_id AND m.node_id = r.node_id
               WHERE r.campione = %s ORDER BY r.task_id, r.node_id""",
            (campione,),
        ).fetchall()
        if not righe:
            raise LookupError(f"nessuna revisione per il campione {campione!r}")
        elementi = [
            ({"task_id": str(r[0]), "node_id": str(r[1])},
             {"model_name": r[5], "prompt_hash": r[6]} if r[5] else {})
            for r in righe
        ]
        campione_id = _salva_campione(
            conn, revisore_id, org_id=org_id, tipo="crosswalk", filtro={"campione": campione},
            criterio="importato", seme=None, popolazione_totale=popolazione_originale or len(elementi),
            elementi=elementi, versione_istruzioni=versione_istruzioni,
            motivazione=f"importazione del campione già rivisto {campione}",
            dettagli={"revisione_cieca": False},
            dettagli_riservati={"revisori_originali": sorted({r[4] for r in righe})},
        )
        for posizione, riga in enumerate(righe, start=1):
            registra_giudizio(conn, revisore_id, campione_id, posizione, _ESITI_CROSSWALK[riga[2]],
                              nota=riga[3], versione_istruzioni=versione_istruzioni)
        return campione_id
