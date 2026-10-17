"""Abbinamento dei task di un'organizzazione al dataset consolidato (fase 3, ADR 0006).

Candidati nello spazio dell'organizzazione, proposte per vicinanza (embedding finto e deterministico),
coda per ambiguità, campione con la quota approvata, decisione in blocco del revisore e applicazione.
"""

from dataclasses import dataclass

import psycopg
import pytest
from psycopg import sql

from neartech.abbinamento import (
    MODELLO_EMBEDDING,
    PARAMETRO_QUOTA,
    applica_lotto,
    coda_revisione,
    crea_campione_del_lotto,
    decidi_lotto,
    proponi_abbinamenti,
    salva_candidati,
)
from neartech.campioni import esporta_campione, registra_giudizio
from neartech.governance import (
    DecisioneGiaPresa,
    ParametroAssente,
    approva_parametro,
    proponi_parametro,
    ritira_parametro,
)
from neartech.metrica import calcola_precisione
from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore

DIMENSIONE = 1024
SPAZIO = sql.Identifier("org_sintetica")


def _vettore(*componenti: tuple[int, float]) -> list[float]:
    v = [0.0] * DIMENSIONE
    for posizione, valore in componenti:
        v[posizione] = valore
    return v


# Vettori dei titoli: i candidati sono vicini ai task del dataset con lo stesso indice principale.
VETTORI = {
    "Redigere la prima nota contabile": _vettore((0, 1.0)),
    "Gestire le pratiche del personale": _vettore((1, 1.0)),
    "Accogliere gli utenti del servizio": _vettore((2, 1.0)),
    "Registrare la prima nota": _vettore((0, 1.0), (1, 0.1)),          # vicino al task 0, margine ampio
    "Curare le pratiche amministrative": _vettore((0, 0.7), (1, 0.7)),  # ambiguo fra 0 e 1
    "Pianificare i turni di lavoro": _vettore((3, 1.0)),                 # lontano da tutti: il revisore lo rifiuta
}


def incorpora(titoli: list[str]) -> list[list[float]]:
    return [VETTORI[t] for t in titoli]


@dataclass
class Attivita:
    titolo: str
    granularita: int
    testo_originale: str
    nota_contesto: str | None = None


def _parametro_comune(conn, admin, codice, valore):
    p = proponi_parametro(conn, admin, codice=codice, valore={"valore": valore}, descrizione=f"{codice} di prova",
                          motivazione="prova", org_id=None)
    approva_parametro(conn, admin, p, motivazione="prova")
    return p


@pytest.fixture
def mondo(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    org = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, revisore, "revisore", org, assegnata_da=admin)
    task = {}
    for titolo in ("Redigere la prima nota contabile", "Gestire le pratiche del personale",
                   "Accogliere gli utenti del servizio"):
        task[titolo] = str(conn.execute(
            "INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2) RETURNING task_id", (titolo,)
        ).fetchone()[0])
        conn.execute("INSERT INTO task_embeddings (task_id, model_name, vec) VALUES (%s, %s, %s::vector)",
                     (task[titolo], MODELLO_EMBEDDING, str(VETTORI[titolo])))
    parametri = {codice: _parametro_comune(conn, admin, codice, valore)
                 for codice, valore in ((PARAMETRO_QUOTA, 0.5), ("soglia_precisione_abbinamento", 0.9),
                                        ("regola_parziali", "errore"), ("livello_confidenza", 0.95))}
    attivita = [
        Attivita("Registrare la prima nota", 2, "registra la prima nota ogni giorno"),
        Attivita("Curare le pratiche amministrative", 2, "cura le pratiche"),
        Attivita("Pianificare i turni di lavoro", 2, "pianifica i turni", "settimanale"),
        Attivita("Area amministrativa", 3, "responsabile dell'area"),
    ]
    salvati = salva_candidati(conn, org, ruolo_nome="Impiegato amministrativo", nome_file="mansionario.docx",
                              sha256="a" * 64, licenza="interno", attivita=attivita,
                              model_name="modello", prompt_hash="hash")
    return {"admin": admin, "org": org, "revisore": revisore, "task": task, "salvati": salvati,
            "parametri": parametri}


def _lotto(conn, mondo, livello="campione"):
    return proponi_abbinamenti(conn, mondo["admin"], mondo["org"], livello_revisione=livello, incorpora=incorpora,
                               motivazione="primo lotto")


