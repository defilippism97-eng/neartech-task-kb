"""Separazione di una fusione del Canonicalizer giudicata sbagliata da un revisore.

La fusione (canonicalizer.fondi) ha spostato le occorrenze del task fuso sul superstite, ha
cancellato quelle doppie per lo stesso ruolo e i collegamenti alle tassonomie del task fuso,
senza lasciare traccia dell'origine. Qui il task fuso torna attivo e le sue occorrenze si
ricostruiscono dalla scomposizione approvata (ruolo, documento, titolo, testo originale): il
confronto avviene nello spazio dell'organizzazione, dove sta il testo (ADR 0005), e i legami
in public seguono con gli stessi identificativi. Il crosswalk del task riattivato va rifatto.
Ogni separazione è un atto 'correzione' nel registro; il Canonicalizer non rifonde più il task.
"""

import json
import uuid
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql

from neartech.occorrenze import registra_occorrenza, spazio_organizzazione
from neartech.permessi import richiedi
from neartech.registro import registra

ORIGINE_RICOSTRUITA = ("scomposizione-2026-10-11", "ricostruita")


def carica_scomposizione(percorso: Path) -> list[dict[str, Any]]:
    """Voci della scomposizione approvata, una per attività: ruolo, documento, titolo, testo originale."""
    voci = []
    for riga in percorso.read_text(encoding="utf-8").splitlines():
        if not riga.strip():
            continue
        documento = json.loads(riga)
        for attivita in documento["attivita"]:
            voci.append({"ruolo": documento["ruolo"], "documento": documento["documento"],
                         "titolo": attivita["titolo"], "testo_originale": attivita["testo_originale"],
                         "nota_contesto": attivita.get("nota_contesto")})
    return voci


def piano_scissione(
    conn: psycopg.Connection, task_id: str, scomposizione: list[dict[str, Any]], org_id: str
) -> dict[str, Any]:
    """Cosa farebbe la separazione. Sola lettura."""
    task_id = str(uuid.UUID(str(task_id)))
    riga = conn.execute(
        "SELECT title_it, status, merged_into FROM canonical_tasks WHERE task_id = %s", (task_id,)
    ).fetchone()
    if riga is None:
        raise LookupError(f"task {task_id} inesistente")
    titolo, stato, superstite = riga
    if stato != "merged" or superstite is None:
        raise ValueError(f"il task {task_id} non è fuso (stato {stato})")
    voci = [v for v in scomposizione if v["titolo"] == titolo]
    if not voci:
        raise LookupError(f"nessuna voce della scomposizione con titolo {titolo!r}")
    spazio = spazio_organizzazione(conn, org_id)
    da_spostare, da_ricreare = [], []
    for voce in voci:
        occorrenza = conn.execute(
            sql.SQL("""SELECT o.occorrenza_id FROM {0}.occorrenze o
                       JOIN {0}.ruoli_organizzativi r ON r.ruolo_id = o.ruolo_id
                       WHERE o.task_id = %s AND r.nome = %s AND o.estratto = %s""").format(spazio),
            (superstite, voce["ruolo"], voce["testo_originale"]),
        ).fetchone()
        if occorrenza is not None:
            da_spostare.append(str(occorrenza[0]))
        else:
            da_ricreare.append(voce)
    return {"task_id": task_id, "titolo": titolo, "superstite": str(superstite),
            "da_spostare": da_spostare, "da_ricreare": da_ricreare}


def _ricrea(conn: psycopg.Connection, org_id: str, task_id: str, superstite: str, voce: dict[str, Any]) -> None:
    spazio = spazio_organizzazione(conn, org_id)
    ruolo = conn.execute(
        sql.SQL("SELECT ruolo_id FROM {}.ruoli_organizzativi WHERE nome = %s").format(spazio), (voce["ruolo"],)
    ).fetchone()
    documento = conn.execute(
        sql.SQL("SELECT documento_id FROM {}.documenti WHERE nome_file = %s ORDER BY caricato_il DESC LIMIT 1")
        .format(spazio),
        (voce["documento"],),
    ).fetchone()
    if ruolo is None or documento is None:
        raise LookupError(f"ruolo o documento della scomposizione non trovati: {voce['ruolo']!r}")
    # Modello e prompt della scomposizione: quelli dell'occorrenza del superstite nello stesso ruolo.
    origine = conn.execute(
        sql.SQL("SELECT model_name, prompt_hash FROM {}.occorrenze WHERE task_id = %s AND ruolo_id = %s")
        .format(spazio),
        (superstite, ruolo[0]),
    ).fetchone()
    model_name, prompt_hash = origine if origine and origine[0] else ORIGINE_RICOSTRUITA
    registra_occorrenza(conn, org_id, task_id=task_id, ruolo_id=str(ruolo[0]), documento_id=str(documento[0]),
                        estratto=voce["testo_originale"], nota_contesto=voce.get("nota_contesto"),
                        model_name=model_name, prompt_hash=prompt_hash)


def scindi(
    conn: psycopg.Connection,
    utente_id: str,
    *,
    task_id: str,
    scomposizione: list[dict[str, Any]],
    org_id: str,
    motivazione: str,
) -> dict[str, int]:
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_dataset_centrale", risorsa=f"scissione:{task_id}")
        piano = piano_scissione(conn, task_id, scomposizione, org_id)
        spazio = spazio_organizzazione(conn, org_id)
        for occorrenza in piano["da_spostare"]:
            conn.execute("UPDATE task_occurrences SET task_id = %s WHERE occurrence_id = %s",
                         (piano["task_id"], occorrenza))
            conn.execute(sql.SQL("UPDATE {}.occorrenze SET task_id = %s WHERE occorrenza_id = %s").format(spazio),
                         (piano["task_id"], occorrenza))
        for voce in piano["da_ricreare"]:
            _ricrea(conn, org_id, piano["task_id"], piano["superstite"], voce)
        conn.execute("UPDATE canonical_tasks SET status = 'active', merged_into = NULL WHERE task_id = %s",
                     (piano["task_id"],))
        esito = {"spostate": len(piano["da_spostare"]), "ricreate": len(piano["da_ricreare"])}
        registra(conn, autore_id=utente_id, tipo_oggetto="task_canonico", oggetto_id=piano["task_id"],
                 atto="correzione", motivazione=motivazione,
                 dettagli={"operazione": "scissione", "superstite": piano["superstite"], **esito,
                           "crosswalk_da_rifare": True})
        return esito
