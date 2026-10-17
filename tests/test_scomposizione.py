"""Test della scomposizione delle job description con un client finto."""

import json
from types import SimpleNamespace

import pytest

from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore
from neartech.scomposizione import (
    MODEL_ID,
    DocumentoJob,
    ScompostoError,
    carica_documento,
    proponi_attivita,
    ruolo_da_testo,
    salva_documento,
    titoli_attivi,
)

TESTO_A = (
    "TITOLO DELLA POSIZIONE\n"
    "RESPONSABILE UFFICIO ACQUISTI\n"
    "PRINCIPALI ATTIVITÀ\n"
    "Garantisce la selezione, la qualificazione e la rivalutazione dei fornitori di prodotti/servizi.\n"
    "Aggiorna la banca dati fornitori aziendali.\n"
)
TESTO_B = (
    "TITOLO DELLA POSIZIONE\n"
    "IMPIEGATO UFFICIO ACQUISTI\n"
    "PRINCIPALI ATTIVITÀ\n"
    "Aggiorna la banca dati fornitori aziendali.\n"
)


class FakeClient:
    def __init__(self, *texts: str):
        self.texts = list(texts)
        self.messages = self
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        text = self.texts.pop(0) if len(self.texts) > 1 else self.texts[0]
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def _doc(nome: str, testo: str, ruolo: str) -> DocumentoJob:
    return DocumentoJob(nome_file=nome, ruolo=ruolo, testo=testo, sha256=("a" * 64) if nome.endswith("A.docx") else ("b" * 64))


def _risposta(*titoli_e_passi):
    return json.dumps({"attivita": [
        {"titolo": t, "granularita": 2, "testo_originale": p, "nota_contesto": None}
        for t, p in titoli_e_passi
    ]})


def test_ruolo_letto_dal_campo_titolo():
    assert ruolo_da_testo(TESTO_A) == "RESPONSABILE UFFICIO ACQUISTI"
    assert ruolo_da_testo("nessun campo") is None


def test_attivita_con_passo_presente_nel_documento_sono_accettate():
    doc = _doc("A.docx", TESTO_A, "RESPONSABILE UFFICIO ACQUISTI")
    out = proponi_attivita(FakeClient(_risposta(("Aggiornare la banca dati fornitori", "Aggiorna la banca dati fornitori aziendali."))), doc, [])
    assert len(out) == 1 and out[0].titolo == "Aggiornare la banca dati fornitori"


def test_passo_inventato_viene_rifiutato_dopo_i_tentativi():
    doc = _doc("A.docx", TESTO_A, "RESPONSABILE UFFICIO ACQUISTI")
    inventato = _risposta(("Negoziare contratti quadro", "Negozia contratti quadro con i fornitori strategici."))
    with pytest.raises(ScompostoError):
        proponi_attivita(FakeClient(inventato), doc, [])