def _spazio(conn, query, *parametri):
    return conn.execute(sql.SQL(query).format(SPAZIO), parametri).fetchall()


# --- candidati -----------------------------------------------------------------------

def test_candidati_nello_spazio_senza_task_nel_dataset(conn, mondo):
    assert mondo["salvati"] == 3  # l'area di responsabilità non è un task
    assert [r[0] for r in _spazio(conn, "SELECT titolo FROM {}.candidati ORDER BY titolo")] == [
        "Curare le pratiche amministrative", "Pianificare i turni di lavoro", "Registrare la prima nota"]
    assert conn.execute("SELECT count(*) FROM canonical_tasks").fetchone()[0] == 3


def test_candidati_non_si_duplicano(conn, mondo):
    di_nuovo = salva_candidati(conn, mondo["org"], ruolo_nome="Impiegato amministrativo",
                               nome_file="mansionario.docx", sha256="a" * 64, licenza="interno",
                               attivita=[Attivita("Registrare la prima nota", 2, "registra")],
                               model_name="modello", prompt_hash="hash")
    assert di_nuovo == 0


# --- proposte e coda -------------------------------------------------------------------

def test_proposta_e_il_task_piu_vicino_con_le_chiavi_del_lotto(conn, mondo):
    lotto = _lotto(conn, mondo)
    righe = dict(_spazio(conn, """SELECT c.titolo, p.task_id FROM {0}.proposte_abbinamento p
                                  JOIN {0}.candidati c USING (candidato_id)"""))
    assert str(righe["Registrare la prima nota"]) == mondo["task"]["Redigere la prima nota contabile"]
    chiavi = _spazio(conn, "SELECT modello_embedding, vicini, livello_revisione, parametro_quota_id "
                           "FROM {}.lotti_abbinamento WHERE lotto_id = %s", lotto)[0]
    assert chiavi[:3] == (MODELLO_EMBEDDING, 5, "campione")
    assert str(chiavi[3]) == mondo["parametri"][PARAMETRO_QUOTA]


def test_coda_ordinata_per_ambiguita(conn, mondo):
    lotto = _lotto(conn, mondo)
    coda = coda_revisione(conn, mondo["revisore"], mondo["org"], lotto)
    titoli = [c["candidato"] for c in coda]
    assert titoli.index("Curare le pratiche amministrative") < titoli.index("Registrare la prima nota")
    assert all({"proposta_id", "distanza", "margine", "task_proposto"} <= set(c) for c in coda)


def test_senza_quota_approvata_il_lotto_a_campione_si_ferma(conn, mondo):
    ritira_parametro(conn, mondo["admin"], mondo["parametri"][PARAMETRO_QUOTA], motivazione="ritirata per prova")
    with pytest.raises(ParametroAssente):
        _lotto(conn, mondo)


def test_lotto_senza_revisione_dichiarato(conn, mondo):
    lotto = _lotto(conn, mondo, livello="nulla")
    assert _spazio(conn, "SELECT livello_revisione, parametro_quota_id FROM {}.lotti_abbinamento "
                         "WHERE lotto_id = %s", lotto) == [("nulla", None)]


def test_solo_chi_gestisce_il_dataset_propone(conn, mondo):
    with pytest.raises(PermessoNegato):
        proponi_abbinamenti(conn, mondo["revisore"], mondo["org"], livello_revisione="campione",
                            incorpora=incorpora, motivazione="x")


def test_candidati_gia_proposti_non_entrano_in_un_lotto_nuovo(conn, mondo):
    _lotto(conn, mondo)
    with pytest.raises(ValueError, match="nessun candidato"):
        _lotto(conn, mondo)


def test_dataset_vuoto_proposta_senza_task(conn, mondo):
    conn.execute("UPDATE canonical_tasks SET status = 'retired'")
    lotto = _lotto(conn, mondo, livello="nulla")
    assert {r[0] for r in _spazio(conn, "SELECT task_id FROM {}.proposte_abbinamento WHERE lotto_id = %s",
                                  lotto)} == {None}


# --- campione, misura, decisione e applicazione -------------------------------------

