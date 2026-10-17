"""Occorrenze dei task nelle organizzazioni (ADR 0001, ADR 0005).

Il testo del cliente (estratti, note, nomi dei ruoli, nomi dei documenti) sta solo nello spazio
dell'organizzazione org_<codice>. In public restano i legami task–ruolo–documento con gli stessi
identificativi e nomi neutri ("ruolo <id>", "documento <id>"): servono al dataset condiviso e alle
viste, e i vincoli della migrazione 0023 impediscono che vi torni testo.
"""

import re
import uuid
from typing import Any

import psycopg
from psycopg import sql

from neartech.organizzazioni import schema_organizzazione
from neartech.permessi import richiedi
from neartech.registro import registra


def spazio_organizzazione(conn: psycopg.Connection, org_id: str) -> sql.Identifier:
    riga = conn.execute("SELECT codice FROM organizations WHERE org_id = %s", (org_id,)).fetchone()
    if riga is None or riga[0] is None:
        raise LookupError(f"l'organizzazione {org_id} non ha uno spazio")
    nome = schema_organizzazione(riga[0])
    if conn.execute("SELECT to_regnamespace(%s)", (nome,)).fetchone()[0] is None:
        raise LookupError(f"lo spazio {nome} non esiste")
    return sql.Identifier(nome)


def _spazi(conn: psycopg.Connection) -> list[sql.Identifier]:
    spazi = []
    for (codice,) in conn.execute("SELECT codice FROM organizations WHERE codice IS NOT NULL ORDER BY codice"):
        nome = schema_organizzazione(codice)
        if conn.execute("SELECT to_regnamespace(%s)", (nome,)).fetchone()[0] is not None:
            spazi.append(sql.Identifier(nome))
    return spazi


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _blocca(conn: psycopg.Connection, chiave: str) -> None:
    """Lock fino alla fine della transazione: due caricamenti dello stesso ruolo o documento non si sovrappongono."""
    conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (chiave,))


def ruolo(conn: psycopg.Connection, org_id: str, nome: str, famiglia: str | None = None) -> str:
    """Ruolo dell'organizzazione: nome nello spazio dell'organizzazione, nome neutro in public."""
    spazio = spazio_organizzazione(conn, org_id)
    _blocca(conn, f"ruolo:{org_id}:{nome}")
    riga = conn.execute(
        sql.SQL("SELECT ruolo_id FROM {}.ruoli_organizzativi WHERE nome = %s").format(spazio), (nome,)
    ).fetchone()
    if riga is not None:
        return str(riga[0])
    ruolo_id = str(uuid.uuid4())
    conn.execute("INSERT INTO roles (role_id, org_id, name) VALUES (%s, %s, %s)",
                 (ruolo_id, org_id, f"ruolo {ruolo_id}"))
    conn.execute(
        sql.SQL("INSERT INTO {}.ruoli_organizzativi (ruolo_id, nome, famiglia) VALUES (%s, %s, %s)").format(spazio),
        (ruolo_id, nome, famiglia),
    )
    return ruolo_id


def documento(
    conn: psycopg.Connection, org_id: str, *, nome_file: str, sha256: str, licenza: str,
    tipo: str = "org_document",
) -> str:
    """Documento dell'organizzazione: nome del file nello spazio dell'organizzazione, nome neutro in public.

    Il documento è il suo contenuto: lo stesso file con un altro nome è lo stesso documento.
    In public la versione è l'inizio dell'impronta (vincolo della migrazione 0025).
    """
    if not _SHA256.fullmatch(sha256):
        raise ValueError("sha256 del documento non valido: attesi 64 caratteri esadecimali minuscoli")
    spazio = spazio_organizzazione(conn, org_id)
    _blocca(conn, f"documento:{org_id}:{sha256}")
    riga = conn.execute(
        sql.SQL("SELECT documento_id FROM {}.documenti WHERE sha256 = %s").format(spazio), (sha256,),
    ).fetchone()
    if riga is not None:
        return str(riga[0])
    documento_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO sources (source_id, kind, name, version, license, content_hash)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (documento_id, tipo, f"documento {documento_id}", sha256[:16], licenza, sha256),
    )
    conn.execute(
        sql.SQL("INSERT INTO {}.documenti (documento_id, nome_file, sha256, tipo) VALUES (%s, %s, %s, %s)")
        .format(spazio),
        (documento_id, nome_file, sha256, tipo),
    )
    return documento_id


def registra_occorrenza(
    conn: psycopg.Connection, org_id: str, *, task_id: str, ruolo_id: str, documento_id: str,
    estratto: str, nota_contesto: str | None, model_name: str, prompt_hash: str,
    quota_tempo: float | None = None,
) -> bool:
    """Legame senza testo in public e occorrenza con il testo nello spazio dell'organizzazione.

    Restituisce False se il task è già presente per quel ruolo.
    """
    spazio = spazio_organizzazione(conn, org_id)
    riga = conn.execute(
        """INSERT INTO task_occurrences (task_id, role_id, time_share, source_id, model_name, prompt_hash)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (task_id, role_id) DO NOTHING RETURNING occurrence_id""",
        (task_id, ruolo_id, quota_tempo, documento_id, model_name, prompt_hash),
    ).fetchone()
    if riga is None:
        return False
    conn.execute(
        sql.SQL("""INSERT INTO {}.occorrenze
                     (occorrenza_id, task_id, ruolo_id, documento_id, estratto, nota_contesto, quota_tempo,
                      model_name, prompt_hash)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""").format(spazio),
        (riga[0], task_id, ruolo_id, documento_id, estratto, nota_contesto, quota_tempo, model_name, prompt_hash),
    )
    return True


