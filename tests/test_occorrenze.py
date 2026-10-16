"""Occorrenze dei task (ADR 0005): il testo del cliente sta solo nello spazio dell'organizzazione;
in public restano legami con gli stessi identificativi e nomi neutri."""

import psycopg
import pytest

from neartech.occorrenze import documento, registra_occorrenza, ruolo, sposta_occorrenze, togli_testo_da_public
from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import inizializza_amministratore


@pytest.fixture
def spazio(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    org = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    task = [str(conn.execute(
        "INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2) RETURNING task_id", (f"Task {i}",)
    ).fetchone()[0]) for i in range(3)]
    return {"admin": admin, "org": org, "task": task}


def _registra(conn, spazio, task, nome_ruolo, estratto):
    r = ruolo(conn, spazio["org"], nome_ruolo)
    d = documento(conn, spazio["org"], nome_file="mansionario.docx", sha256="abc123", licenza="interno")
    return registra_occorrenza(conn, spazio["org"], task_id=task, ruolo_id=r, documento_id=d, estratto=estratto,
                               nota_contesto="nota", model_name="modello", prompt_hash="hash")


def test_il_testo_resta_nello_spazio_dell_organizzazione(conn, spazio):
    assert _registra(conn, spazio, spazio["task"][0], "Coordinatore amministrativo", "redige la prima nota")
    pubblico = conn.execute(
        """SELECT o.raw_snippet, o.context_note, r.name, s.name, o.role_id, o.source_id
           FROM task_occurrences o JOIN roles r USING (role_id) JOIN sources s USING (source_id)"""
    ).fetchone()
    assert pubblico[:2] == (None, None)
    assert pubblico[2] == f"ruolo {pubblico[4]}"
    assert pubblico[3] == f"documento {pubblico[5]}"
    privato = conn.execute(
        """SELECT o.estratto, o.nota_contesto, r.nome, d.nome_file FROM org_sintetica.occorrenze o
           JOIN org_sintetica.ruoli_organizzativi r USING (ruolo_id)
           JOIN org_sintetica.documenti d USING (documento_id)"""
    ).fetchone()
    assert privato == ("redige la prima nota", "nota", "Coordinatore amministrativo", "mansionario.docx")


def test_ruolo_e_documento_si_riusano(conn, spazio):
    assert ruolo(conn, spazio["org"], "Contabile") == ruolo(conn, spazio["org"], "Contabile")
    assert documento(conn, spazio["org"], nome_file="a.docx", sha256="x", licenza="interno") == \
        documento(conn, spazio["org"], nome_file="a.docx", sha256="x", licenza="interno")


def test_rilancio_non_duplica(conn, spazio):
    assert _registra(conn, spazio, spazio["task"][0], "Contabile", "passo")
    assert not _registra(conn, spazio, spazio["task"][0], "Contabile", "passo")
    assert conn.execute("SELECT count(*) FROM org_sintetica.occorrenze").fetchone()[0] == 1


def test_lo_spostamento_vale_anche_nello_spazio_dell_organizzazione(conn, spazio):
    a, m = spazio["task"][0], spazio["task"][1]
    _registra(conn, spazio, a, "Ruolo uno", "testo a")
    _registra(conn, spazio, m, "Ruolo uno", "testo m doppio")
    _registra(conn, spazio, m, "Ruolo due", "testo m")
    sposta_occorrenze(conn, da_task=m, a_task=a)
    for tabella in ("task_occurrences", "org_sintetica.occorrenze"):
        assert conn.execute(f"SELECT count(*) FROM {tabella} WHERE task_id = %s", (m,)).fetchone()[0] == 0
        assert conn.execute(f"SELECT count(*) FROM {tabella} WHERE task_id = %s", (a,)).fetchone()[0] == 2
    assert sorted(r[0] for r in conn.execute(
        "SELECT estratto FROM org_sintetica.occorrenze WHERE task_id = %s", (a,)
    ).fetchall()) == ["testo a", "testo m"]


@pytest.mark.parametrize("comando", [
    """INSERT INTO task_occurrences (task_id, role_id, raw_snippet, source_id, model_name, prompt_hash)
       SELECT %(t)s, role_id, 'testo del cliente', source_id, 'm', 'h' FROM task_occurrences LIMIT 1""",
    "INSERT INTO roles (org_id, name) VALUES (%(o)s, 'Nome vero del ruolo')",
    """INSERT INTO sources (kind, name, version, license, content_hash)
       VALUES ('org_document', 'mansionario vero.docx', '1', 'interno', 'h2')""",
])
def test_il_testo_non_puo_tornare_in_public(conn, spazio, comando):
    _registra(conn, spazio, spazio["task"][0], "Contabile", "passo")
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(comando, {"t": spazio["task"][2], "o": spazio["org"]})


def test_togli_testo_da_public_sui_dati_precedenti(conn, spazio):
    """Dati come quelli di Società Dolce: testo in public e copia identica nello spazio dell'organizzazione."""
    for tabella, vincolo in (("task_occurrences", "task_occurrences_senza_testo"), ("roles", "roles_nome_neutro"),
                             ("sources", "sources_documento_neutro")):
        conn.execute(f"ALTER TABLE {tabella} DROP CONSTRAINT {vincolo}")
    _registra(conn, spazio, spazio["task"][0], "Contabile", "passo originale")
    conn.execute("UPDATE roles SET name = 'Contabile'")
    conn.execute("UPDATE sources SET name = 'mansionario.docx' WHERE kind = 'org_document'")
    conn.execute("UPDATE task_occurrences SET raw_snippet = 'passo originale', context_note = 'nota'")
    esito = togli_testo_da_public(conn, spazio["admin"], spazio["org"])
    assert esito == {"occorrenze": 1, "ruoli": 1, "documenti": 1}
    assert conn.execute("SELECT raw_snippet, context_note FROM task_occurrences").fetchone() == (None, None)
    assert conn.execute("SELECT name LIKE 'ruolo %%' FROM roles").fetchone()[0]
    assert conn.execute("SELECT estratto FROM org_sintetica.occorrenze").fetchone()[0] == "passo originale"


def test_togli_testo_si_ferma_se_la_copia_non_coincide(conn, spazio):
    conn.execute("ALTER TABLE task_occurrences DROP CONSTRAINT task_occurrences_senza_testo")
    _registra(conn, spazio, spazio["task"][0], "Contabile", "passo originale")
    conn.execute("UPDATE task_occurrences SET raw_snippet = 'testo diverso'")
    with pytest.raises(RuntimeError):
        togli_testo_da_public(conn, spazio["admin"], spazio["org"])
