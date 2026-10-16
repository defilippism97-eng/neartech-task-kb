"""Fase 2: campioni di revisione, giudizi e metrica di precisione.

Dati sintetici. I valori dei parametri (soglia, regola, livello) sono di prova: in produzione
li approva l'amministratore tecnico come parametri comuni (metodologia, sezione 9).
"""

import psycopg
import pytest

from neartech.campioni import crea_campione, esporta_campione, importa_revisioni_crosswalk, registra_giudizio
from neartech.governance import ParametroAssente, approva_parametro, parametro_vigente, proponi_parametro
from neartech.metrica import CampioneIncompleto, DisaccordoRevisori, calcola_precisione, intervallo_wilson
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore


@pytest.fixture
def base(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    org = str(conn.execute("INSERT INTO organizations (name) VALUES ('Org sintetica') RETURNING org_id").fetchone()[0])
    revisore = crea_utente(conn, "sso|revisore")
    secondo = crea_utente(conn, "sso|secondo-revisore")
    comitato = crea_utente(conn, "sso|comitato")
    assegna_ruolo(conn, revisore, "revisore", org, assegnata_da=admin)
    assegna_ruolo(conn, secondo, "revisore", org, assegnata_da=admin)
    assegna_ruolo(conn, comitato, "comitato_guida", org, assegnata_da=admin)
    task = [str(conn.execute(
        "INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2) RETURNING task_id", (f"Task {i}",)
    ).fetchone()[0]) for i in range(6)]
    coppie = [(0, 1, "stessa_attivita"), (0, 2, "stessa_attivita"), (3, 4, "stessa_attivita"),
              (1, 5, "diversa"), (2, 5, "diversa")]
    for a, b, decisione in coppie:
        conn.execute(
            """INSERT INTO fusioni_proposte (task_id, altro_task_id, decisione, motivazione, model_name, prompt_hash)
               VALUES (%s, %s, %s, 'motivazione del modello', 'modello-prova', 'hash-prova')""",
            (task[a], task[b], decisione),
        )
    return {"admin": admin, "org": org, "revisore": revisore, "secondo": secondo, "comitato": comitato, "task": task}


def _parametri_comuni(conn, admin, *, soglia=0.9, regola="errore", livello=0.95):
    for codice, valore in (("soglia_precisione_abbinamento", soglia), ("regola_parziali", regola),
                           ("livello_confidenza", livello)):
        parametro = proponi_parametro(conn, admin, codice=codice, valore={"valore": valore},
                                      descrizione="valore di prova", motivazione="test", org_id=None)
        approva_parametro(conn, admin, parametro, motivazione="test")


def _campione_fusioni(conn, base, **kw):
    return crea_campione(conn, base["revisore"], org_id=base["org"], tipo="fusione",
                         filtro={"decisione": "stessa_attivita"}, criterio="tutte",
                         versione_istruzioni="istruzioni-v1", motivazione="revisione completa", **kw)


def _giudica(conn, revisore, campione, esiti):
    for posizione, esito in enumerate(esiti, start=1):
        registra_giudizio(conn, revisore, campione, posizione, esito, nota=None, versione_istruzioni="istruzioni-v1")


# --- parametri comuni -----------------------------------------------------------

def test_amministratore_approva_parametri_comuni(conn, base):
    _parametri_comuni(conn, base["admin"])
    assert parametro_vigente(conn, "regola_parziali", base["org"]).valore == {"valore": "errore"}


def test_comitato_non_propone_parametri_comuni(conn, base):
    with pytest.raises(PermessoNegato):
        proponi_parametro(conn, base["comitato"], codice="regola_parziali", valore={"valore": "errore"},
                          descrizione="x", motivazione="x", org_id=None)


def test_amministratore_non_propone_parametri_di_organizzazione(conn, base):
    with pytest.raises(PermessoNegato):
        proponi_parametro(conn, base["admin"], codice="soglia_locale", valore={"valore": 1},
                          descrizione="x", motivazione="x", org_id=base["org"])


# --- campioni ---------------------------------------------------------------------

def test_campione_completo_delle_fusioni(conn, base):
    campione = _campione_fusioni(conn, base)
    righe = conn.execute(
        "SELECT popolazione, dimensione FROM campioni_revisione WHERE campione_id = %s", (campione,)
    ).fetchone()
    assert righe == (3, 3)
    assert conn.execute(
        "SELECT atto FROM registro_decisioni WHERE tipo_oggetto = 'campione_revisione' AND oggetto_id = %s",
        (campione,),
    ).fetchall() == [("approvazione",)]


def test_campione_casuale_ripetibile_con_lo_stesso_seme(conn, base):
    def elementi(seme):
        campione = crea_campione(conn, base["revisore"], org_id=base["org"], tipo="fusione", filtro={},
                                 criterio="casuale", dimensione=3, seme=seme,
                                 versione_istruzioni="istruzioni-v1", motivazione="controllo")
        return [r[0] for r in conn.execute(
            "SELECT riferimento FROM elementi_campione WHERE campione_id = %s ORDER BY posizione", (campione,)
        ).fetchall()]
    assert elementi(42) == elementi(42)


def test_dimensione_oltre_la_popolazione_rifiutata(conn, base):
    with pytest.raises(ValueError):
        crea_campione(conn, base["revisore"], org_id=base["org"], tipo="fusione", filtro={"decisione": "diversa"},
                      criterio="casuale", dimensione=5, seme=1, versione_istruzioni="v1", motivazione="x")


def test_solo_i_revisori_creano_campioni(conn, base):
    with pytest.raises(PermessoNegato):
        crea_campione(conn, base["comitato"], org_id=base["org"], tipo="fusione", filtro={}, criterio="tutte",
                      versione_istruzioni="v1", motivazione="x")


def test_esportazione_cieca(conn, base):
    campione = _campione_fusioni(conn, base)
    righe = esporta_campione(conn, base["revisore"], campione)
    assert len(righe) == 3
    assert {"posizione", "proposta"} <= set(righe[0])
    assert not {"motivazione", "model_name", "prompt_hash"} & set(righe[0])
    assert "motivazione del modello" not in str(righe)


# --- giudizi ----------------------------------------------------------------------

def test_esito_sconosciuto_rifiutato(conn, base):
    campione = _campione_fusioni(conn, base)
    with pytest.raises(ValueError):
        registra_giudizio(conn, base["revisore"], campione, 1, "forse", nota=None, versione_istruzioni="v1")


def test_solo_chi_giudica_i_task_registra_giudizi(conn, base):
    campione = _campione_fusioni(conn, base)
    with pytest.raises(PermessoNegato):
        registra_giudizio(conn, base["comitato"], campione, 1, "corretto", nota=None, versione_istruzioni="v1")


def test_giudizi_non_si_modificano(conn, base):
    campione = _campione_fusioni(conn, base)
    _giudica(conn, base["revisore"], campione, ["corretto"])
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("UPDATE giudizi_revisione SET esito = 'errato'")


# --- metrica ----------------------------------------------------------------------

def test_intervallo_di_wilson_noto():
    basso, alto = intervallo_wilson(36, 40, 0.95)
    assert basso == pytest.approx(0.7695, abs=1e-3)
    assert alto == pytest.approx(0.9604, abs=1e-3)


def test_precisione_con_parziali_come_errori(conn, base):
    _parametri_comuni(conn, base["admin"])
    campione = _campione_fusioni(conn, base)
    _giudica(conn, base["revisore"], campione, ["corretto", "corretto", "parziale"])
    misura = calcola_precisione(conn, base["revisore"], campione)
    assert (misura.n_corretti, misura.n_parziali, misura.n_errati) == (2, 1, 0)
    assert misura.precisione == pytest.approx(2 / 3)
    assert misura.esito == "sotto_soglia"
    assert misura.intervallo[0] < misura.precisione < misura.intervallo[1]
    chiavi = conn.execute(
        """SELECT parametro_soglia_id, parametro_regola_id, parametro_confidenza_id, origine_proposte
           FROM misure_precisione WHERE misura_id = %s""",
        (misura.misura_id,),
    ).fetchone()
    assert all(chiavi[:3])
    assert chiavi[3] == [{"model_name": "modello-prova", "prompt_hash": "hash-prova"}]


def test_precisione_con_parziali_esclusi(conn, base):
    _parametri_comuni(conn, base["admin"], regola="escluso")
    campione = _campione_fusioni(conn, base)
    _giudica(conn, base["revisore"], campione, ["corretto", "corretto", "parziale"])
    misura = calcola_precisione(conn, base["revisore"], campione)
    assert misura.precisione == pytest.approx(1.0)
    assert misura.esito == "sopra_soglia"


def test_senza_parametri_il_calcolo_si_ferma(conn, base):
    campione = _campione_fusioni(conn, base)
    _giudica(conn, base["revisore"], campione, ["corretto", "corretto", "corretto"])
    with pytest.raises(ParametroAssente):
        calcola_precisione(conn, base["revisore"], campione)


def test_campione_incompleto(conn, base):
    _parametri_comuni(conn, base["admin"])
    campione = _campione_fusioni(conn, base)
    _giudica(conn, base["revisore"], campione, ["corretto"])
    with pytest.raises(CampioneIncompleto):
        calcola_precisione(conn, base["revisore"], campione)


def test_disaccordo_fra_revisori_ferma_il_calcolo(conn, base):
    _parametri_comuni(conn, base["admin"])
    campione = _campione_fusioni(conn, base)
    _giudica(conn, base["revisore"], campione, ["corretto", "corretto", "corretto"])
    _giudica(conn, base["secondo"], campione, ["corretto", "errato", "corretto"])
    with pytest.raises(DisaccordoRevisori) as errore:
        calcola_precisione(conn, base["revisore"], campione)
    assert errore.value.posizioni == [2]


def test_conta_l_ultimo_giudizio_di_ciascun_revisore(conn, base):
    _parametri_comuni(conn, base["admin"])
    campione = _campione_fusioni(conn, base)
    _giudica(conn, base["revisore"], campione, ["corretto", "errato", "corretto"])
    registra_giudizio(conn, base["revisore"], campione, 2, "corretto", nota="ripensamento", versione_istruzioni="v1")
    assert calcola_precisione(conn, base["revisore"], campione).precisione == pytest.approx(1.0)


def test_misure_non_si_modificano(conn, base):
    _parametri_comuni(conn, base["admin"])
    campione = _campione_fusioni(conn, base)
    _giudica(conn, base["revisore"], campione, ["corretto", "corretto", "corretto"])
    calcola_precisione(conn, base["revisore"], campione)
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("UPDATE misure_precisione SET precisione = 0")


# --- importazione del crosswalk già rivisto ---------------------------------------------

def test_importa_revisioni_crosswalk(conn, base):
    fonte = conn.execute(
        """INSERT INTO sources (kind, name, version, license, content_hash)
           VALUES ('taxonomy', 'Tassonomia sintetica', '1', 'aperta', 'h') RETURNING source_id"""
    ).fetchone()[0]
    nodi = [conn.execute(
        """INSERT INTO taxonomy_nodes (scheme, code, label, lang, source_id)
           VALUES ('ONET_TASK', %s, %s, 'en', %s) RETURNING node_id""",
        (f"N{i}", f"Nodo {i}", fonte),
    ).fetchone()[0] for i in range(3)]
    for nodo, esito in zip(nodi, ("ok", "parziale", "no")):
        conn.execute(
            """INSERT INTO task_mappings (task_id, node_id, relation, confidence, rationale)
               VALUES (%s, %s, 'exact', 0.9, 'motivazione')""",
            (base["task"][0], nodo),
        )
        conn.execute(
            """INSERT INTO revisioni_crosswalk (task_id, node_id, relazione_proposta, esito, revisore, campione)
               VALUES (%s, %s, 'exact', %s, 'responsabile', 'crosswalk-prova')""",
            (base["task"][0], nodo, esito),
        )
    campione = importa_revisioni_crosswalk(conn, base["revisore"], org_id=base["org"], campione="crosswalk-prova")
    esiti = [r[0] for r in conn.execute(
        "SELECT esito FROM giudizi_revisione WHERE campione_id = %s ORDER BY posizione", (campione,)
    ).fetchall()]
    assert sorted(esiti) == ["corretto", "errato", "parziale"]
    _parametri_comuni(conn, base["admin"])
    assert calcola_precisione(conn, base["revisore"], campione).precisione == pytest.approx(1 / 3)
