"""Abbinamento dei task di un'organizzazione al dataset consolidato (fase 3, ADR 0006).

1. Le attività estratte da un documento sono candidati nello spazio dell'organizzazione (salva_candidati).
2. Un lotto propone per ogni candidato il task attivo più vicino per embedding (proponi_abbinamenti):
   distanza, margine sul secondo e vicini restano registrati. Nessuna soglia di distanza.
3. La coda di revisione ordina per ambiguità (coda_revisione); il campione del lotto ha la dimensione
   data dalla quota approvata (crea_campione_del_lotto) e si misura con la metrica della fase 2.
4. Il revisore decide il lotto in blocco (decidi_lotto); l'applicazione è deterministica (applica_lotto):
   approvata, occorrenza sul task del dataset; rifiutata o senza task vicino, task nuovo.

Gli agenti propongono, il codice calcola, le persone decidono. Ogni passo lascia un atto nel registro;
titoli, estratti e note dei candidati stanno nello spazio fino a quando un task nuovo entra nel dataset.
"""

import math
import uuid
from collections.abc import Callable, Sequence
from decimal import Decimal
from typing import Any, Protocol

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from neartech import campioni
from neartech.crosswalk import EMBEDDING_MODEL, una_riga
from neartech.governance import DecisioneGiaPresa, parametro_vigente
from neartech.occorrenze import documento, registra_occorrenza, ruolo, spazio_organizzazione
from neartech.permessi import richiedi
from neartech.registro import registra

MODELLO_EMBEDDING = EMBEDDING_MODEL
VICINI = 5  # come il Canonicalizer: quanti task vicini si registrano, non una soglia
PARAMETRO_QUOTA = "quota_revisione_abbinamenti"
LIVELLI = ("campione", "completa", "nulla")

# Funzione di embedding. Se ha l'attributo `modello`, deve coincidere con il modello del lotto.
Incorpora = Callable[[list[str]], Sequence[Sequence[float]]]


class TaskNonAttivo(LookupError):
    """Il task proposto o con lo stesso titolo non è più attivo (ritirato): il candidato va riproposto."""


class AttivitaCandidata(Protocol):
    titolo: str
    granularita: int
    testo_originale: str
    nota_contesto: str | None


def _uuid(valore: str) -> str:
    return str(uuid.UUID(str(valore)))


def _vettore(v: Sequence[float]) -> str:
    return "[" + ",".join(f"{float(x):.6f}" for x in v) + "]"


def _blocca(conn: psycopg.Connection, chiave: str) -> None:
    conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (chiave,))


def _vettori(incorpora: Incorpora, titoli: list[str], modello: str) -> Sequence[Sequence[float]]:
    dichiarato = getattr(incorpora, "modello", None)
    if dichiarato is not None and dichiarato != modello:
        raise ValueError(f"embedding con {dichiarato}, ma il lotto usa {modello}")
    vettori = incorpora(titoli)
    if len(vettori) != len(titoli):
        raise ValueError("l'embedding non ha restituito un vettore per titolo")
    return vettori


def dimensione_campione(quota: str | float | Decimal, popolazione: int) -> int:
    """Quota per numero di proposte, arrotondata per eccesso, in aritmetica decimale (0,07 × 100 = 7)."""
    return max(1, math.ceil(Decimal(str(quota)) * popolazione))


def _lotto(conn: psycopg.Connection, schema: sql.Identifier, lotto_id: str) -> tuple[str, str | None, str, int]:
    riga = conn.execute(
        sql.SQL("SELECT livello_revisione, parametro_quota_id, modello_embedding, vicini "
                "FROM {}.lotti_abbinamento WHERE lotto_id = %s").format(schema), (lotto_id,),
    ).fetchone()
    if riga is None:
        raise LookupError(f"lotto {lotto_id} inesistente")
    return riga[0], (str(riga[1]) if riga[1] else None), riga[2], riga[3]


# --- candidati ---------------------------------------------------------------------