def _campione_giudicato(conn, mondo, lotto, esiti):
    campione = crea_campione_del_lotto(conn, mondo["revisore"], mondo["org"], lotto, seme=7,
                                       versione_istruzioni="istruzioni-abbinamento-v1", motivazione="campione")
    righe = esporta_campione(conn, mondo["revisore"], campione)
    for riga in righe:
        registra_giudizio(conn, mondo["revisore"], campione, riga["posizione"],
                          esiti.get(riga["candidato"], "corretto"), nota=None,
                          versione_istruzioni="istruzioni-abbinamento-v1")
    return campione, righe


def test_campione_con_la_quota_e_esportazione_cieca(conn, mondo):
    lotto = _lotto(conn, mondo)
    _, righe = _campione_giudicato(conn, mondo, lotto, {})
    assert len(righe) == 2  # 3 proposte, quota 0,5: dimensione arrotondata per eccesso
    assert set(righe[0]) == {"posizione", "candidato", "task", "proposta"}


def test_lotto_senza_revisione_non_ha_campione(conn, mondo):
    lotto = _lotto(conn, mondo, livello="nulla")
    with pytest.raises(ValueError, match="nulla"):
        crea_campione_del_lotto(conn, mondo["revisore"], mondo["org"], lotto, seme=1,
                                versione_istruzioni="v1", motivazione="x")


def test_decisione_a_campione_richiede_la_misura(conn, mondo):
    lotto = _lotto(conn, mondo)
    with pytest.raises(ValueError, match="misura"):
        decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto, rifiutate=[], motivazione="ok")


def _decidi_e_applica(conn, mondo, rifiuta=("Curare le pratiche amministrative", "Pianificare i turni di lavoro")):
    lotto = _lotto(conn, mondo)
    campione, _ = _campione_giudicato(conn, mondo, lotto, {})
    calcola_precisione(conn, mondo["revisore"], campione)
    proposte = {c["candidato"]: c["proposta_id"] for c in coda_revisione(conn, mondo["revisore"], mondo["org"], lotto)}
    atto = decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto,
                        rifiutate=[proposte[t] for t in rifiuta], motivazione="rivisto il campione")
    esito = applica_lotto(conn, mondo["admin"], mondo["org"], lotto, incorpora=incorpora, motivazione="applicazione")
    return lotto, atto, esito


def test_decisione_in_blocco_un_record_per_proposta(conn, mondo):
    _, atto, _ = _decidi_e_applica(conn, mondo)
    esiti = dict(_spazio(conn, """SELECT c.titolo, d.esito FROM {0}.decisioni_abbinamento d
                                  JOIN {0}.proposte_abbinamento p USING (proposta_id)
                                  JOIN {0}.candidati c USING (candidato_id)"""))
    assert esiti == {"Registrare la prima nota": "approvata", "Curare le pratiche amministrative": "rifiutata",
                     "Pianificare i turni di lavoro": "rifiutata"}
    dettagli = conn.execute("SELECT dettagli FROM registro_decisioni WHERE decisione_id = %s", (atto,)).fetchone()[0]
    assert dettagli["approvate"] == 1 and dettagli["rifiutate"] == 2 and "misura_id" in dettagli


def test_seconda_decisione_rifiutata(conn, mondo):
    lotto, _, _ = _decidi_e_applica(conn, mondo)
    with pytest.raises(DecisioneGiaPresa):
        decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto, rifiutate=[], motivazione="ripensamento")


def test_applicazione_collega_le_approvate_e_crea_i_task_nuovi(conn, mondo):
    _, _, esito = _decidi_e_applica(conn, mondo)
    assert esito == {"collegate": 1, "task_nuovi": 2, "occorrenze_nuove": 3}
    nota = mondo["task"]["Redigere la prima nota contabile"]
    pubblico = conn.execute("SELECT raw_snippet FROM task_occurrences WHERE task_id = %s", (nota,)).fetchall()
    assert pubblico == [(None,)]  # nessun testo in public
    nuovi = {r[0] for r in conn.execute("SELECT title_it FROM canonical_tasks").fetchall()} - set(mondo["task"])
    assert nuovi == {"Curare le pratiche amministrative", "Pianificare i turni di lavoro"}
    assert conn.execute(
        "SELECT count(*) FROM task_embeddings e JOIN canonical_tasks t USING (task_id) WHERE t.title_it = ANY(%s)",
        (list(nuovi),)).fetchone()[0] == 2


def test_applicazione_una_volta(conn, mondo):
    lotto, _, _ = _decidi_e_applica(conn, mondo)
    with pytest.raises(DecisioneGiaPresa):
        applica_lotto(conn, mondo["admin"], mondo["org"], lotto, incorpora=incorpora, motivazione="di nuovo")


