"""Metrica di precisione su un campione rivisto (fase 2): calcolo deterministico.

Precisione = giudizi corretti / giudizi considerati, con la regola sui parziali presa dal
parametro di governance `regola_parziali` (errore, corretto, escluso). Intervallo di Wilson al
livello `livello_confidenza`; confronto con `soglia_precisione_abbinamento`. Senza parametri
approvati il calcolo si ferma. Per ogni elemento conta l'ultimo giudizio di ciascun revisore;
se i revisori non concordano il calcolo si ferma: la risoluzione è una decisione delle persone.
Ogni misura registra i parametri usati, l'origine delle proposte e la versione del calcolo.
"""

import math
import uuid
from dataclasses import dataclass
from statistics import NormalDist

import psycopg
from psycopg.types.json import Jsonb

from neartech.governance import parametro_vigente
from neartech.permessi import richiedi

VERSIONE_CALCOLO = "precisione-wilson-1"
REGOLE_PARZIALI = ("errore", "corretto", "escluso")
PARAMETRO_SOGLIA = "soglia_precisione_abbinamento"
PARAMETRO_REGOLA = "regola_parziali"
PARAMETRO_LIVELLO = "livello_confidenza"


class CampioneIncompleto(RuntimeError):
    def __init__(self, posizioni: list[int]):
        super().__init__(f"elementi senza giudizio: {posizioni}")
        self.posizioni = posizioni


class DisaccordoRevisori(RuntimeError):
    def __init__(self, posizioni: list[int]):
        super().__init__(f"revisori in disaccordo sugli elementi: {posizioni}")
        self.posizioni = posizioni


@dataclass(frozen=True)
class Misura:
    misura_id: str
    n_elementi: int
    n_corretti: int
    n_parziali: int
    n_errati: int
    precisione: float
    intervallo: tuple[float, float]
    esito: str


def intervallo_wilson(successi: int, totale: int, livello: float) -> tuple[float, float]:
    if totale <= 0 or not 0 <= successi <= totale:
        raise ValueError("conteggi non validi per l'intervallo")
    if not 0 < livello < 1:
        raise ValueError("livello di confidenza fuori da (0, 1)")
    z = NormalDist().inv_cdf((1 + livello) / 2)
    p = successi / totale
    denominatore = 1 + z * z / totale
    centro = (p + z * z / (2 * totale)) / denominatore
    margine = z * math.sqrt(p * (1 - p) / totale + z * z / (4 * totale * totale)) / denominatore
    return max(0.0, centro - margine), min(1.0, centro + margine)


def _valore(parametro, ammessi=None) -> float | str:
    valore = parametro.valore.get("valore") if isinstance(parametro.valore, dict) else None
    if ammessi is not None:
        if valore not in ammessi:
            raise ValueError(f"valore non ammesso per {parametro.codice}: {valore!r}")
        return valore
    if not isinstance(valore, (int, float)) or not 0 < valore < 1:
        raise ValueError(f"valore non valido per {parametro.codice}: {valore!r}")
    return float(valore)


def _origine(conn: psycopg.Connection, campione_id: str, tipo: str) -> list[dict[str, str]]:
    if tipo == "fusione":
        righe = conn.execute(
            """SELECT DISTINCT f.model_name, f.prompt_hash
               FROM elementi_campione e
               JOIN fusioni_proposte f ON f.proposal_id = (e.riferimento ->> 'proposal_id')::uuid
               WHERE e.campione_id = %s ORDER BY 1, 2""",
            (campione_id,),
        ).fetchall()
    else:
        righe = conn.execute(
            """SELECT DISTINCT m.model_name, m.prompt_hash
               FROM elementi_campione e
               JOIN task_mappings m ON m.task_id = (e.riferimento ->> 'task_id')::uuid
                                   AND m.node_id = (e.riferimento ->> 'node_id')::uuid
               WHERE e.campione_id = %s ORDER BY 1, 2""",
            (campione_id,),
        ).fetchall()
    return [{"model_name": r[0], "prompt_hash": r[1]} for r in righe]


def calcola_precisione(conn: psycopg.Connection, utente_id: str, campione_id: str) -> Misura:
    campione_id = str(uuid.UUID(str(campione_id)))
    with conn.transaction():
        riga = conn.execute(
            "SELECT org_id, tipo_proposta, dimensione FROM campioni_revisione WHERE campione_id = %s",
            (campione_id,),
        ).fetchone()
        if riga is None:
            raise LookupError(f"campione {campione_id} inesistente")
        org_id, tipo, dimensione = str(riga[0]), riga[1], riga[2]
        richiedi(conn, utente_id, "gestire_campioni", org_id, risorsa=f"misura:{campione_id}")

        soglia_p = parametro_vigente(conn, PARAMETRO_SOGLIA, org_id)
        regola_p = parametro_vigente(conn, PARAMETRO_REGOLA, org_id)
        livello_p = parametro_vigente(conn, PARAMETRO_LIVELLO, org_id)
        soglia, livello = _valore(soglia_p), _valore(livello_p)
        regola = _valore(regola_p, REGOLE_PARZIALI)

        ultimi = conn.execute(
            """SELECT DISTINCT ON (posizione, revisore_id) posizione, revisore_id, esito
               FROM giudizi_revisione WHERE campione_id = %s
               ORDER BY posizione, revisore_id, giudizio_id DESC""",
            (campione_id,),
        ).fetchall()
        per_elemento: dict[int, set[str]] = {}
        for posizione, _, esito in ultimi:
            per_elemento.setdefault(posizione, set()).add(esito)
        mancanti = [p for p in range(1, dimensione + 1) if p not in per_elemento]
        if mancanti:
            raise CampioneIncompleto(mancanti)
        disaccordi = sorted(p for p, esiti in per_elemento.items() if len(esiti) > 1)
        if disaccordi:
            raise DisaccordoRevisori(disaccordi)

        esiti = [next(iter(e)) for e in per_elemento.values()]
        corretti, parziali, errati = (esiti.count(x) for x in ("corretto", "parziale", "errato"))
        if regola == "errore":
            successi, totale = corretti, corretti + parziali + errati
        elif regola == "corretto":
            successi, totale = corretti + parziali, corretti + parziali + errati
        else:
            successi, totale = corretti, corretti + errati
        if totale == 0:
            raise ValueError("nessun giudizio utile al calcolo con la regola sui parziali vigente")
        precisione = successi / totale
        intervallo = intervallo_wilson(successi, totale, livello)
        esito = "sopra_soglia" if precisione >= soglia else "sotto_soglia"

        misura_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO misure_precisione
                 (misura_id, campione_id, n_elementi, n_corretti, n_parziali, n_errati,
                  regola_parziali, parametro_regola_id, precisione, intervallo_basso, intervallo_alto,
                  livello_confidenza, parametro_confidenza_id, soglia, parametro_soglia_id, esito,
                  origine_proposte, versione_calcolo, calcolata_da)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (misura_id, campione_id, dimensione, corretti, parziali, errati, regola, regola_p.parametro_id,
             precisione, intervallo[0], intervallo[1], livello, livello_p.parametro_id, soglia,
             soglia_p.parametro_id, esito, Jsonb(_origine(conn, campione_id, tipo)), VERSIONE_CALCOLO, utente_id),
        )
        return Misura(misura_id, dimensione, corretti, parziali, errati, precisione, intervallo, esito)