def sposta_occorrenze(conn: psycopg.Connection, *, da_task: str, a_task: str) -> None:
    """Fusione: le occorrenze di da_task passano ad a_task, in public e in ogni spazio.

    Se il ruolo ha già a_task si tiene quella esistente e si cancella la doppia.
    """
    conn.execute(
        """DELETE FROM task_occurrences o WHERE o.task_id = %s
           AND EXISTS (SELECT 1 FROM task_occurrences s WHERE s.task_id = %s AND s.role_id = o.role_id)""",
        (da_task, a_task),
    )
    conn.execute("UPDATE task_occurrences SET task_id = %s WHERE task_id = %s", (a_task, da_task))
    for spazio in _spazi(conn):
        conn.execute(
            sql.SQL("""DELETE FROM {0}.occorrenze o WHERE o.task_id = %s
                       AND EXISTS (SELECT 1 FROM {0}.occorrenze s WHERE s.task_id = %s AND s.ruolo_id = o.ruolo_id)""")
            .format(spazio),
            (da_task, a_task),
        )
        conn.execute(sql.SQL("UPDATE {}.occorrenze SET task_id = %s WHERE task_id = %s").format(spazio),
                     (a_task, da_task))


def togli_testo_da_public(conn: psycopg.Connection, utente_id: str, org_id: str) -> dict[str, Any]:
    """Una tantum: toglie da public il testo di un'organizzazione già copiato nel suo spazio.

    Si ferma se una riga di public non ha nello spazio la copia identica con lo stesso identificativo.
    """
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "gestire_organizzazioni", org_id, risorsa=f"pulizia:{org_id}")
        spazio = spazio_organizzazione(conn, org_id)
        controlli = {
            "occorrenze": sql.SQL(
                """SELECT count(*) FROM task_occurrences o JOIN roles r ON r.role_id = o.role_id
                   WHERE r.org_id = %s AND (o.raw_snippet IS NOT NULL OR o.context_note IS NOT NULL)
                     AND NOT EXISTS (SELECT 1 FROM {}.occorrenze c WHERE c.occorrenza_id = o.occurrence_id
                                     AND c.estratto = o.raw_snippet
                                     AND c.nota_contesto IS NOT DISTINCT FROM o.context_note)"""),
            "ruoli": sql.SQL(
                """SELECT count(*) FROM roles r WHERE r.org_id = %s AND r.name <> 'ruolo ' || r.role_id::text
                     AND NOT EXISTS (SELECT 1 FROM {}.ruoli_organizzativi c
                                     WHERE c.ruolo_id = r.role_id AND c.nome = r.name
                                       AND c.famiglia IS NOT DISTINCT FROM r.family)"""),
            "documenti": sql.SQL(
                """SELECT count(*) FROM sources s
                   WHERE s.kind = 'org_document' AND s.name <> 'documento ' || s.source_id::text
                     AND s.source_id IN (SELECT o.source_id FROM task_occurrences o JOIN roles r USING (role_id)
                                         WHERE r.org_id = %s)
                     AND NOT EXISTS (SELECT 1 FROM {}.documenti c WHERE c.documento_id = s.source_id
                                     AND c.nome_file = s.name)"""),
        }
        diversi = {k: conn.execute(q.format(spazio), (org_id,)).fetchone()[0] for k, q in controlli.items()}
        if any(diversi.values()):
            raise RuntimeError(f"copia nello spazio non identica, nulla è stato tolto: {diversi}")
        occorrenze = conn.execute(
            """UPDATE task_occurrences o SET raw_snippet = NULL, context_note = NULL
               FROM roles r WHERE r.role_id = o.role_id AND r.org_id = %s
                 AND (o.raw_snippet IS NOT NULL OR o.context_note IS NOT NULL)""",
            (org_id,),
        ).rowcount
        documenti = conn.execute(
            """UPDATE sources s SET name = 'documento ' || s.source_id::text
               WHERE s.kind = 'org_document' AND s.name <> 'documento ' || s.source_id::text
                 AND s.source_id IN (SELECT o.source_id FROM task_occurrences o JOIN roles r USING (role_id)
                                     WHERE r.org_id = %s)""",
            (org_id,),
        ).rowcount
        ruoli = conn.execute(
            """UPDATE roles SET name = 'ruolo ' || role_id::text, family = NULL
               WHERE org_id = %s AND name <> 'ruolo ' || role_id::text""",
            (org_id,),
        ).rowcount
        esito = {"occorrenze": occorrenze, "ruoli": ruoli, "documenti": documenti}
        registra(conn, autore_id=utente_id, tipo_oggetto="organizzazione", oggetto_id=org_id, atto="correzione",
                 motivazione="testo del cliente tolto da public: resta solo nello spazio dell'organizzazione (ADR 0005)",
                 org_id=org_id, dettagli=esito)
        return esito