def salva_candidati(
    conn: psycopg.Connection, org_id: str, *, ruolo_nome: str, nome_file: str, sha256: str, licenza: str,
    attivita: Sequence[AttivitaCandidata], model_name: str, prompt_hash: str,
) -> int:
    """Attività di un documento come candidati nello spazio. Le aree di responsabilità (granularità 3) non
    sono task e restano fuori. Ritorna i candidati nuovi; un rilancio non duplica.

    Scrittura di basso livello, senza permessi né atto: la usa neartech.scomposizione.carica_candidati."""
    schema = spazio_organizzazione(conn, org_id)
    ruolo_id = ruolo(conn, org_id, ruolo_nome)
    documento_id = documento(conn, org_id, nome_file=nome_file, sha256=sha256, licenza=licenza)
    nuovi = 0
    for att in attivita:
        if att.granularita not in (1, 2):
            continue
        nuovi += conn.execute(
            sql.SQL("""INSERT INTO {}.candidati (documento_id, ruolo_id, titolo, granularita, estratto,
                                               nota_contesto, model_name, prompt_hash)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (documento_id, ruolo_id, titolo) DO NOTHING""").format(schema),
            (documento_id, ruolo_id, una_riga(att.titolo), att.granularita, att.testo_originale,
             att.nota_contesto, model_name, prompt_hash),
        ).rowcount
    return nuovi


# --- proposte ----------------------------------------------------------------------

def _quota(conn: psycopg.Connection, org_id: str) -> tuple[str, float]:
    """Parametro della quota vigente per l'organizzazione (proprio o comune) e il suo valore in (0, 1]."""
    parametro = parametro_vigente(conn, PARAMETRO_QUOTA, org_id)
    valore = parametro.valore.get("valore") if isinstance(parametro.valore, dict) else None
    if isinstance(valore, bool) or not isinstance(valore, (int, float)) or not 0 < valore <= 1:
        raise ValueError(f"valore non ammesso per {PARAMETRO_QUOTA}: {valore!r}")
    return parametro.parametro_id, float(valore)


def proponi_abbinamenti(
    conn: psycopg.Connection, utente_id: str, org_id: str, *, livello_revisione: str, incorpora: Incorpora,
    motivazione: str, vicini: int = VICINI, modello_embedding: str = MODELLO_EMBEDDING,
) -> str:
    """Un lotto con una proposta per ogni candidato non ancora proposto. Ritorna l'identificativo del lotto."""
    if livello_revisione not in LIVELLI:
        raise ValueError(f"livello di revisione sconosciuto: {livello_revisione!r}")
    if vicini < 1:
        raise ValueError("servono almeno un vicino")
    org_id = _uuid(org_id)
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_dataset_centrale", org_id, risorsa="abbinamento")
        schema = spazio_organizzazione(conn, org_id)
        _blocca(conn, f"abbinamento:{org_id}")
        candidati = conn.execute(
            sql.SQL("""SELECT c.candidato_id, c.titolo FROM {0}.candidati c
                       WHERE NOT EXISTS (SELECT 1 FROM {0}.proposte_abbinamento p
                                         WHERE p.candidato_id = c.candidato_id)
                       ORDER BY c.creato_il, c.candidato_id""").format(schema),
        ).fetchall()
        if not candidati:
            raise ValueError("nessun candidato da proporre")
        quota_id = _quota(conn, org_id)[0] if livello_revisione == "campione" else None
        vettori = _vettori(incorpora, [r[1] for r in candidati], modello_embedding)
        lotto_id = str(uuid.uuid4())
        atto = registra(conn, autore_id=utente_id, tipo_oggetto="lotto_abbinamento", oggetto_id=lotto_id,
                        atto="proposta", motivazione=motivazione, org_id=org_id,
                        dettagli={"candidati": len(candidati), "livello_revisione": livello_revisione,
                                  "vicini": vicini})
        conn.execute(
            sql.SQL("""INSERT INTO {}.lotti_abbinamento
                         (lotto_id, decisione_id, modello_embedding, vicini, livello_revisione, parametro_quota_id)
                       VALUES (%s, %s, %s, %s, %s, %s)""").format(schema),
            (lotto_id, atto, modello_embedding, vicini, livello_revisione, quota_id),
        )
        for (candidato_id, _), vettore in zip(candidati, vettori):
            vicini_trovati = conn.execute(
                """SELECT t.task_id, (e.vec <=> %s::vector) AS distanza
                   FROM canonical_tasks t
                   JOIN task_embeddings e ON e.task_id = t.task_id AND e.model_name = %s
                   WHERE t.status = 'active' AND t.granularity IN (1, 2)
                   ORDER BY distanza, t.task_id LIMIT %s""",
                (_vettore(vettore), modello_embedding, vicini),
            ).fetchall()
            primo = vicini_trovati[0] if vicini_trovati else (None, None)
            margine = vicini_trovati[1][1] - primo[1] if len(vicini_trovati) > 1 else None
            conn.execute(
                sql.SQL("""INSERT INTO {}.proposte_abbinamento
                             (proposta_id, lotto_id, candidato_id, task_id, distanza, margine, vicini)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""").format(schema),
                (str(uuid.uuid4()), lotto_id, candidato_id, primo[0], primo[1], margine,
                 Jsonb([{"task_id": str(t), "distanza": float(d)} for t, d in vicini_trovati])),
            )
        return lotto_id