def test_solo_il_revisore_decide_e_solo_chi_gestisce_il_dataset_applica(conn, mondo):
    lotto = _lotto(conn, mondo, livello="nulla")
    estraneo = crea_utente(conn, "sso|estraneo")
    with pytest.raises(PermessoNegato):
        decidi_lotto(conn, estraneo, mondo["org"], lotto, rifiutate=[], motivazione="x")
    decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto, rifiutate=[], motivazione="senza revisione")
    with pytest.raises(PermessoNegato):
        applica_lotto(conn, mondo["revisore"], mondo["org"], lotto, incorpora=incorpora, motivazione="x")


def test_applicazione_prima_della_decisione_rifiutata(conn, mondo):
    lotto = _lotto(conn, mondo, livello="nulla")
    with pytest.raises(ValueError, match="decis"):
        applica_lotto(conn, mondo["admin"], mondo["org"], lotto, incorpora=incorpora, motivazione="x")


def test_tabelle_dello_spazio_append_only(conn, mondo):
    _lotto(conn, mondo)
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute(sql.SQL("UPDATE {}.proposte_abbinamento SET distanza = 0").format(SPAZIO))


def test_il_flusso_funziona_con_il_ruolo_applicativo(conn, mondo):
    """Il ruolo applicativo non è proprietario: deve avere i privilegi su tutte le tabelle del flusso."""
    conn.execute("SET LOCAL ROLE neartech_app")
    _, _, esito = _decidi_e_applica(conn, mondo)
    assert esito == {"collegate": 1, "task_nuovi": 2, "occorrenze_nuove": 3}
    conn.execute("SET CONSTRAINTS ALL IMMEDIATE")  # anche i controlli differiti passano con il ruolo applicativo


def test_il_report_di_audit_riassume_il_lotto(conn, mondo):
    from neartech.audit import report_organizzazione

    lotto, _, _ = _decidi_e_applica(conn, mondo)
    auditor = crea_utente(conn, "sso|auditor")
    assegna_ruolo(conn, auditor, "auditor", assegnata_da=mondo["admin"])
    riepilogo = report_organizzazione(conn, auditor, mondo["org"])["abbinamenti"]
    assert [(r["lotto_id"], r["livello_revisione"], r["proposte"], r["approvate"], r["rifiutate"],
             r["collegate"], r["task_nuovi"]) for r in riepilogo] == [(lotto, "campione", 3, 1, 2, 1, 2)]


# --- correzioni dopo le revisioni della fase 3 ---------------------------------------

def test_dimensione_del_campione_in_aritmetica_decimale():
    from neartech.abbinamento import dimensione_campione
    assert dimensione_campione("0.07", 100) == 7  # con i float sarebbe 8
    assert dimensione_campione(0.5, 3) == 2
    assert dimensione_campione("0.01", 10) == 1


def test_un_solo_campione_per_lotto(conn, mondo):
    lotto = _lotto(conn, mondo)
    crea_campione_del_lotto(conn, mondo["revisore"], mondo["org"], lotto, seme=1, versione_istruzioni="v1",
                            motivazione="primo")
    with pytest.raises(psycopg.errors.UniqueViolation):
        crea_campione_del_lotto(conn, mondo["revisore"], mondo["org"], lotto, seme=2, versione_istruzioni="v1",
                                motivazione="secondo seme")


def test_la_quota_non_si_aggira_con_un_campione_piu_piccolo(conn, mondo):
    from neartech.campioni import crea_campione
    lotto = _lotto(conn, mondo)
    campione = crea_campione(conn, mondo["revisore"], org_id=mondo["org"], tipo="abbinamento",
                             filtro={"lotto": lotto}, criterio="casuale", dimensione=1, seme=3,
                             versione_istruzioni="v1", motivazione="campione ridotto")
    riga = esporta_campione(conn, mondo["revisore"], campione)[0]
    registra_giudizio(conn, mondo["revisore"], campione, riga["posizione"], "corretto", nota=None,
                      versione_istruzioni="v1")
    calcola_precisione(conn, mondo["revisore"], campione)
    with pytest.raises(ValueError, match="previste"):
        decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto, rifiutate=[], motivazione="ok")


