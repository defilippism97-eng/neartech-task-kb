"""Test della scomposizione delle job description con un client finto."""

import json
from types import SimpleNamespace

import pytest

from neartech.scomposizione import (
    MODEL_ID,
    DocumentoJob,
    ScompostoError,
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


def test_salvataggio_riusa_il_titolo_canonico_tra_ruoli(conn):
    doc_a = _doc("A.docx", TESTO_A, "RESPONSABILE UFFICIO ACQUISTI")
    doc_b = _doc("B.docx", TESTO_B, "IMPIEGATO UFFICIO ACQUISTI")
    titolo = "Aggiornare la banca dati fornitori"
    att_a = proponi_attivita(FakeClient(_risposta((titolo, "Aggiorna la banca dati fornitori aziendali."))), doc_a, [])
    att_b = proponi_attivita(FakeClient(_risposta((titolo, "Aggiorna la banca dati fornitori aziendali."))), doc_b, titoli_attivi(conn))

    assert salva_documento(conn, doc_a, att_a) == 1
    assert salva_documento(conn, doc_b, att_b) == 1
    # Un solo task canonico, due occorrenze (una per ruolo).
    assert conn.execute("SELECT count(*) FROM canonical_tasks WHERE title_it = %s", (titolo,)).fetchone()[0] == 1
    assert conn.execute("SELECT count(*) FROM task_occurrences").fetchone()[0] == 2
    modello = conn.execute("SELECT DISTINCT model_name FROM task_occurrences").fetchall()
    assert modello == [(MODEL_ID,)]


def test_rilancio_non_duplica(conn):
    doc = _doc("A.docx", TESTO_A, "RESPONSABILE UFFICIO ACQUISTI")
    att = proponi_attivita(FakeClient(_risposta(("Aggiornare la banca dati fornitori", "Aggiorna la banca dati fornitori aziendali."))), doc, [])
    assert salva_documento(conn, doc, att) == 1
    assert salva_documento(conn, doc, att) == 0
    # Si contano solo le righe di questo test: altre suite possono lasciare fonti nel database di test.
    assert conn.execute("SELECT count(*) FROM sources WHERE name = 'A.docx'").fetchone()[0] == 1
    assert conn.execute("SELECT count(*) FROM roles WHERE name = 'RESPONSABILE UFFICIO ACQUISTI'").fetchone()[0] == 1
