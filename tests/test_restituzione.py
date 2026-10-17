"""Restituzione dei risultati a un'organizzazione (fase 5; registro di metodo, sezione 24).

Lettura per organizzazione e per ruolo con le chiavi dei risultati, le ragioni per cui sono provvisori, la coda
delle occorrenze da rivedere (con la soglia di stabilità approvata, se c'è) e l'approvazione del comitato guida.
Nessun output riguarda una persona: solo ruoli e task.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from neartech.calcolo import calcola_organizzazione
from neartech.governance import DecisioneGiaPresa, adotta_parametro_comune, approva_parametro, proponi_parametro
from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente
from neartech.restituzione import (
    PARAMETRO_STABILITA,
    VERSIONE_RESTITUZIONE,
    RestituzioneSuperata,
    _quadrante,
    approva_restituzione,
    restituzione_in_markdown,
    restituzione_organizzazione,
)
from test_calcolo import mondo  # noqa: F401  (stessa organizzazione sintetica del calcolo)


@pytest.fixture
def comitato(conn, mondo):  # noqa: F811
    utente = crea_utente(conn, "sso|comitato")
    assegna_ruolo(conn, utente, "comitato_guida", mondo["org"], assegnata_da=mondo["admin"])
    return utente


def _giudizio(conn, task, voce, valore, valutatore="llm", rif="modello-prova"):
    conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind, rater_ref,
                                                 rubric_version) VALUES ('task', %s, %s, %s, %s, %s, 'rubrica-prova')""",
                 (task, voce, valore, valutatore, rif))


def _soglia(conn, mondo, valore):
    p = proponi_parametro(conn, mondo["admin"], codice=PARAMETRO_STABILITA, valore={"valore": valore},
                          descrizione="soglia di stabilità del quadrante", motivazione="prova", org_id=None)
    approva_parametro(conn, mondo["admin"], p, motivazione="prova")
    return p


def _calcola(conn, mondo, seme=7):
    calcola_organizzazione(conn, mondo["admin"], mondo["org"], seme=seme, estrazioni=200)


def _incerto(conn, mondo):
    # Due giudizi di modello diversi su k1 e k2: N oscilla fra Q1 (circa un quarto delle estrazioni) e Q3.
    _giudizio(conn, mondo["task"], "k1", 0)
    _giudizio(conn, mondo["task"], "k2", 0)
    _calcola(conn, mondo)


