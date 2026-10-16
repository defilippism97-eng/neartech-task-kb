"""Spostamento del testo del cliente dallo schema condiviso allo spazio dell'organizzazione (ADR 0001).

La copia conserva gli identificativi, non tocca le righe in public e non si ripete.
La rimozione del testo da public è un passo separato, con approvazione.
"""

import pytest

from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente
from neartech.spostamento import GiaSpostata, piano_spostamento, sposta_testo_cliente


@pytest.fixture
def dati(conn):
    admin = crea_utente(conn, "sso|admin")
    assegna_ruolo(conn, admin, "amministratore_tecnico")
    org = str(conn.execute("INSERT INTO organizations (name) VALUES ('Org sintetica') RETURNING org_id").fetchone()[0])
    ruolo = conn.execute(
        "INSERT INTO roles (org_id, name, family) VALUES (%s, 'Coordinatore sintetico', 'servizi') RETURNING role_id",
        (org,),
    ).fetchone()[0]
    fonte = conn.execute(
        """INSERT INTO sources (kind, name, version, license, content_hash)
           VALUES ('org_document', 'mansionario.docx', '1', 'interno', 'hash-sintetico') RETURNING source_id"""
    ).fetchone()[0]
    task = conn.execute(
        "INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Task sintetico', 2) RETURNING task_id"
    ).fetchone()[0]
    occorrenza = conn.execute(
        """INSERT INTO task_occurrences
             (task_id, role_id, context_note, raw_snippet, time_share, source_id, model_name, prompt_hash)
           VALUES (%s, %s, 'nota', 'frammento originale', 0.5, %s, 'modello', 'hash') RETURNING occurrence_id""",
        (task, ruolo, fonte),
    ).fetchone()[0]
    return {"admin": admin, "org": org, "ruolo": ruolo, "fonte": fonte, "task": task, "occorrenza": occorrenza}


def test_piano_conta_senza_scrivere(conn, dati):
    assert piano_spostamento(conn, dati["org"]) == {
        "ruoli": 1, "occorrenze": 1, "documenti": 1, "stime_collegate": 0,
    }


def test_copia_conserva_testo_e_identificativi(conn, dati):
    sposta_testo_cliente(conn, dati["admin"], dati["org"], codice="sintetica")
    occorrenza = conn.execute(
        """SELECT occorrenza_id, task_id, ruolo_id, documento_id, estratto, nota_contesto, quota_tempo
           FROM org_sintetica.occorrenze"""
    ).fetchall()
    assert occorrenza == [(dati["occorrenza"], dati["task"], dati["ruolo"], dati["fonte"],
                           "frammento originale", "nota", pytest.approx(0.5))]
    ruoli = conn.execute("SELECT ruolo_id, nome, famiglia FROM org_sintetica.ruoli_organizzativi").fetchall()
    assert ruoli == [(dati["ruolo"], "Coordinatore sintetico", "servizi")]
    documenti = conn.execute("SELECT documento_id, nome_file, sha256 FROM org_sintetica.documenti").fetchall()
    assert documenti == [(dati["fonte"], "mansionario.docx", "hash-sintetico")]


def test_le_righe_in_public_restano(conn, dati):
    sposta_testo_cliente(conn, dati["admin"], dati["org"], codice="sintetica")
    assert conn.execute("SELECT count(*) FROM task_occurrences").fetchone()[0] == 1


def test_non_si_ripete(conn, dati):
    sposta_testo_cliente(conn, dati["admin"], dati["org"], codice="sintetica")
    with pytest.raises(GiaSpostata):
        sposta_testo_cliente(conn, dati["admin"], dati["org"], codice="sintetica")


def test_serve_l_amministratore(conn, dati):
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, revisore, "revisore", dati["org"])
    with pytest.raises(PermessoNegato):
        sposta_testo_cliente(conn, revisore, dati["org"], codice="sintetica")