def coda_revisione(conn: psycopg.Connection, utente_id: str, org_id: str, lotto_id: str) -> list[dict[str, Any]]:
    """Proposte del lotto dalla più ambigua: margine sul secondo vicino crescente, poi distanza decrescente.
    È un ordinamento, non un filtro. Un solo vicino (margine ignoto) va in testa: l'ambiguità non è misurabile.
    Le proposte senza task vicino vanno in fondo: diventano task nuovi."""
    org_id, lotto_id = _uuid(org_id), _uuid(lotto_id)
    richiedi(conn, utente_id, "leggere", org_id, risorsa=f"lotto_abbinamento:{lotto_id}")
    schema = spazio_organizzazione(conn, org_id)
    _lotto(conn, schema, lotto_id)
    righe = conn.execute(
        sql.SQL("""SELECT p.proposta_id, c.titolo, p.task_id, t.title_it, p.distanza, p.margine
                   FROM {0}.proposte_abbinamento p JOIN {0}.candidati c USING (candidato_id)
                   LEFT JOIN canonical_tasks t ON t.task_id = p.task_id
                   WHERE p.lotto_id = %s
                   ORDER BY p.task_id IS NULL, p.margine ASC NULLS FIRST, p.distanza DESC, p.proposta_id"""
                ).format(schema),
        (lotto_id,),
    ).fetchall()
    return [{"proposta_id": str(r[0]), "candidato": r[1], "task_id": str(r[2]) if r[2] else None,
             "task_proposto": r[3], "distanza": r[4], "margine": r[5]} for r in righe]


# --- campione ----------------------------------------------------------------------

