"""Separazione di una fusione del Canonicalizer giudicata sbagliata da un revisore.

La fusione (canonicalizer.fondi) ha spostato le occorrenze del task fuso sul superstite, ha
cancellato quelle doppie per lo stesso ruolo e i collegamenti alle tassonomie del task fuso,
senza lasciare traccia dell'origine. Qui il task fuso torna attivo e le sue occorrenze si
ricostruiscono dalla scomposizione approvata (ruolo, documento, titolo, testo originale),
sia in public sia nello spazio dell'organizzazione. Il crosswalk del task riattivato va rifatto.
Ogni separazione è un atto 'correzione' nel registro; il Canonicalizer non rifonde più il task.
"""

import json
import uuid
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql

from neartech.organizzazioni import schema_organizzazione
from neartech.permessi import richiedi
from neartech.registro import registra


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
    da_spostare, da_ricreare = [], []
    for voce in voci:
        occorrenza = conn.execute(
            """SELECT o.occurrence_id FROM task_occurrences o JOIN roles r ON r.role_id = o.role_id
               WHERE o.task_id = %s AND r.org_id = %s AND r.name = %s AND o.raw_snippet = %s""",
            (superstite, org_id, voce["ruolo"], voce["testo_originale"]),
        ).fetchone()
        if occorrenza is not None:
            da_spostare.append(str(occorrenza[0]))
        else:
            da_ricreare.append(voce)
    return {"task_id": task_id, "titolo": titolo, "superstite": str(superstite),
            "da_spostare": da_spostare, "da_ricreare": da_ricreare}


def _ricrea(conn: psycopg.Connection, schema: sql.Identifier, task_id: str, superstite: str,
            org_id: str, voce: dict[str, Any]) -> None:
    ruolo = conn.execute(
        "SELECT role_id FROM roles WHERE org_id = %s AND name = %s", (org_id, voce["ruolo"])
    ).fetchone()
    fonte = conn.execute(
        "SELECT source_id FROM sources WHERE name = %s ORDER BY retrieved_at DESC LIMIT 1", (voce["documento"],)
    ).fetchone()
    if ruolo is None or fonte is None:
        raise LookupError(f"ruolo o documento della scomposizione non trovati: {voce['ruolo']!r}")
    # Modello e prompt della scomposizione: quelli dell'occorrenza del superstite nello stesso ruolo.
    origine = conn.execute(
        "SELECT model_name, prompt_hash FROM task_occurrences WHERE task_id = %s AND role_id = %s",
        (superstite, ruolo[0]),
    ).fetchone() or ("scomposizione-2026-10-11", "ricostruita")
    occorrenza = conn.execute(
        """INSERT INTO task_occurrences
             (task_id, role_id, context_note, raw_snippet, source_id, model_name, prompt_hash)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING occurrence_id""",
        (task_id, ruolo[0], voce.get("nota_contesto"), voce["testo_originale"], fonte[0], origine[0], origine[1]),
    ).fetchone()[0]
    conn.execute(
        sql.SQL("""INSERT INTO {}.documenti (documento_id, nome_file, sha256, tipo)
                   SELECT source_id, name, content_hash, kind FROM sources WHERE source_id = %s
                   ON CONFLICT (documento_id) DO NOTHING""").format(schema),
        (fonte[0],),
    )
    conn.execute(
        sql.SQL("""INSERT INTO {}.occorrenze
                     (occorrenza_id, task_id, ruolo_id, documento_id, estratto, nota_contesto, model_name, prompt_hash)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""").format(schema),
        (occorrenza, task_id, ruolo[0], fonte[0], voce["testo_originale"], voce.get("nota_contesto"),
         origine[0], origine[1]),
    )


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
        codice = conn.execute("SELECT codice FROM organizations WHERE org_id = %s", (org_id,)).fetchone()
        if codice is None or codice[0] is None:
            raise LookupError("l'organizzazione non ha uno spazio")
        schema = sql.Identifier(schema_organizzazione(codice[0]))
        for occorrenza in piano["da_spostare"]:
            conn.execute("UPDATE task_occurrences SET task_id = %s WHERE occurrence_id = %s",
                         (piano["task_id"], occorrenza))
            conn.execute(sql.SQL("UPDATE {}.occorrenze SET task_id = %s WHERE occorrenza_id = %s").format(schema),
                         (piano["task_id"], occorrenza))
        for voce in piano["da_ricreare"]:
            _ricrea(conn, schema, piano["task_id"], piano["superstite"], org_id, voce)
        conn.execute("UPDATE canonical_tasks SET status = 'active', merged_into = NULL WHERE task_id = %s",
                     (piano["task_id"],))
        esito = {"spostate": len(piano["da_spostare"]), "ricreate": len(piano["da_ricreare"])}
        registra(conn, autore_id=utente_id, tipo_oggetto="task_canonico", oggetto_id=piano["task_id"],
                 atto="correzione", motivazione=motivazione,
                 dettagli={"operazione": "scissione", "superstite": piano["superstite"], **esito,
                           "crosswalk_da_rifare": True})
        return esito
