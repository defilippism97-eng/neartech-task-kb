"""Pipeline dei documenti dalla piattaforma (fase 6, fetta 5), con modello ed embedding finti.

Caricamento nello spazio, stima dal parametro dei prezzi, avvio con atto e job, gestori del lavoratore,
lotto del revisore dal livello alla decisione (revisione cieca), applicazione accodata.
"""

import io
import json
import zipfile
from types import SimpleNamespace
from xml.sax.saxutils import escape

import pytest
from psycopg import sql

from neartech import pipeline
from neartech.abbinamento import MODELLO_EMBEDDING, PARAMETRO_QUOTA, decidi_lotto, imposta_livello
from neartech.campioni import registra_giudizio
from neartech.coda import completa, prendi
from neartech.governance import approva_parametro, proponi_parametro
from neartech.metrica import calcola_precisione
from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore
from neartech.scomposizione import MODEL_ID

DIMENSIONE = 1024
SPAZIO = sql.Identifier("org_sintetica")
RIGHE = ["TITOLO DELLA POSIZIONE", "Impiegato amministrativo", "PRINCIPALI ATTIVITÀ",
         "Registra la prima nota ogni giorno.", "Pianifica i turni del reparto."]


def docx(righe: list[str]) -> bytes:
    corpo = "".join(f"<w:p><w:r><w:t>{escape(r)}</w:t></w:r></w:p>" for r in righe)
    xml = ('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/'
           f'wordprocessingml/2006/main"><w:body>{corpo}</w:body></w:document>')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("word/document.xml", xml)
    return buffer.getvalue()


def _vettore(indice: int) -> list[float]:
    v = [0.0] * DIMENSIONE
    v[indice] = 1.0
    return v


VETTORI = {"Redigere la prima nota contabile": _vettore(0), "Registrare la prima nota": _vettore(0),
           "Pianificare i turni del reparto": _vettore(3)}


def incorpora(titoli):
    return [VETTORI[t] for t in titoli]


incorpora.modello = MODELLO_EMBEDDING


class Client:
    """Modello finto: le attività citano passi presenti nel documento."""

    def __init__(self):
        self.messages = self
        self.chiamate = 0

    def create(self, **_):
        self.chiamate += 1
        testo = json.dumps({"attivita": [
            {"titolo": "Registrare la prima nota", "granularita": 2, "testo_originale": RIGHE[3], "nota_contesto": None},
            {"titolo": "Pianificare i turni del reparto", "granularita": 2, "testo_originale": RIGHE[4],
             "nota_contesto": None}]})
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=testo)])


def _parametro(conn, admin, codice, valore):
    p = proponi_parametro(conn, admin, codice=codice, valore=valore, descrizione=f"{codice} di prova",
                          motivazione="prova", org_id=None)
    approva_parametro(conn, admin, p, motivazione="prova")


PREZZI = {"modello": MODEL_ID, "ingresso_eur_mtok": 3, "uscita_eur_mtok": 15, "caratteri_per_token": 4,
          "uscita_su_ingresso": 0.5}


@pytest.fixture
def mondo(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    org = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, revisore, "revisore", org, assegnata_da=admin)
    task = str(conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2) RETURNING task_id",
                            ("Redigere la prima nota contabile",)).fetchone()[0])
    conn.execute("INSERT INTO task_embeddings (task_id, model_name, vec) VALUES (%s, %s, %s::vector)",
                 (task, MODELLO_EMBEDDING, str(VETTORI["Redigere la prima nota contabile"])))
    for codice, valore in ((PARAMETRO_QUOTA, 1.0), ("soglia_precisione_abbinamento", 0.5),
                           ("regola_parziali", "errore"), ("livello_confidenza", 0.95)):
        _parametro(conn, admin, codice, {"valore": valore})
    return {"admin": admin, "org": org, "revisore": revisore}


def _esegui(conn, gestori):
    """Un passo del lavoratore: prende un job, lo esegue con il gestore, lo chiude."""
    job = prendi(conn, "prova", tipi=list(gestori))
    assert job is not None
    gestori[job.tipo](conn, job.payload)
    assert completa(conn, job.job_id, "prova")
    return job