def crea_campione_del_lotto(
    conn: psycopg.Connection, utente_id: str, org_id: str, lotto_id: str, *, seme: int,
    versione_istruzioni: str, motivazione: str,
) -> str:
    """Campione di revisione del lotto: casuale con la quota registrata nel lotto (arrotondata per eccesso),
    oppure tutte le proposte se la revisione è completa. Un lotto senza revisione non ha campione."""
    org_id, lotto_id = _uuid(org_id), _uuid(lotto_id)
    richiedi(conn, utente_id, "gestire_campioni", org_id, risorsa=f"lotto_abbinamento:{lotto_id}")
    schema = spazio_organizzazione(conn, org_id)
    livello, quota_id, _, _ = _lotto(conn, schema, lotto_id)
    filtro = {"lotto": lotto_id}
    if livello == "nulla":
        raise ValueError("il lotto ha livello di revisione 'nulla': nessun campione")
    if livello == "completa":
        return campioni.crea_campione(conn, utente_id, org_id=org_id, tipo="abbinamento", filtro=filtro,
                                      criterio="tutte", versione_istruzioni=versione_istruzioni,
                                      motivazione=motivazione)
    popolazione = len(campioni.popolazione(conn, "abbinamento", filtro, org_id))
    if popolazione == 0:
        raise ValueError("il lotto non ha proposte con un task vicino")
    dimensione = _dimensione_attesa(conn, quota_id, popolazione)
    return campioni.crea_campione(conn, utente_id, org_id=org_id, tipo="abbinamento", filtro=filtro,
                                  criterio="casuale", dimensione=dimensione, seme=seme,
                                  versione_istruzioni=versione_istruzioni, motivazione=motivazione)


def _dimensione_attesa(conn: psycopg.Connection, quota_id: str, popolazione: int) -> int:
    # La quota è quella vigente quando il lotto è nato, non quella di oggi: il campione resta ripetibile.
    valore = conn.execute("SELECT valore ->> 'valore' FROM parametri_governance WHERE parametro_id = %s",
                          (quota_id,)).fetchone()[0]
    return dimensione_campione(valore, popolazione)


# --- decisione e applicazione ------------------------------------------------------

def _misura_del_lotto(conn: psycopg.Connection, org_id: str, lotto_id: str) -> tuple[str, str, int, bool, str] | None:
    """Ultima misura dell'unico campione del lotto (indice campioni_uno_per_lotto)."""
    riga = conn.execute(
        """SELECT m.misura_id, m.esito, m.n_elementi, m.censimento, c.campione_id FROM misure_precisione m
           JOIN campioni_revisione c USING (campione_id)
           WHERE c.org_id = %s AND c.tipo_proposta = 'abbinamento' AND c.filtro ->> 'lotto' = %s
           ORDER BY m.calcolata_il DESC LIMIT 1""",
        (org_id, lotto_id),
    ).fetchone()
    return (str(riga[0]), riga[1], riga[2], riga[3], str(riga[4])) if riga else None