def test_lotto_a_campione_su_dataset_vuoto_si_decide_senza_misura(conn, mondo):
    conn.execute("UPDATE canonical_tasks SET status = 'retired'")
    lotto = _lotto(conn, mondo)
    atto = decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto, rifiutate=[], motivazione="dataset vuoto")
    dettagli = conn.execute("SELECT dettagli FROM registro_decisioni WHERE decisione_id = %s", (atto,)).fetchone()[0]
    assert dettagli["proposte_con_task"] == 0 and "misura_id" not in dettagli
    conn.execute("UPDATE canonical_tasks SET status = 'active'")
    esito = applica_lotto(conn, mondo["admin"], mondo["org"], lotto, incorpora=incorpora, motivazione="x")
    assert esito["task_nuovi"] == 3
    conn.execute("SET CONSTRAINTS ALL IMMEDIATE")


def test_revisione_completa_dall_inizio_alla_fine(conn, mondo):
    lotto = _lotto(conn, mondo, livello="completa")
    campione = crea_campione_del_lotto(conn, mondo["revisore"], mondo["org"], lotto, seme=0,
                                       versione_istruzioni="v1", motivazione="tutte")
    for riga in esporta_campione(conn, mondo["revisore"], campione):
        registra_giudizio(conn, mondo["revisore"], campione, riga["posizione"], "corretto", nota=None,
                          versione_istruzioni="v1")
    calcola_precisione(conn, mondo["revisore"], campione)
    decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto, rifiutate=[], motivazione="tutte riviste")
    assert applica_lotto(conn, mondo["admin"], mondo["org"], lotto, incorpora=incorpora,
                         motivazione="x")["task_nuovi"] == 0


def test_campione_con_giudizi_errati_non_rifiutati_resta_nell_atto(conn, mondo):
    lotto = _lotto(conn, mondo)
    campione, righe = _campione_giudicato(conn, mondo, lotto, {"Registrare la prima nota": "errato",
                                                               "Curare le pratiche amministrative": "errato",
                                                               "Pianificare i turni di lavoro": "errato"})
    calcola_precisione(conn, mondo["revisore"], campione)
    atto = decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto, rifiutate=[], motivazione="approvo tutto")
    dettagli = conn.execute("SELECT dettagli FROM registro_decisioni WHERE decisione_id = %s", (atto,)).fetchone()[0]
    assert dettagli["campione_non_corrette_approvate"] == len(righe)


def test_task_proposto_ritirato_ferma_l_applicazione(conn, mondo):
    from neartech.abbinamento import TaskNonAttivo
    lotto = _lotto(conn, mondo, livello="nulla")
    decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto, rifiutate=[], motivazione="approvo")
    conn.execute("UPDATE canonical_tasks SET status = 'retired'")
    with pytest.raises(TaskNonAttivo):
        applica_lotto(conn, mondo["admin"], mondo["org"], lotto, incorpora=incorpora, motivazione="x")


def test_task_proposto_fuso_si_segue_fino_al_superstite(conn, mondo):
    lotto = _lotto(conn, mondo, livello="nulla")
    decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto, rifiutate=[], motivazione="approvo")
    nota, personale = mondo["task"]["Redigere la prima nota contabile"], mondo["task"]["Gestire le pratiche del personale"]
    conn.execute("UPDATE canonical_tasks SET status = 'merged', merged_into = %s WHERE task_id = %s", (personale, nota))
    applica_lotto(conn, mondo["admin"], mondo["org"], lotto, incorpora=incorpora, motivazione="x")
    assert conn.execute("SELECT count(*) FROM task_occurrences WHERE task_id = %s", (nota,)).fetchone()[0] == 0
    conn.execute("SET CONSTRAINTS ALL IMMEDIATE")


def test_embedding_incompleto_o_di_un_altro_modello_rifiutato(conn, mondo):
    with pytest.raises(ValueError, match="vettore"):
        proponi_abbinamenti(conn, mondo["admin"], mondo["org"], livello_revisione="nulla",
                            incorpora=lambda titoli: [], motivazione="x")

    def altro(titoli):
        return incorpora(titoli)
    altro.modello = "altro-modello"
    with pytest.raises(ValueError, match="modello"):
        proponi_abbinamenti(conn, mondo["admin"], mondo["org"], livello_revisione="nulla", incorpora=altro,
                            motivazione="x")