def test_restituzione_con_chiavi_avvertenze_e_ruoli(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert r["versione"] == VERSIONE_RESTITUZIONE and r["organizzazione"]["codice"] == "sintetica"
    assert r["chiavi"] == {
        "rubriche": ["rubrica-prova"], "profili": ["profilo-prova"],
        "soglie_quadranti": [{"profilo": "profilo-prova", "theta_n": 0.5, "theta_d": 0.5}],
        "snapshot": [mondo["snapshot"]], "metodi_capacita": ["riserva-prova"], "versioni_calcolo": ["calcolo-nd-v2"],
        "capacita": ["riserva"], "componenti_d": ["d1", "d2"], "modelli_giudizi": ["modello-prova"]}
    assert r["avvertenze"] == ["occorrenze_senza_risultato", "capacita_di_riserva", "d_provvisorio", "pesi_uguali",
                               "soglia_di_stabilita_non_approvata"]
    assert r["riepilogo"]["occorrenze"] == 2 and r["riepilogo"]["con_risultato"] == 1
    assert r["riepilogo"]["quadranti"] == {"q1": 1, "q2": 0, "q3": 0, "q4": 0}
    (ruolo,) = r["ruoli"]
    assert ruolo["ruolo"] == "Coordinatore" and ruolo["occorrenze"] == 1 and ruolo["provvisorio"] is True
    assert ruolo["pesi_tempo"] == "uguali" and ruolo["quadranti"] == {"q1": 1, "q2": 0, "q3": 0, "q4": 0}
    assert ruolo["baricentro_n"] == pytest.approx(0.825) and ruolo["baricentro_d"] == pytest.approx(0.875)


def test_senza_risultati_la_restituzione_e_vuota_e_lo_dice(conn, mondo, comitato):  # noqa: F811
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert r["ruoli"] == [] and r["riepilogo"]["con_risultato"] == 0 and "nessun_risultato" in r["avvertenze"]


def test_nessun_valutatore_persona_nella_restituzione(conn, mondo, comitato):  # noqa: F811
    _giudizio(conn, mondo["task"], "d1", 0, valutatore="expert", rif="esperto-riservato")
    _calcola(conn, mondo)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert "esperto-riservato" not in json.dumps(r) and r["chiavi"]["modelli_giudizi"] == ["modello-prova"]


# --- coda da rivedere -----------------------------------------------------------------

def test_senza_soglia_approvata_la_coda_non_si_calcola(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert r["soglia_stabilita"] is None and r["da_rivedere"] is None and r["riepilogo"]["instabili"] is None


def test_con_la_soglia_la_coda_elenca_le_occorrenze_incerte(conn, mondo, comitato):  # noqa: F811
    _incerto(conn, mondo)
    _soglia(conn, mondo, 0.8)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert r["soglia_stabilita"]["valore"] == 0.8 and r["soglia_stabilita"]["comune"] is True
    assert "soglia_di_stabilita_non_approvata" not in r["avvertenze"]
    (incerta,) = r["da_rivedere"]
    assert incerta["task"] == "Colloquio con la famiglia" and incerta["ruolo"] == "Coordinatore"
    assert incerta["quadrante"] == "q3" and 0.6 < incerta["probabilita"] < 0.8
    assert r["riepilogo"]["instabili"] == 1 and r["ruoli"][0]["instabili"] == 1


def test_un_occorrenza_stabile_non_va_in_coda(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    _soglia(conn, mondo, 0.8)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert r["da_rivedere"] == [] and r["riepilogo"]["instabili"] == 0


def test_soglia_comune_da_adottare(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    parametro = _soglia(conn, mondo, 0.8)
    assert "soglia_comune_non_adottata" in restituzione_organizzazione(conn, comitato, mondo["org"])["avvertenze"]
    adotta_parametro_comune(conn, comitato, org_id=mondo["org"], parametro_id=parametro, motivazione="adottata")
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert "soglia_comune_non_adottata" not in r["avvertenze"] and r["soglia_stabilita"]["adozione_id"] is not None


@pytest.mark.parametrize("valore", [1.5, 0, -0.2, True, "0.8"])
def test_soglia_fuori_intervallo_rifiutata(conn, mondo, comitato, valore):  # noqa: F811
    _calcola(conn, mondo)
    _soglia(conn, mondo, valore)
    with pytest.raises(ValueError, match=PARAMETRO_STABILITA):
        restituzione_organizzazione(conn, comitato, mondo["org"])


def test_quadrante_a_pari_probabilita():
    assert _quadrante({"p_q1": 0.1, "p_q2": 0.4, "p_q3": 0.4, "p_q4": 0.1}) == ("q2", 0.4, True)
    assert _quadrante({"p_q1": 0.0, "p_q2": 0.0, "p_q3": 0.75, "p_q4": 0.25}) == ("q3", 0.75, False)


# --- quale risultato vale ------------------------------------------------------------

def test_un_risultato_per_occorrenza_nella_vista(conn, mondo):  # noqa: F811
    _calcola(conn, mondo)
    _giudizio(conn, mondo["task"], "d1", 0, valutatore="expert", rif="esperto-1")
    _calcola(conn, mondo)
    _calcola(conn, mondo, seme=8)
    assert conn.execute("SELECT count(*), count(DISTINCT occurrence_id) FROM v_risultati_vigenti").fetchone() == (1, 1)


def test_un_occorrenza_che_cambia_task_perde_il_risultato(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    altro = conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES ('Altro', 2) RETURNING task_id"
                         ).fetchone()[0]
    conn.execute("UPDATE task_occurrences SET task_id = %s WHERE occurrence_id = %s", (altro, mondo["occorrenza"]))
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert r["riepilogo"]["con_risultato"] == 0 and r["ruoli"] == []


def test_i_modelli_sono_quelli_dei_giudizi_usati(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    prima = restituzione_organizzazione(conn, comitato, mondo["org"])
    _giudizio(conn, mondo["task"], "d1", 2, rif="modello-successivo")  # dopo il calcolo: non usato
    dopo = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert dopo["chiavi"]["modelli_giudizi"] == ["modello-prova"] and dopo["impronta"] == prima["impronta"]


def test_modelli_dedotti_per_i_risultati_senza_giudizi_registrati(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    # Un risultato come quelli calcolati prima della migrazione 0036, più recente: vale lui.
    conn.execute("""INSERT INTO policy_estimates (occurrence_id, task_id, role_id, profile_id, snapshot_id,
                      rubric_version, n_mean, n_sd, d_mean, d_sd, p_q1, p_q2, p_q3, p_q4, d_source_mix,
                      versione_calcolo, seme, estrazioni, tipo_capacita, componenti_d, d_provvisorio,
                      impronta_input, calcolata_da)
                    SELECT occurrence_id, task_id, role_id, profile_id, snapshot_id, rubric_version, n_mean, n_sd,
                           d_mean, d_sd, p_q1, p_q2, p_q3, p_q4, d_source_mix, versione_calcolo, 99, estrazioni,
                           tipo_capacita, componenti_d, d_provvisorio, impronta_input, calcolata_da
                    FROM policy_estimates WHERE occurrence_id = %s""", (mondo["occorrenza"],))
    _giudizio(conn, mondo["task"], "d1", 2, rif="modello-successivo")
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert r["chiavi"]["modelli_giudizi"] == ["modello-prova"] and "modelli_dedotti" in r["avvertenze"]


def test_la_lettura_funziona_in_una_transazione_di_sola_lettura(conn, mondo):  # noqa: F811
    from neartech.restituzione import _costruisci  # senza permessi: il log di accesso scriverebbe
    _calcola(conn, mondo)
    conn.execute("SET LOCAL transaction_read_only = on")  # come lo script con conn.read_only
    assert _costruisci(conn, mondo["org"])["riepilogo"]["con_risultato"] == 1


# --- permessi e Markdown ---------------------------------------------------------------

def test_solo_chi_legge_l_organizzazione(conn, mondo):  # noqa: F811
    with pytest.raises(PermessoNegato):
        restituzione_organizzazione(conn, crea_utente(conn, "sso|estraneo"), mondo["org"])


def test_markdown_leggibile(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    testo = restituzione_in_markdown(restituzione_organizzazione(conn, comitato, mondo["org"]))
    assert testo.startswith("# Restituzione") and "Coordinatore" in testo and "riserva" in testo
    assert "Impronta" in testo and "N alto da 0.5" in testo


def test_markdown_non_si_rompe_con_nomi_strani(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    r["ruoli"][0]["ruolo"] = "Capo | reparto\n# titolo <b>"
    r["organizzazione"]["nome"] = "Org\n## falsa"
    righe = restituzione_in_markdown(r).splitlines()
    assert "Capo \\| reparto # titolo &lt;b&gt;" in "\n".join(righe)
    assert not any(riga.startswith(("# titolo", "## falsa")) for riga in righe)


# --- approvazione ---------------------------------------------------------------------

def test_il_comitato_approva_la_restituzione_con_la_sua_impronta(conn, mondo, comitato):  # noqa: F811
    _incerto(conn, mondo)
    _soglia(conn, mondo, 0.8)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert r["approvazione"] is None and r["da_rivedere"]
    letta = json.loads(json.dumps(r, ensure_ascii=False, indent=2))  # come la scrive e la rilegge lo script
    atto = approva_restituzione(conn, comitato, mondo["org"], letta, motivazione="letta in seduta")
    riga = conn.execute("SELECT tipo_oggetto, oggetto_id, atto FROM registro_decisioni WHERE decisione_id = %s",
                        (atto,)).fetchone()
    assert riga == ("restituzione", r["impronta"], "approvazione")
    di_nuovo = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert di_nuovo["impronta"] == r["impronta"] and di_nuovo["approvazione"] == atto
    with pytest.raises(DecisioneGiaPresa):
        approva_restituzione(conn, comitato, mondo["org"], r, motivazione="di nuovo")


def test_l_indice_impedisce_una_seconda_approvazione(conn, mondo, comitato):  # noqa: F811
    import psycopg
    from neartech.registro import registra
    _calcola(conn, mondo)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    approva_restituzione(conn, comitato, mondo["org"], r, motivazione="prima")
    with pytest.raises(psycopg.errors.UniqueViolation):
        with conn.transaction():
            registra(conn, autore_id=comitato, tipo_oggetto="restituzione", oggetto_id=r["impronta"],
                     atto="approvazione", motivazione="seconda", org_id=mondo["org"])


def test_una_restituzione_riguarda_un_organizzazione(conn, mondo, comitato):  # noqa: F811
    import psycopg
    with pytest.raises(psycopg.errors.CheckViolation):
        with conn.transaction():
            conn.execute("""INSERT INTO registro_decisioni (tipo_oggetto, oggetto_id, atto, autore_id, motivazione)
                            VALUES ('restituzione', 'x', 'approvazione', %s, 'senza organizzazione')""", (comitato,))


def test_l_impronta_cambia_se_cambiano_i_risultati(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    prima = restituzione_organizzazione(conn, comitato, mondo["org"])
    _giudizio(conn, mondo["task"], "d1", 0, valutatore="expert", rif="esperto-1")
    _calcola(conn, mondo)
    dopo = restituzione_organizzazione(conn, comitato, mondo["org"])
    assert dopo["impronta"] != prima["impronta"]
    with pytest.raises(RestituzioneSuperata):
        approva_restituzione(conn, comitato, mondo["org"], prima, motivazione="x")


def test_una_restituzione_alterata_non_si_approva(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    r["riepilogo"]["quadranti"]["q1"] = 0
    with pytest.raises(ValueError, match="impronta"):
        approva_restituzione(conn, comitato, mondo["org"], r, motivazione="x")
    with pytest.raises(ValueError, match="non valida"):
        approva_restituzione(conn, comitato, mondo["org"], ["non", "un", "oggetto"], motivazione="x")


def test_la_restituzione_di_un_altra_organizzazione(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    altra = crea_organizzazione(conn, mondo["admin"], nome="Altra", codice="altra")
    comitato_altra = crea_utente(conn, "sso|comitato-altra")
    assegna_ruolo(conn, comitato_altra, "comitato_guida", altra, assegnata_da=mondo["admin"])
    with pytest.raises(ValueError, match="altra organizzazione"):
        approva_restituzione(conn, comitato_altra, altra, r, motivazione="x")
    with pytest.raises(PermessoNegato):
        approva_restituzione(conn, comitato_altra, mondo["org"], r, motivazione="x")


def test_solo_il_comitato_approva(conn, mondo, comitato):  # noqa: F811
    _calcola(conn, mondo)
    r = restituzione_organizzazione(conn, comitato, mondo["org"])
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, revisore, "revisore", mondo["org"], assegnata_da=mondo["admin"])
    with pytest.raises(PermessoNegato):
        approva_restituzione(conn, revisore, mondo["org"], r, motivazione="x")


# --- script ------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def script():
    percorso = Path(__file__).resolve().parents[1] / "scripts" / "restituzione.py"
    spec = importlib.util.spec_from_file_location("script_restituzione", percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_lo_script_scrive_fuori_dal_repository(script, tmp_path):
    with pytest.raises(SystemExit, match="fuori dal repository"):
        script.file_di_uscita(str(tmp_path / "dentro" / "r"), radice=tmp_path)
    (tmp_path / "r.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="esiste già"):
        script.file_di_uscita(str(tmp_path / "r"), radice=tmp_path / "repo")


def test_lo_script_non_lascia_un_json_orfano(script, tmp_path):
    file_md, file_json = tmp_path / "r.md", tmp_path / "r.json"
    script.scrivi_file(file_md, "# testo", file_json, "{}")
    assert file_md.read_text(encoding="utf-8") == "# testo" and file_json.read_text(encoding="utf-8") == "{}"
    altro_md = tmp_path / "s.md"
    with pytest.raises(FileExistsError):
        script.scrivi_file(altro_md, "# altro", file_json, "{}")  # il JSON esiste già
    assert not altro_md.exists()


def test_lo_script_rifiuta_un_file_non_valido(script, tmp_path):
    (tmp_path / "rotto.json").write_text("{non json", encoding="utf-8")
    (tmp_path / "lista.json").write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit, match="non leggibile"):
        script.leggi_restituzione(str(tmp_path / "rotto.json"))
    with pytest.raises(SystemExit, match="atteso un oggetto"):
        script.leggi_restituzione(str(tmp_path / "lista.json"))
