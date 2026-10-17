"""Snapshot di capacità tecnologica (fase 4; piano, "Come si stima la copertura tecnologica"; metodo, sezione 17).

Copertura di riserva: finché la capacità di test non è calibrata, ogni task e dimensione ha la copertura di
riserva della rubrica (0 nessuna soluzione dimostrata … 4 esecuzione autonoma affidabile documentata), con
qualità minima. Lo snapshot si calcola dalle evidenze sul task con la formula del piano:

  c_k = Σ q_e m_e 2^(-(t - t_e)/h) s_e / Σ q_e m_e 2^(-(t - t_e)/h)

con m_e = 1 (evidenza sul task stesso). L'intervallo [c_low, c_high] è il disaccordo fra le evidenze
(punteggio minimo e massimo): fonti in conflitto danno una stima incerta, non una media rassicurante.
Le evidenze con dimensione 'any' valgono per k1, k2 e k3; quelle successive alla data dello snapshot no.
Lo snapshot nasce proposto; lo pubblica chi approva gli snapshot, con un atto e una nota esplicativa.
"""

import uuid
from datetime import date

import psycopg

from neartech.permessi import richiedi
from neartech.registro import registra

METODO_RISERVA = "riserva-v1"
DIMENSIONI = ("k1", "k2", "k3")


def proponi_snapshot_riserva(
    conn: psycopg.Connection, utente_id: str, *, as_of: str | date, emivita_giorni: int, motivazione: str
) -> str:
    """Calcola la copertura di riserva di ogni task con evidenze e la salva in uno snapshot proposto."""
    if emivita_giorni < 1:
        raise ValueError("l'emivita delle evidenze deve essere di almeno un giorno")
    data = as_of if isinstance(as_of, date) else date.fromisoformat(as_of)
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_parametri_tecnici", risorsa="snapshot_capacita")
        righe = conn.execute(
            """SELECT e.task_id, d.dimensione, e.score_0_4, e.quality,
                      power(2::numeric, -((%(data)s::date - e.observed_at)::numeric / %(h)s)) AS decadimento
               FROM evidence_items e
               CROSS JOIN LATERAL unnest(CASE WHEN e.dimension = 'any' THEN ARRAY['k1', 'k2', 'k3']
                                              ELSE ARRAY[e.dimension] END) AS d(dimensione)
               JOIN canonical_tasks t ON t.task_id = e.task_id AND t.status = 'active'
               WHERE e.task_id IS NOT NULL AND e.observed_at <= %(data)s::date
               ORDER BY e.task_id, d.dimensione, e.evidence_id""",
            {"data": data, "h": emivita_giorni},
        ).fetchall()
        if not righe:
            raise ValueError("nessuna evidenza sui task alla data dello snapshot")
        per_chiave: dict[tuple[str, str], list[tuple[float, float, float]]] = {}
        for task_id, dimensione, punteggio, qualita, decadimento in righe:
            per_chiave.setdefault((str(task_id), dimensione), []).append(
                (float(punteggio), float(qualita), float(decadimento)))
        snapshot_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO capability_snapshots (snapshot_id, as_of, method_version, half_life_days, status,
                                                 tipo_capacita)
               VALUES (%s, %s, %s, %s, 'proposed', 'riserva')""",
            (snapshot_id, data, METODO_RISERVA, emivita_giorni),
        )
        for (task_id, dimensione), evidenze in sorted(per_chiave.items()):
            pesi = [q * d for _, q, d in evidenze]
            if sum(pesi) == 0:
                continue  # evidenze di qualità nulla: non coprono nulla
            media = sum(p * s for p, (s, _, _) in zip(pesi, evidenze)) / sum(pesi)
            punteggi = [s for s, _, _ in evidenze]
            conn.execute(
                """INSERT INTO task_capability (snapshot_id, task_id, dimension, c_mean, c_low, c_high, n_evidence)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (snapshot_id, task_id, dimensione, round(media, 2), min(punteggi), max(punteggi), len(evidenze)),
            )
        registra(conn, autore_id=utente_id, tipo_oggetto="snapshot_capacita", oggetto_id=snapshot_id,
                 atto="proposta", motivazione=motivazione,
                 dettagli={"metodo": METODO_RISERVA, "tipo_capacita": "riserva", "emivita_giorni": emivita_giorni,
                           "task_dimensioni": len(per_chiave)})
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
        soggetto = conn.execute("SELECT soggetto_sso FROM utenti WHERE utente_id = %s", (utente_id,)).fetchone()[0]
        conn.execute("UPDATE capability_snapshots SET status = 'retired' WHERE status = 'published'")
        conn.execute(
            """UPDATE capability_snapshots SET status = 'published', approved_by = %s, approved_at = now()
               WHERE snapshot_id = %s""",
            (soggetto, snapshot_id),
        )
        return registra(conn, autore_id=utente_id, tipo_oggetto="snapshot_capacita", oggetto_id=snapshot_id,
                        atto="approvazione", motivazione=nota)