def decidi_lotto(
    conn: psycopg.Connection, utente_id: str, org_id: str, lotto_id: str, *, rifiutate: Sequence[str],
    motivazione: str,
) -> int:
    """Il revisore approva il lotto in blocco, tranne le proposte rifiutate. Le proposte senza task vicino
    sono rifiutate: diventeranno task nuovi. Con revisione a campione o completa serve la misura del lotto,
    di cui l'atto riporta l'esito. Ritorna l'atto nel registro."""
    org_id, lotto_id = _uuid(org_id), _uuid(lotto_id)
    with conn.transaction():
        richiedi(conn, utente_id, "approvare_abbinamenti", org_id, risorsa=f"lotto_abbinamento:{lotto_id}")
        rifiutate = {_uuid(p) for p in rifiutate}
        schema = spazio_organizzazione(conn, org_id)
        _blocca(conn, f"lotto_abbinamento:{lotto_id}")
        livello, quota_id, _, _ = _lotto(conn, schema, lotto_id)
        proposte = conn.execute(
            sql.SQL("""SELECT p.proposta_id, p.task_id, d.proposta_id IS NOT NULL
                       FROM {0}.proposte_abbinamento p
                       LEFT JOIN {0}.decisioni_abbinamento d USING (proposta_id)
                       WHERE p.lotto_id = %s""").format(schema),
            (lotto_id,),
        ).fetchall()
        if any(r[2] for r in proposte):
            raise DecisioneGiaPresa(f"lotto {lotto_id}: già deciso")
        sconosciute = rifiutate - {str(r[0]) for r in proposte}
        if sconosciute:
            raise ValueError(f"proposte non del lotto: {sorted(sconosciute)}")
        con_task = sum(1 for r in proposte if r[1] is not None)
        dettagli: dict[str, Any] = {"livello_revisione": livello, "proposte_con_task": con_task}
        # Senza proposte con un task (dataset vuoto) non c'è nulla da campionare: si decide senza misura.
        if livello != "nulla" and con_task:
            misura = _misura_del_lotto(conn, org_id, lotto_id)
            if misura is None:
                raise ValueError("serve una misura di precisione sul campione del lotto prima di decidere")
            misura_id, esito_misura, n_elementi, censimento, campione_id = misura
            attesi = con_task if livello == "completa" else _dimensione_attesa(conn, quota_id, con_task)
            if n_elementi != attesi or (livello == "completa" and not censimento):
                raise ValueError(f"la misura del lotto copre {n_elementi} proposte, non le {attesi} previste")
            # Proposte giudicate errate o parziali nel campione che il revisore non rifiuta: restano nell'atto.
            non_rifiutate = conn.execute(
                """SELECT e.riferimento ->> 'proposta_id' FROM elementi_campione e
                   JOIN LATERAL (SELECT g.esito FROM giudizi_revisione g
                                 WHERE g.campione_id = e.campione_id AND g.posizione = e.posizione
                                 ORDER BY g.giudizio_id DESC LIMIT 1) g ON true
                   WHERE e.campione_id = %s AND g.esito IN ('errato', 'parziale')""",
                (campione_id,),
            ).fetchall()
            dettagli |= {"misura_id": misura_id, "esito_misura": esito_misura,
                         "campione_non_corrette_approvate": sum(1 for (p,) in non_rifiutate if p not in rifiutate)}
        esiti = {str(p): ("rifiutata" if str(p) in rifiutate or task is None else "approvata")
                 for p, task, _ in proposte}
        dettagli |= {"approvate": sum(e == "approvata" for e in esiti.values()),
                     "rifiutate": sum(e == "rifiutata" for e in esiti.values())}
        atto = registra(conn, autore_id=utente_id, tipo_oggetto="lotto_abbinamento", oggetto_id=lotto_id,
                        atto="approvazione", motivazione=motivazione, org_id=org_id, dettagli=dettagli)
        for proposta_id, esito in sorted(esiti.items()):
            conn.execute(
                sql.SQL("INSERT INTO {}.decisioni_abbinamento (proposta_id, esito, decisione_id) VALUES (%s, %s, %s)")
                .format(schema),
                (proposta_id, esito, atto),
            )
        return atto


def _task_attivo(conn: psycopg.Connection, task_id: str) -> str:
    """Il task stesso o, se nel frattempo è stato fuso, quello in cui è confluito. La riga resta bloccata
    fino alla fine della transazione: una fusione concorrente aspetta. Un task ritirato non si usa."""
    visti = set()
    while True:
        stato, fuso_in = conn.execute(
            "SELECT status, merged_into FROM canonical_tasks WHERE task_id = %s FOR SHARE", (task_id,)
        ).fetchone()
        if stato == "active":
            return task_id
        if stato != "merged" or fuso_in is None or task_id in visti:
            raise TaskNonAttivo(f"il task {task_id} non è attivo ({stato}): il candidato va riproposto")
        visti.add(task_id)
        task_id = str(fuso_in)