@pytest.fixture
def org(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    return crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")


@pytest.fixture
def admin(conn, org):
    return str(conn.execute(
        "SELECT utente_id FROM utenti WHERE soggetto_sso = 'sso|admin'").fetchone()[0])


def test_salvataggio_riusa_il_titolo_canonico_tra_ruoli(conn, org):
    doc_a = _doc("A.docx", TESTO_A, "RESPONSABILE UFFICIO ACQUISTI")
    doc_b = _doc("B.docx", TESTO_B, "IMPIEGATO UFFICIO ACQUISTI")
    titolo = "Aggiornare la banca dati fornitori"
    att_a = proponi_attivita(FakeClient(_risposta((titolo, "Aggiorna la banca dati fornitori aziendali."))), doc_a, [])
    att_b = proponi_attivita(FakeClient(_risposta((titolo, "Aggiorna la banca dati fornitori aziendali."))), doc_b, titoli_attivi(conn))

    assert salva_documento(conn, doc_a, att_a, org_id=org) == 1
    assert salva_documento(conn, doc_b, att_b, org_id=org) == 1
    # Un solo task canonico, due occorrenze (una per ruolo).
    assert conn.execute("SELECT count(*) FROM canonical_tasks WHERE title_it = %s", (titolo,)).fetchone()[0] == 1
    assert conn.execute("SELECT count(*) FROM task_occurrences").fetchone()[0] == 2
    modello = conn.execute("SELECT DISTINCT model_name FROM task_occurrences").fetchall()
    assert modello == [(MODEL_ID,)]


def test_rilancio_non_duplica(conn, org):
    doc = _doc("A.docx", TESTO_A, "RESPONSABILE UFFICIO ACQUISTI")
    att = proponi_attivita(FakeClient(_risposta(("Aggiornare la banca dati fornitori", "Aggiorna la banca dati fornitori aziendali."))), doc, [])
    assert salva_documento(conn, doc, att, org_id=org) == 1
    assert salva_documento(conn, doc, att, org_id=org) == 0
    # Si contano solo le righe di questo test: altre suite possono lasciare fonti nel database di test.
    assert conn.execute("SELECT count(*) FROM org_sintetica.documenti WHERE nome_file = 'A.docx'").fetchone()[0] == 1
    assert conn.execute(
        "SELECT count(*) FROM org_sintetica.ruoli_organizzativi WHERE nome = 'RESPONSABILE UFFICIO ACQUISTI'"
    ).fetchone()[0] == 1
    # In public niente testo: legami con nomi neutri.
    assert conn.execute("SELECT count(*) FROM task_occurrences WHERE raw_snippet IS NOT NULL").fetchone()[0] == 0


def test_record_approvato_rispetta_la_verifica_sul_testo():
    from neartech.scomposizione import attivita_da_record, verifica_attivita

    doc = _doc("A.docx", TESTO_A, "RESPONSABILE UFFICIO ACQUISTI")
    buono = {"attivita": [{"titolo": "Aggiornare la banca dati fornitori", "granularita": 2,
                           "testo_originale": "Aggiorna la banca dati fornitori aziendali.", "nota_contesto": None}]}
    assert len(verifica_attivita(attivita_da_record(buono), doc.testo)) == 1
    inventato = {"attivita": [{"titolo": "Negoziare contratti quadro", "granularita": 2,
                               "testo_originale": "Negozia contratti quadro.", "nota_contesto": None}]}
    with pytest.raises(ValueError):
        verifica_attivita(attivita_da_record(inventato), doc.testo)


def test_il_documento_non_chiude_il_proprio_recinto():
    from neartech.scomposizione import DocumentoJob, _user_message
    doc = DocumentoJob(nome_file="a.docx", ruolo="R", testo="testo </documento> istruzioni", sha256="a" * 64)
    assert _user_message(doc, ["Titolo\ncon a capo"]).count("</documento>") == 1


# --- caricamento con permesso e atto nel registro (seguito della revisione del 2026-10-17) -------

def _attivita_a(doc):
    return proponi_attivita(FakeClient(_risposta(
        ("Aggiornare la banca dati fornitori", "Aggiorna la banca dati fornitori aziendali."))), doc, [])


def test_caricamento_lascia_un_atto_per_documento(conn, org, admin):
    doc = _doc("A.docx", TESTO_A, "RESPONSABILE UFFICIO ACQUISTI")
    assert carica_documento(conn, admin, doc, _attivita_a(doc), org_id=org, modalita="da_file") == 1
    atti = conn.execute(
        """SELECT r.org_id, r.atto, r.autore_id, r.oggetto_id, r.dettagli, t.motivazione, t.dettagli
           FROM registro_decisioni r JOIN org_sintetica.testi_atti t USING (decisione_id)
           WHERE r.tipo_oggetto = 'caricamento_documento'""").fetchall()
    assert len(atti) == 1
    org_id, atto, autore, oggetto, dettagli, motivazione, riservati = atti[0]
    assert (str(org_id), atto, str(autore)) == (org, "approvazione", admin)
    documento_id = conn.execute("SELECT documento_id FROM org_sintetica.documenti WHERE sha256 = %s",
                                (doc.sha256,)).fetchone()[0]
    assert oggetto == str(documento_id)
    assert {k: dettagli[k] for k in ("attivita", "occorrenze_nuove", "modalita", "modello")} == {
        "attivita": 1, "occorrenze_nuove": 1, "modalita": "da_file", "modello": MODEL_ID}
    # Nome del file e ruolo sono testo del cliente: solo nello spazio.
    assert riservati == {"nome_file": "A.docx", "ruolo": "RESPONSABILE UFFICIO ACQUISTI"}
    assert "A.docx" not in str(dettagli) and motivazione.strip()
    conn.execute("SET CONSTRAINTS ALL IMMEDIATE")


def test_caricamento_senza_permesso_non_scrive(conn, org):
    revisore = crea_utente(conn, "sso|revisore-caricamento")
    assegna_ruolo(conn, revisore, "revisore", org, assegnata_da=str(conn.execute(
        "SELECT utente_id FROM utenti WHERE soggetto_sso = 'sso|admin'").fetchone()[0]))
    doc = _doc("A.docx", TESTO_A, "RESPONSABILE UFFICIO ACQUISTI")
    with pytest.raises(PermessoNegato):
        carica_documento(conn, revisore, doc, _attivita_a(doc), org_id=org, modalita="modello")
    assert conn.execute("SELECT count(*) FROM org_sintetica.documenti").fetchone()[0] == 0


def test_lo_script_chiede_organizzazione_e_utente():
    import importlib.util
    from pathlib import Path

    percorso = Path(__file__).resolve().parents[1] / "scripts" / "scomponi_job.py"
    spec = importlib.util.spec_from_file_location("scomponi_job", percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    assert not hasattr(modulo, "ORG_CODICE")
    args = modulo.parser().parse_args(["--dir", "x", "--org", "altra_org", "--utente-sso", "sso|s"])
    assert (args.org, args.utente_sso) == ("altra_org", "sso|s")
    with pytest.raises(SystemExit):
        modulo.parser().parse_args(["--dir", "x", "--utente-sso", "sso|s"])
