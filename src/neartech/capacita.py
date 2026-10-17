"""Snapshot di capacità tecnologica (fase 4; piano, "Come si stima la copertura tecnologica"; metodo, sezione 17).

Copertura di riserva: finché la capacità di test non è calibrata, ogni task e dimensione ha la copertura di
riserva della rubrica (0 nessuna soluzione dimostrata … 4 esecuzione autonoma affidabile documentata), con
qualità minima. Lo snapshot si calcola dalle evidenze sul task con la formula del piano:

  c_k = Σ q_e m_e 2^(-(t - t_e)/h) s_e / Σ q_e m_e 2^(-(t - t_e)/h)

con m_e = 1 (evidenza sul task stesso). L'intervallo [c_low, c_high] è il disaccordo fra le evidenze
(punteggio minimo e massimo): fonti in conflitto danno una stima incerta, non una media rassicurante.
Le evidenze con dimensione 'any' valgono per k1, k2 e k3; quelle successive alla data dello snapshot no.
Le evidenze su un task poi fuso valgono per il superstite. Nello snapshot di riserva tutte le evidenze hanno
la stessa classe di qualità: con qualità diverse servono i pesi di qualità approvati, e lo snapshot si ferma.
Lo snapshot nasce proposto; lo pubblica chi approva gli snapshot, con un atto e una nota esplicativa
(il database ne controlla il ciclo di vita, migrazione 0033).
"""

import uuid
from datetime import date

import psycopg

from neartech.permessi import richiedi
from neartech.registro import registra

METODO_RISERVA = "riserva-v1"  # intervallo dal solo disaccordo fra le evidenze


def metodo_riserva(banda: float) -> str:
    """riserva-v1 senza banda; riserva-v2 con l'intervallo allargato di ±banda livelli (metodo, sezione 20)."""
    return METODO_RISERVA if banda == 0 else f"riserva-v2-banda-{banda:g}"
DIMENSIONI = ("k1", "k2", "k3")


def proponi_snapshot_riserva(
    conn: psycopg.Connection, utente_id: str, *, as_of: str | date, emivita_giorni: int, motivazione: str,
    banda: float = 0.0,
) -> str:
    """Calcola la copertura di riserva di ogni task con evidenze e la salva in uno snapshot proposto.

    banda: livelli aggiunti sotto e sopra l'intervallo delle evidenze (limitato a 0–4), perché una sola opinione
    non è una certezza (registro di metodo, sezione 20: 0,5, metà della distanza fra due livelli della scala).
    Il valore è dichiarato nel metodo dello snapshot e nell'atto."""
    if emivita_giorni < 1:
        raise ValueError("l'emivita delle evidenze deve essere di almeno un giorno")
    if not 0 <= banda <= 2:
        raise ValueError("la banda deve stare fra 0 e 2 livelli")
    metodo = metodo_riserva(banda)
    data = as_of if isinstance(as_of, date) else date.fromisoformat(as_of)
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_parametri_tecnici", risorsa="snapshot_capacita")
        # Ogni evidenza va al task attivo in cui il suo task è confluito (catena di fusioni).
        righe = conn.execute(
            """WITH RECURSIVE catena(origine, task_id, status, merged_into) AS (
                 SELECT t.task_id, t.task_id, t.status, t.merged_into FROM canonical_tasks t
                 UNION ALL
                 SELECT c.origine, t.task_id, t.status, t.merged_into
                 FROM catena c JOIN canonical_tasks t ON t.task_id = c.merged_into WHERE c.status = 'merged'
               ), finale AS (
                 SELECT origine, task_id FROM catena WHERE status = 'active'
               )
               SELECT f.task_id, d.dimensione, e.score_0_4, e.quality,
                      power(2::numeric, -((%(data)s::date - e.observed_at)::numeric / %(h)s)) AS decadimento
               FROM evidence_items e
               JOIN finale f ON f.origine = e.task_id
               CROSS JOIN LATERAL unnest(CASE WHEN e.dimension = 'any' THEN ARRAY['k1', 'k2', 'k3']
                                              ELSE ARRAY[e.dimension] END) AS d(dimensione)
               WHERE e.observed_at <= %(data)s::date
               ORDER BY f.task_id, d.dimensione, e.evidence_id""",
            {"data": data, "h": emivita_giorni},
        ).fetchall()
        if not righe:
            raise ValueError("nessuna evidenza sui task alla data dello snapshot")
        if len({float(r[3]) for r in righe}) > 1:
            raise ValueError("evidenze di qualità diverse: servono i pesi di qualità approvati, non previsti "
                             "nello snapshot di riserva")
        per_chiave: dict[tuple[str, str], list[tuple[float, float, float]]] = {}
        for task_id, dimensione, punteggio, qualita, decadimento in righe:
            per_chiave.setdefault((str(task_id), dimensione), []).append(
                (float(punteggio), float(qualita), float(decadimento)))
        snapshot_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO capability_snapshots (snapshot_id, as_of, method_version, half_life_days, status,
                                                 tipo_capacita)
               VALUES (%s, %s, %s, %s, 'proposed', 'riserva')""",
            (snapshot_id, data, metodo, emivita_giorni),
        )
        scritte = 0
        for (task_id, dimensione), evidenze in sorted(per_chiave.items()):
            contano = [(s, q * d) for s, q, d in evidenze if q * d > 0]  # solo le evidenze che pesano
            if not contano:
                continue
            media = sum(p * s for s, p in contano) / sum(p for _, p in contano)
            punteggi = [s for s, _ in contano]
            conn.execute(
                """INSERT INTO task_capability (snapshot_id, task_id, dimension, c_mean, c_low, c_high, n_evidence)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (snapshot_id, task_id, dimensione, round(media, 2), max(0.0, min(punteggi) - banda),
                 min(4.0, max(punteggi) + banda), len(contano)),
            )
            scritte += 1
        if not scritte:
            raise ValueError("nessuna evidenza con peso alla data dello snapshot")
        registra(conn, autore_id=utente_id, tipo_oggetto="snapshot_capacita", oggetto_id=snapshot_id,
                 atto="proposta", motivazione=motivazione,
                 dettagli={"metodo": metodo, "banda": banda, "tipo_capacita": "riserva",
                           "emivita_giorni": emivita_giorni,
                           "task_dimensioni": scritte})
        return snapshot_id