def applica_lotto(
    conn: psycopg.Connection, utente_id: str, org_id: str, lotto_id: str, *, incorpora: Incorpora,
    motivazione: str,
) -> dict[str, int]:
    """Applica le decisioni del lotto: approvata, occorrenza sul task del dataset (N e D si trasferiscono);
    rifiutata, task nuovo con il titolo del candidato e il suo embedding. Una volta sola per lotto."""
    org_id, lotto_id = _uuid(org_id), _uuid(lotto_id)
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_dataset_centrale", org_id, risorsa=f"lotto_abbinamento:{lotto_id}")
        schema = spazio_organizzazione(conn, org_id)
        _blocca(conn, f"lotto_abbinamento:{lotto_id}")
        _, _, modello_embedding, _ = _lotto(conn, schema, lotto_id)
        righe = conn.execute(
            sql.SQL("""SELECT p.proposta_id, d.esito, p.task_id, a.proposta_id IS NOT NULL,
                              c.titolo, c.granularita, c.ruolo_id, c.documento_id, c.estratto, c.nota_contesto,
                              c.model_name, c.prompt_hash
                       FROM {0}.proposte_abbinamento p JOIN {0}.candidati c USING (candidato_id)
                       LEFT JOIN {0}.decisioni_abbinamento d USING (proposta_id)
                       LEFT JOIN {0}.applicazioni_abbinamento a USING (proposta_id)
                       WHERE p.lotto_id = %s
                       ORDER BY c.creato_il, c.documento_id, c.ruolo_id, c.titolo""").format(schema),
            (lotto_id,),
        ).fetchall()
        if any(r[3] for r in righe):
            raise DecisioneGiaPresa(f"lotto {lotto_id}: già applicato")
        if any(r[1] is None for r in righe):
            raise ValueError(f"lotto {lotto_id}: non ancora deciso")
        applicazioni = []
        nuovi: dict[str, str] = {}
        for (proposta_id, esito, task_proposto, _, titolo, granularita, ruolo_id, documento_id, estratto, nota,
             model_name, prompt_hash) in righe:
            if esito == "approvata":
                task_id, task_nuovo = _task_attivo(conn, str(task_proposto)), False
            else:
                inserito = conn.execute(
                    """INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, %s)
                       ON CONFLICT (title_it) DO NOTHING RETURNING task_id""",
                    (titolo, granularita),
                ).fetchone()
                if inserito is not None:
                    task_id, task_nuovo = str(inserito[0]), True
                    nuovi[task_id] = titolo
                else:  # stesso titolo già nel dataset (anche da un candidato dello stesso lotto)
                    esistente = conn.execute("SELECT task_id FROM canonical_tasks WHERE title_it = %s",
                                             (titolo,)).fetchone()[0]
                    task_id, task_nuovo = _task_attivo(conn, str(esistente)), False
            nuova = registra_occorrenza(conn, org_id, task_id=task_id, ruolo_id=str(ruolo_id),
                                        documento_id=str(documento_id), estratto=estratto, nota_contesto=nota,
                                        model_name=model_name, prompt_hash=prompt_hash)
            occorrenza = conn.execute(
                "SELECT occurrence_id FROM task_occurrences WHERE task_id = %s AND role_id = %s",
                (task_id, ruolo_id),
            ).fetchone() if nuova else None
            applicazioni.append((str(proposta_id), task_id, task_nuovo, str(occorrenza[0]) if occorrenza else None))
        if nuovi:
            vettori = _vettori(incorpora, list(nuovi.values()), modello_embedding)
            for task_id, vettore in zip(nuovi, vettori):
                conn.execute("INSERT INTO task_embeddings (task_id, model_name, vec) VALUES (%s, %s, %s::vector)",
                             (task_id, modello_embedding, _vettore(vettore)))
        esito = {"collegate": sum(not a[2] for a in applicazioni), "task_nuovi": len(nuovi),
                 "occorrenze_nuove": sum(a[3] is not None for a in applicazioni)}
        atto = registra(conn, autore_id=utente_id, tipo_oggetto="applicazione_abbinamento", oggetto_id=lotto_id,
                        atto="approvazione", motivazione=motivazione, org_id=org_id, dettagli=esito)
        for proposta_id, task_id, task_nuovo, occorrenza_id in applicazioni:
            conn.execute(
                sql.SQL("""INSERT INTO {}.applicazioni_abbinamento
                             (proposta_id, task_id, task_nuovo, occorrenza_id, decisione_id)
                           VALUES (%s, %s, %s, %s, %s)""").format(schema),
                (proposta_id, task_id, task_nuovo, occorrenza_id, atto),
            )
        return esito