def test_caricamento_nello_spazio_con_atto_e_senza_duplicati(conn, mondo):
    primo = pipeline.carica_file(conn, mondo["admin"], mondo["org"], "mansionario.docx", docx(RIGHE))
    assert primo["nuovo"] and primo["ruolo"] == "Impiegato amministrativo"
    assert not pipeline.carica_file(conn, mondo["admin"], mondo["org"], "copia.docx", docx(RIGHE))["nuovo"]
    testo = conn.execute(sql.SQL("SELECT testo FROM {}.caricamenti").format(SPAZIO)).fetchall()
    assert len(testo) == 1 and "prima nota" in testo[0][0]
    atto = conn.execute("SELECT atto, dettagli FROM registro_decisioni WHERE tipo_oggetto = 'caricamento_file'").fetchone()
    assert atto[0] == "proposta" and "nome_file" not in atto[1]  # il nome del file resta nello spazio


@pytest.mark.parametrize("nome, dati", [("mansionario.pdf", b"x"), ("rotto.docx", b"non un zip"),
                                        ("senza.docx", docx(["Solo testo, nessun titolo"]))])
def test_caricamento_rifiuta_file_non_leggibili(conn, mondo, nome, dati):
    with pytest.raises(ValueError):
        pipeline.carica_file(conn, mondo["admin"], mondo["org"], nome, dati)


def test_solo_l_amministratore_carica(conn, mondo):
    with pytest.raises(PermessoNegato):
        pipeline.carica_file(conn, mondo["revisore"], mondo["org"], "m.docx", docx(RIGHE))
    with pytest.raises(PermessoNegato):
        pipeline.stato_pipeline(conn, mondo["revisore"], mondo["org"])


def test_senza_prezzi_approvati_niente_stima_e_niente_avvio(conn, mondo):
    c = pipeline.carica_file(conn, mondo["admin"], mondo["org"], "m.docx", docx(RIGHE))["caricamento_id"]
    stato = pipeline.stato_pipeline(conn, mondo["admin"], mondo["org"])
    assert stato["prezzi"] is None and stato["documenti"][0]["stima"] is None
    with pytest.raises(ValueError, match="prezzi_scomposizione"):
        pipeline.avvia_scomposizione(conn, mondo["admin"], mondo["org"], [c], motivazione="avvio")


def test_avvio_con_stima_nell_atto_e_job_senza_testo(conn, mondo):
    _parametro(conn, mondo["admin"], pipeline.PARAMETRO_PREZZI, PREZZI)
    c = pipeline.carica_file(conn, mondo["admin"], mondo["org"], "m.docx", docx(RIGHE))["caricamento_id"]
    stima = pipeline.stato_pipeline(conn, mondo["admin"], mondo["org"])["stima_da_avviare"]
    assert stima["token_ingresso"] > 0 and stima["costo_massimo"] == pytest.approx(2 * stima["costo"], abs=1e-4)
    esito = pipeline.avvia_scomposizione(conn, mondo["admin"], mondo["org"], [c], motivazione="avvio del pilota")
    assert esito["costo"] == stima["costo"]
    dettagli = conn.execute("SELECT dettagli FROM registro_decisioni WHERE decisione_id = %s", (esito["atto"],)).fetchone()[0]
    assert dettagli["stima_costo"] == stima["costo"] and dettagli["modello"] == MODEL_ID
    payload = conn.execute("SELECT payload FROM jobs WHERE kind = %s", (pipeline.TIPO_SCOMPOSIZIONE,)).fetchone()[0]
    assert set(payload) == {"org_id", "caricamento_id", "utente_id", "atto"}
    assert pipeline.stato_pipeline(conn, mondo["admin"], mondo["org"])["documenti"][0]["stato"] == "in_coda"
    with pytest.raises(ValueError, match="già avviato"):
        pipeline.avvia_scomposizione(conn, mondo["admin"], mondo["org"], [c], motivazione="di nuovo")


def test_senza_client_o_embedding_i_job_restano_in_coda():
    assert pipeline.gestori(client=None, incorpora=None) == {}
    assert set(pipeline.gestori(client=None, incorpora=incorpora)) == {pipeline.TIPO_PROPOSTA, pipeline.TIPO_APPLICAZIONE}


