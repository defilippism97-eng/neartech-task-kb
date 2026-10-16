"""Spostamento del testo del cliente dallo schema condiviso allo spazio dell'organizzazione (ADR 0001).

Prima dell'ADR 0001 ruoli, estratti e note dei documenti stavano in public.roles e
public.task_occurrences. Qui si copiano in org_<codice> conservando gli identificativi.
Le righe in public restano: la rimozione del testo da public è un passo separato,
da approvare. In produzione la copia richiede l'approvazione del responsabile.
"""

import psycopg
from psycopg import sql

from neartech.organizzazioni import crea_spazio
from neartech.permessi import richiedi

_OCCORRENZE_ORG = """
    SELECT o.* FROM task_occurrences o JOIN roles r ON r.role_id = o.role_id WHERE r.org_id = %s
"""


class GiaSpostata(RuntimeError):
    """L'organizzazione ha già un codice e uno spazio."""


def piano_spostamento(conn: psycopg.Connection, org_id: str) -> dict[str, int]:
    """Conta cosa verrebbe copiato. Sola lettura."""
    return {
        "ruoli": conn.execute("SELECT count(*) FROM roles WHERE org_id = %s", (org_id,)).fetchone()[0],
        "occorrenze": conn.execute(f"SELECT count(*) FROM ({_OCCORRENZE_ORG}) o", (org_id,)).fetchone()[0],
        "documenti": conn.execute(
            f"SELECT count(DISTINCT source_id) FROM ({_OCCORRENZE_ORG}) o", (org_id,)
        ).fetchone()[0],
        "stime_collegate": conn.execute(
            f"""SELECT count(*) FROM policy_estimates
                WHERE occurrence_id IN (SELECT occurrence_id FROM ({_OCCORRENZE_ORG}) o)""",
            (org_id,),
        ).fetchone()[0],
    }


def sposta_testo_cliente(conn: psycopg.Connection, utente_id: str, org_id: str, *, codice: str) -> dict[str, int]:
    richiedi(conn, utente_id, "gestire_organizzazioni", org_id, risorsa=f"spostamento:{org_id}")
    riga = conn.execute("SELECT codice FROM organizations WHERE org_id = %s FOR UPDATE", (org_id,)).fetchone()
    if riga is None:
        raise LookupError(f"organizzazione {org_id} inesistente")
    if riga[0] is not None:
        raise GiaSpostata(f"l'organizzazione ha già lo spazio org_{riga[0]}")
    schema = crea_spazio(conn, org_id, codice)
    destinazione = sql.Identifier(schema)

    conn.execute(
        sql.SQL("""INSERT INTO {}.ruoli_organizzativi (ruolo_id, nome, famiglia)
                   SELECT role_id, name, family FROM roles WHERE org_id = %s""").format(destinazione),
        (org_id,),
    )
    conn.execute(
        sql.SQL("""INSERT INTO {}.documenti (documento_id, nome_file, sha256, tipo)
                   SELECT DISTINCT s.source_id, s.name, s.content_hash, s.kind
                   FROM sources s JOIN (""" + _OCCORRENZE_ORG + """) o ON o.source_id = s.source_id""")
        .format(destinazione),
        (org_id,),
    )
    conn.execute(
        sql.SQL("""INSERT INTO {}.occorrenze
                     (occorrenza_id, task_id, ruolo_id, documento_id, estratto, nota_contesto,
                      quota_tempo, model_name, prompt_hash)
                   SELECT occurrence_id, task_id, role_id, source_id, raw_snippet, context_note,
                          time_share, model_name, prompt_hash
                   FROM (""" + _OCCORRENZE_ORG + """) o""").format(destinazione),
        (org_id,),
    )
    return piano_spostamento(conn, org_id)
