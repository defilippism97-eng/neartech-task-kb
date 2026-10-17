"""Percorso del pilota (fase 6; registro di metodo, sezione 27): in che fase è un'organizzazione.

Quattro fasi sul flusso a nove passi, calcolate dai dati e mai dichiarate a mano:
- avvio (passi 1-3): mansionari caricati, attività scomposte e abbinate al dataset NEARTECH, occorrenze create;
- indirizzi (passi 4-5): profilo di pesi dell'organizzazione approvato dal comitato (l'ok dell'auditor si
  aggiunge con la fetta degli indirizzi);
- verifica (passi 6-8): risultati calcolati con la configurazione vigente e giudizi di persona a campione;
- esito (passo 9): restituzione vigente approvata dal comitato.

Ogni fase è "fatta", "in corso" o "da fare"; la fase corrente è la prima non fatta. Le fasi possono sovrapporsi
(per esempio risultati provvisori con il profilo comune prima degli indirizzi): la piattaforma lo mostra.
"""

import uuid
from typing import Any

import psycopg
from psycopg import sql

from neartech.permessi import richiedi
from neartech.registro import spazio
from neartech.restituzione import restituzione_organizzazione
from neartech.sperimentazione import avanzamento_sperimentazione

FASI = ("avvio", "indirizzi", "verifica", "esito")


def _stato(fatto: bool, in_corso: bool) -> str:
    return "fatta" if fatto else "in_corso" if in_corso else "da_fare"


def stato_percorso(conn: psycopg.Connection, utente_id: str, org_id: str, *,
                   restituzione: dict[str, Any] | None = None,
                   avanzamento: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fasi del percorso con i fatti che le determinano. Serve il permesso leggere. Restituzione e avanzamento
    si possono passare se chi chiama li ha già letti nella stessa transazione."""
    org_id = str(uuid.UUID(str(org_id)))
    richiedi(conn, utente_id, "leggere", org_id, risorsa=f"percorso:{org_id}")
    schema = spazio(conn, org_id)
    if schema is None:
        raise LookupError(f"l'organizzazione {org_id} non ha uno spazio")
    restituzione = restituzione or restituzione_organizzazione(conn, utente_id, org_id)
    avanzamento = avanzamento or avanzamento_sperimentazione(conn, utente_id, org_id)

    documenti = conn.execute(sql.SQL("SELECT count(*) FROM {}.documenti").format(schema)).fetchone()[0]
    candidati, in_attesa = conn.execute(sql.SQL(
        """SELECT count(DISTINCT candidato_id),
                  count(DISTINCT candidato_id) FILTER (WHERE atto_applicazione IS NULL)
           FROM {}.v_abbinamenti""").format(schema)).fetchone()
    occorrenze = restituzione["riepilogo"]["occorrenze"]
    profilo = conn.execute(
        """SELECT profile_id FROM weight_profiles
           WHERE org_id = %s AND is_active AND approved_by IS NOT NULL""", (org_id,)).fetchone()
    # Ultimo profilo proposto dal comitato e non ancora attivo: chi deve ancora decidere (comitato o auditor).
    proposto = conn.execute(
        """SELECT p.profile_id,
                  EXISTS (SELECT 1 FROM registro_decisioni a WHERE a.tipo_oggetto = 'profilo_pesi'
                          AND a.oggetto_id = p.profile_id AND a.org_id = p.org_id AND a.atto = 'approvazione'),
                  EXISTS (SELECT 1 FROM registro_decisioni a WHERE a.tipo_oggetto = 'profilo_pesi'
                          AND a.oggetto_id = p.profile_id AND a.org_id = p.org_id AND a.atto = 'verifica')
           FROM weight_profiles p
           JOIN registro_decisioni r ON r.tipo_oggetto = 'profilo_pesi' AND r.oggetto_id = p.profile_id
                                    AND r.atto = 'proposta' AND r.org_id = p.org_id
           WHERE p.org_id = %s AND NOT p.is_active AND p.approved_by IS NULL
           ORDER BY r.posizione DESC LIMIT 1""", (org_id,)).fetchone()
    risultati = restituzione["riepilogo"]["con_risultato"]
    instabili = restituzione["riepilogo"]["instabili"]

    avvio = _stato(occorrenze > 0 and in_attesa == 0, documenti > 0 or candidati > 0)
    indirizzi = _stato(profilo is not None, avvio == "fatta" or proposto is not None)
    verifica = _stato(indirizzi == "fatta" and risultati > 0 and instabili == 0, risultati > 0)
    esito = _stato(restituzione["approvazione"] is not None, verifica == "fatta")
    stati = {"avvio": avvio, "indirizzi": indirizzi, "verifica": verifica, "esito": esito}
    corrente = next((f for f in FASI if stati[f] != "fatta"), "esito")
    return {
        "fase_corrente": corrente,
        "fasi": [
            {"codice": "avvio", "stato": avvio,
             "fatti": {"documenti": documenti, "attivita": candidati, "in_attesa_di_abbinamento": in_attesa,
                       "occorrenze": occorrenze}},
            {"codice": "indirizzi", "stato": indirizzi,
             "fatti": {"profilo_proprio": profilo[0] if profilo else None,
                       "profilo_in_uso": (restituzione["chiavi"]["profili"] or [None])[0],
                       "proposta": None if proposto is None else
                       {"profile_id": proposto[0], "approvata": proposto[1], "verificata": proposto[2]}}},
            {"codice": "verifica", "stato": verifica,
             "fatti": {"risultati": risultati, "da_confermare": instabili,
                       "quota_giudizi_di_persona": avanzamento["quota"]}},
            {"codice": "esito", "stato": esito,
             "fatti": {"approvazione": restituzione["approvazione"], "impronta": restituzione["impronta"]}},
        ],
    }