def test_due_candidati_dello_stesso_ruolo_sullo_stesso_task(conn, mondo):
    VETTORI["Tenere la prima nota"] = _vettore((0, 1.0), (1, 0.05))
    salva_candidati(conn, mondo["org"], ruolo_nome="Impiegato amministrativo", nome_file="mansionario.docx",
                    sha256="a" * 64, licenza="interno", attivita=[Attivita("Tenere la prima nota", 2, "tiene")],
                    model_name="modello", prompt_hash="hash")
    lotto = _lotto(conn, mondo, livello="nulla")
    decidi_lotto(conn, mondo["revisore"], mondo["org"], lotto, rifiutate=[], motivazione="approvo")
    esito = applica_lotto(conn, mondo["admin"], mondo["org"], lotto, incorpora=incorpora, motivazione="x")
    applicate = esito["collegate"] + esito["task_nuovi"]
    vuote = _spazio(conn, "SELECT count(*) FROM {}.applicazioni_abbinamento WHERE occorrenza_id IS NULL")[0][0]
    # Lo stesso ruolo sullo stesso task ha una sola occorrenza: le altre applicazioni restano senza.
    assert vuote >= 1 and esito["occorrenze_nuove"] == applicate - vuote


def test_un_lotto_di_un_altra_organizzazione_non_si_trova(conn, mondo):
    altra = crea_organizzazione(conn, mondo["admin"], nome="Altra", codice="altra")
    lotto = _lotto(conn, mondo, livello="nulla")
    with pytest.raises(LookupError):
        coda_revisione(conn, mondo["admin"], altra, lotto)


# --- vincoli nel database -------------------------------------------------------------

def test_database_rifiuta_una_decisione_con_l_atto_sbagliato(conn, mondo):
    lotto = _lotto(conn, mondo, livello="nulla")
    proposta = coda_revisione(conn, mondo["revisore"], mondo["org"], lotto)[0]["proposta_id"]
    atto_lotto = _spazio(conn, "SELECT decisione_id FROM {}.lotti_abbinamento WHERE lotto_id = %s", lotto)[0][0]
    with pytest.raises(psycopg.errors.RaiseException, match="non è l'atto"):
        conn.execute(sql.SQL("INSERT INTO {}.decisioni_abbinamento (proposta_id, esito, decisione_id) "
                             "VALUES (%s, 'approvata', %s)").format(SPAZIO), (proposta, atto_lotto))


def test_database_rifiuta_un_lotto_deciso_a_meta(conn, mondo):
    from neartech.registro import registra
    lotto = _lotto(conn, mondo, livello="nulla")
    proposta = coda_revisione(conn, mondo["revisore"], mondo["org"], lotto)[0]["proposta_id"]
    atto = registra(conn, autore_id=mondo["revisore"], tipo_oggetto="lotto_abbinamento", oggetto_id=lotto,
                    atto="approvazione", motivazione="a metà", org_id=mondo["org"])
    conn.execute(sql.SQL("INSERT INTO {}.decisioni_abbinamento (proposta_id, esito, decisione_id) "
                         "VALUES (%s, 'rifiutata', %s)").format(SPAZIO), (proposta, atto))
    with pytest.raises(psycopg.errors.RaiseException, match="per intero"):
        conn.execute("SET CONSTRAINTS ALL IMMEDIATE")


def test_database_rifiuta_un_elemento_di_un_altro_lotto(conn, mondo):
    primo = _lotto(conn, mondo, livello="campione")
    salva_candidati(conn, mondo["org"], ruolo_nome="Impiegato amministrativo", nome_file="mansionario.docx",
                    sha256="a" * 64, licenza="interno",
                    attivita=[Attivita("Gestire le pratiche del personale", 2, "gestisce")],
                    model_name="modello", prompt_hash="hash")
    VETTORI.setdefault("Gestire le pratiche del personale", _vettore((1, 1.0)))
    secondo = _lotto(conn, mondo, livello="campione")
    estranea = coda_revisione(conn, mondo["revisore"], mondo["org"], secondo)[0]["proposta_id"]
    campione = crea_campione_del_lotto(conn, mondo["revisore"], mondo["org"], primo, seme=1,
                                       versione_istruzioni="v1", motivazione="x")
    with pytest.raises(psycopg.errors.RaiseException, match="non del lotto"):
        conn.execute("INSERT INTO elementi_campione (campione_id, posizione, riferimento) VALUES (%s, 99, %s)",
                     (campione, psycopg.types.json.Jsonb({"proposta_id": estranea})))
