"""Valutazioni registrate: importazione dei giudizi di modello già prodotti (etichette silver).

Ogni giudizio è un record a sé in assessment_runs, con modello, versione della rubrica, prompt e campagna
(CLAUDE.md: un record per ogni giudizio). La versione della rubrica si registra se manca, come bozza: non
diventa corrente e non risulta approvata, perché l'approvazione è del comitato di governance.
Il titolo del dataset trova il task del dataset condiviso; un task fuso passa i suoi giudizi al superstite
(registro di metodo, sezione 8); un task ritirato resta fuori.
"""

from collections.abc import Iterable
from typing import Any

import psycopg

from neartech.permessi import richiedi
from neartech.registro import registra

VOCI = ("k1", "k2", "k3", "r", "d1", "d2", "d3", "d4")


def _task_valido(conn: psycopg.Connection, titolo: str) -> tuple[str | None, str]:
    """Task attivo con quel titolo, o il superstite se è stato fuso. Esito: task, superstite, ritirato, sconosciuto."""
    riga = conn.execute("SELECT task_id, status, merged_into FROM canonical_tasks WHERE title_it = %s",
                        (titolo,)).fetchone()
    if riga is None:
        return None, "sconosciuto"
    task_id, stato, fuso_in = str(riga[0]), riga[1], riga[2]
    esito = "task"
    visti = set()
    while stato == "merged" and fuso_in is not None and task_id not in visti:
        visti.add(task_id)
        task_id = str(fuso_in)
        stato, fuso_in = conn.execute("SELECT status, merged_into FROM canonical_tasks WHERE task_id = %s",
                                      (task_id,)).fetchone()
        esito = "su_superstite"
    if stato != "active":
        return None, "ritirato"
    return task_id, esito


def importa_giudizi_modello(
    conn: psycopg.Connection, utente_id: str, righe: Iterable[dict[str, Any]], *, campagna: str, rubrica: str,
    modello: str, prompt: str, motivazione: str,
) -> dict[str, int]:
    """righe: {"titolo", "valori": {voce: 0..4}, "motivazione"}. Un giudizio per voce; un rilancio della stessa
    campagna non duplica. Ritorna i conteggi."""
    righe = list(righe)
    for riga in righe:
        for voce, valore in riga["valori"].items():
            if voce not in VOCI or isinstance(valore, bool) or valore not in (0, 1, 2, 3, 4):
                raise ValueError(f"voce o valore fuori scala per {riga['titolo']!r}: {voce}={valore!r}")
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_dataset_centrale", risorsa=f"importazione_giudizi:{campagna}")
        conn.execute("INSERT INTO rubric_versions (version, is_current) VALUES (%s, false) ON CONFLICT DO NOTHING",
                     (rubrica,))
        esito = {"giudizi": 0, "task": 0, "su_superstite": 0, "ritirati": 0, "sconosciuti": 0}
        chiavi = {"task": "task", "su_superstite": "su_superstite", "ritirato": "ritirati", "sconosciuto": "sconosciuti"}
        for riga in righe:
            task_id, come = _task_valido(conn, riga["titolo"])
            esito[chiavi[come]] += 1
            if task_id is None:
                continue
            for voce, valore in sorted(riga["valori"].items()):
                # Lo stesso giudizio della stessa campagna non si ripete: un rilancio non duplica.
                esito["giudizi"] += conn.execute(
                    """INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind, rater_ref,
                                                    rubric_version, prompt_hash, rationale, campaign_id)
                       SELECT 'task', %(task)s, %(voce)s, %(valore)s, 'llm', %(modello)s, %(rubrica)s, %(prompt)s,
                              %(motivazione)s, %(campagna)s
                       WHERE NOT EXISTS (SELECT 1 FROM assessment_runs a
                                         WHERE a.target_kind = 'task' AND a.target_id = %(task)s
                                           AND a.item = %(voce)s AND a.campaign_id = %(campagna)s
                                           AND a.rubric_version = %(rubrica)s AND a.prompt_hash = %(prompt)s
                                           AND a.rater_ref = %(modello)s AND a.value = %(valore)s
                                           AND a.rationale IS NOT DISTINCT FROM %(motivazione)s)""",
                    {"task": task_id, "voce": voce, "valore": valore, "modello": modello, "rubrica": rubrica,
                     "prompt": prompt, "motivazione": riga.get("motivazione"), "campagna": campagna},
                ).rowcount
        # 'proposta': sono giudizi di modello, non una decisione di persone su di essi.
        registra(conn, autore_id=utente_id, tipo_oggetto="importazione_giudizi", oggetto_id=campagna,
                 atto="proposta", motivazione=motivazione,
                 dettagli={**esito, "rubrica": rubrica, "modello": modello, "prompt": prompt})
        return esito