def test_dal_documento_al_lotto_applicato(conn, mondo):
    admin, revisore, org = mondo["admin"], mondo["revisore"], mondo["org"]
    _parametro(conn, admin, pipeline.PARAMETRO_PREZZI, PREZZI)
    client = Client()
    gestori = pipeline.gestori(client=client, incorpora=incorpora)
    c = pipeline.carica_file(conn, admin, org, "m.docx", docx(RIGHE))["caricamento_id"]
    pipeline.avvia_scomposizione(conn, admin, org, [c], motivazione="avvio")
    _esegui(conn, gestori)
    stato = pipeline.stato_pipeline(conn, admin, org)
    assert client.chiamate == 1 and stato["documenti"][0]["stato"] == "fatto"
    assert stato["documenti"][0]["candidati"] == 2 and stato["candidati_da_proporre"] == 2

    pipeline.avvia_proposta(conn, admin, org, motivazione="primo lotto")
    with pytest.raises(ValueError, match="già in coda"):
        pipeline.avvia_proposta(conn, admin, org, motivazione="doppio")
    _esegui(conn, gestori)
    [lotto] = pipeline.lotti(conn, revisore, org)
    assert lotto["stato"] == "da_impostare" and lotto["proposte"] == 2

    imposta_livello(conn, revisore, org, lotto["lotto_id"], livello_revisione="campione", motivazione="a campione")
    assert pipeline.lotti(conn, revisore, org)[0]["stato"] == "da_campionare"
    pipeline.crea_campione(conn, revisore, org, lotto["lotto_id"], motivazione="campione del lotto")
    dettaglio = pipeline.dettaglio_lotto(conn, revisore, org, lotto["lotto_id"])
    assert dettaglio["lotto"]["stato"] == "da_giudicare"
    assert dettaglio["proposte"] is None  # revisione cieca: niente distanze prima della misura
    for elemento in dettaglio["campione"]["elementi"]:
        assert set(elemento) == {"posizione", "candidato", "task", "proposta", "mio_esito"}
        registra_giudizio(conn, revisore, dettaglio["lotto"]["campione_id"], elemento["posizione"], "corretto",
                          nota=None, versione_istruzioni=pipeline.ISTRUZIONI_ABBINAMENTO)
    assert pipeline.lotti(conn, revisore, org)[0]["stato"] == "da_misurare"
    calcola_precisione(conn, revisore, dettaglio["lotto"]["campione_id"])
    dettaglio = pipeline.dettaglio_lotto(conn, revisore, org, lotto["lotto_id"])
    assert dettaglio["lotto"]["stato"] == "da_decidere" and len(dettaglio["proposte"]) == 2
    assert dettaglio["campione"]["elementi"][0]["mio_esito"] == "corretto"

    with pytest.raises(ValueError, match="non è da applicare"):
        pipeline.avvia_applicazione(conn, admin, org, lotto["lotto_id"], motivazione="troppo presto")
    turni = [x["proposta_id"] for x in dettaglio["proposte"] if x["candidato"] == "Pianificare i turni del reparto"]
    decidi_lotto(conn, revisore, org, lotto["lotto_id"], rifiutate=turni, motivazione="i turni sono un task nuovo")
    pipeline.avvia_applicazione(conn, admin, org, lotto["lotto_id"], motivazione="applica")
    assert pipeline.lotti(conn, revisore, org)[0]["stato"] == "in_applicazione"
    _esegui(conn, gestori)
    assert pipeline.lotti(conn, revisore, org)[0]["stato"] == "applicato"
    assert conn.execute("SELECT count(*) FROM canonical_tasks WHERE title_it = 'Pianificare i turni del reparto'"
                        ).fetchone()[0] == 1


def test_un_documento_fallito_si_riavvia(conn, mondo):
    admin, org = mondo["admin"], mondo["org"]
    _parametro(conn, admin, pipeline.PARAMETRO_PREZZI, PREZZI)
    c = pipeline.carica_file(conn, admin, org, "m.docx", docx(RIGHE))["caricamento_id"]
    pipeline.avvia_scomposizione(conn, admin, org, [c], motivazione="avvio")
    conn.execute("UPDATE jobs SET status = 'failed', ultimo_errore = 'ScompostoError: risposta non valida'")
    documento = pipeline.stato_pipeline(conn, admin, org)["documenti"][0]
    assert documento["stato"] == "fallito" and documento["stima"] is not None
    pipeline.avvia_scomposizione(conn, admin, org, [c], motivazione="secondo tentativo")
    assert pipeline.stato_pipeline(conn, admin, org)["documenti"][0]["stato"] == "in_coda"