def pubblica_snapshot(conn: psycopg.Connection, utente_id: str, snapshot_id: str, *, nota: str) -> int:
    """Pubblica uno snapshot proposto e ritira quello pubblicato prima. Ritorna l'atto nel registro."""
    snapshot_id = str(uuid.UUID(str(snapshot_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "approvare_snapshot", risorsa=f"snapshot_capacita:{snapshot_id}")
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('snapshot_capacita'))")
        stato = conn.execute("SELECT status FROM capability_snapshots WHERE snapshot_id = %s FOR UPDATE",
                             (snapshot_id,)).fetchone()
        if stato is None:
            raise LookupError(f"snapshot {snapshot_id} inesistente")
        if stato[0] != "proposed":
            raise ValueError(f"lo snapshot {snapshot_id} non è proposto ({stato[0]})")
        if not conn.execute("SELECT EXISTS (SELECT 1 FROM task_capability WHERE snapshot_id = %s)",
                            (snapshot_id,)).fetchone()[0]:
            raise ValueError(f"lo snapshot {snapshot_id} non ha copertura")
        soggetto = conn.execute("SELECT soggetto_sso FROM utenti WHERE utente_id = %s", (utente_id,)).fetchone()[0]
        proponente = conn.execute(
            """SELECT autore_id FROM registro_decisioni WHERE tipo_oggetto = 'snapshot_capacita'
                 AND oggetto_id = %s AND atto = 'proposta' ORDER BY posizione LIMIT 1""", (snapshot_id,)).fetchone()
        # L'atto viene prima del cambio di stato: il database pubblica solo uno snapshot con l'approvazione registrata.
        atto = registra(conn, autore_id=utente_id, tipo_oggetto="snapshot_capacita", oggetto_id=snapshot_id,
                        atto="approvazione", motivazione=nota,
                        dettagli={"stesso_proponente": proponente is not None
                                  and str(proponente[0]) == str(uuid.UUID(str(utente_id)))})
        conn.execute("UPDATE capability_snapshots SET status = 'retired' WHERE status = 'published'")
        conn.execute(
            """UPDATE capability_snapshots SET status = 'published', approved_by = %s, approved_at = now()
               WHERE snapshot_id = %s""",
            (soggetto, snapshot_id),
        )
        return atto
