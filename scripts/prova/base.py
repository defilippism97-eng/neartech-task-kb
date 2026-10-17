"""Seme di base della prova locale: l'organizzazione immaginaria ACME S.p.A. (ruoli di staff) con utenti, task,
giudizi, snapshot di copertura di riserva, parametri approvati e calcolo, come in un pilota vero.

I dati sono quelli di sempre (stesso seme casuale, stesso ordine): le corsie aggiungono i propri nei loro moduli.
"""

import json
import random

import psycopg

from neartech.abbinamento import MODELLO_EMBEDDING
from neartech.calcolo import calcola_organizzazione
from neartech.capacita import pubblica_snapshot
from neartech.governance import approva_parametro, proponi_parametro
from neartech.occorrenze import documento, registra_occorrenza, ruolo
from neartech.organizzazioni import crea_organizzazione
from neartech.permessi import assegna_ruolo, crea_utente, inizializza_amministratore
from neartech.pipeline import PARAMETRO_PREZZI
from neartech.scomposizione import MODEL_ID

from .comune import RADICE, Contesto, incorpora_prova

# Archetipi di task: domanda (k1, k2, k3), copertura di riserva (k1, k2, k3), affidabilità r, d1, d2.
ARCHETIPI = {
    "relazione": ((3, 3, 2), (2, 2, 2), 2, (4, 3)),
    "presenza": ((3, 3, 4), (1, 1, 1), 3, (3, 3)),
    "operativo": ((1, 1, 0), (3, 3, 3), 1, (1, 1)),
    "pianificazione": ((2, 3, 1), (3, 2, 3), 2, (2, 1)),
    "responsabilita": ((2, 2, 1), (3, 3, 3), 2, (1, 4)),
    "analisi": ((3, 3, 1), (1, 1, 2), 3, (1, 1)),
}

# Ruoli di staff di un'impresa immaginaria.
RUOLI = {
    "Specialista risorse umane": [
        ("Colloquio di selezione", "relazione"), ("Gestione di un conflitto tra colleghi", "presenza"),
        ("Inserimento dei nuovi assunti", "relazione"), ("Elaborazione delle presenze", "operativo"),
        ("Redazione degli annunci di lavoro", "operativo"), ("Comunicazione di un provvedimento disciplinare", "responsabilita")],
    "Addetto contabilità": [
        ("Registrazione delle fatture passive", "operativo"), ("Riconciliazioni bancarie", "operativo"),
        ("Gestione dei solleciti ai clienti", "pianificazione"), ("Chiusura contabile mensile", "analisi"),
        ("Risposta alle richieste dei fornitori", "operativo")],
    "Controller": [
        ("Analisi degli scostamenti di budget", "analisi"), ("Preparazione del budget annuale", "pianificazione"),
        ("Presentazione dei risultati alla direzione", "relazione"), ("Chiusura contabile mensile", "analisi")],
    "Responsabile acquisti": [
        ("Negoziazione con i fornitori", "relazione"), ("Qualifica dei nuovi fornitori", "responsabilita"),
        ("Emissione degli ordini di acquisto", "operativo"), ("Pianificazione dei fabbisogni", "pianificazione")],
    "Tecnico IT": [
        ("Gestione dei ticket di primo livello", "operativo"), ("Installazione e cablaggio delle postazioni", "presenza"),
        ("Gestione degli accessi ai sistemi", "responsabilita"), ("Formazione degli utenti sui nuovi strumenti", "relazione")],
    "Specialista marketing": [
        ("Redazione dei contenuti per il sito", "operativo"), ("Analisi dei risultati delle campagne", "analisi"),
        ("Organizzazione di eventi con i clienti", "presenza"), ("Gestione dei rapporti con l'agenzia", "relazione")],
}


def _limita(x: float) -> float:
    return max(0.0, min(4.0, x))


def semina(conn: psycopg.Connection, ctx: Contesto) -> None:
    """Organizzazione sintetica con risultati calcolati dal motore, come in un pilota vero."""
    caso = random.Random(20261017)
    admin = inizializza_amministratore(conn, "prova|admin")
    ctx.admin = ctx.utenti["prova|admin"] = admin
    org = crea_organizzazione(conn, admin, nome="ACME S.p.A.", codice="acme")
    ctx.org, ctx.codice_org = org, "acme"
    for soggetto, nome_ruolo in (("prova|comitato", "comitato_guida"), ("prova|revisore", "revisore")):
        ctx.utenti[soggetto] = crea_utente(conn, soggetto)
        assegna_ruolo(conn, ctx.utenti[soggetto], nome_ruolo, org, assegnata_da=admin)

    conn.execute("INSERT INTO rubric_versions (version, is_current, approved_by, approved_at) "
                 "VALUES ('bozza-3', true, 'comitato di prova', now())")
    conn.execute("""INSERT INTO weight_profiles (profile_id, org_id, w_k1, w_k2, w_k3, lambda_r, w_d1, w_d2, w_d3, w_d4,
                                                 theta_n, theta_d, is_active, approved_by, approved_at)
                    VALUES ('neartech-comune-prova', NULL, 0.4, 0.4, 0.2, 0.5, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5, true,
                            'comitato di prova', now())""")
    snapshot = str(conn.execute(
        """INSERT INTO capability_snapshots (as_of, method_version, half_life_days, status, tipo_capacita)
           VALUES ('2026-10-17', 'riserva-prova', 180, 'proposed', 'riserva') RETURNING snapshot_id""").fetchone()[0])
    ctx.snapshot = snapshot

    task_id = ctx.task_id
    doc = documento(conn, org, nome_file="mansionari.docx", sha256="ab" * 32, licenza="interno")
    ctx.documento = doc
    for nome_ruolo, compiti in RUOLI.items():
        r = ruolo(conn, org, nome_ruolo)
        ctx.ruoli[nome_ruolo] = r
        for titolo, archetipo in compiti:
            if titolo not in task_id:
                task_id[titolo] = str(conn.execute(
                    "INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2) RETURNING task_id",
                    (titolo,)).fetchone()[0])
                domanda, copertura, affidabilita, (d1, d2) = ARCHETIPI[archetipo]
                for dim, c in zip(("k1", "k2", "k3"), copertura):
                    c = _limita(c + caso.choice((-1, 0, 0, 1)))
                    conn.execute("""INSERT INTO task_capability (snapshot_id, task_id, dimension, c_mean, c_low, c_high, n_evidence)
                                    VALUES (%s, %s, %s, %s, %s, %s, 1)""",
                                 (snapshot, task_id[titolo], dim, c, _limita(c - 0.5), _limita(c + 0.5)))
                valori = dict(zip(("k1", "k2", "k3"), domanda)) | {"r": affidabilita, "d1": d1, "d2": d2}
                for voce, valore in valori.items():
                    # Due stime del modello per voce, a volte diverse: l'incertezza che la piattaforma mostra.
                    for scarto in (0, caso.choice((-1, 0, 0, 0, 1))):
                        conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind,
                                                                     rater_ref, rubric_version)
                                        VALUES ('task', %s, %s, %s, 'llm', 'modello-prova', 'bozza-3')""",
                                     (task_id[titolo], voce, _limita(valore + scarto)))
                if caso.random() < 0.3:  # alcuni task già giudicati dai revisori
                    for voce in ("k2", "d1"):
                        conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind,
                                                                     rater_ref, rubric_version)
                                        VALUES ('task', %s, %s, %s, 'expert', 'revisore-prova', 'bozza-3')""",
                                     (task_id[titolo], voce, valori[voce]))
            registra_occorrenza(conn, org, task_id=task_id[titolo], ruolo_id=r, documento_id=doc,
                                estratto=titolo, nota_contesto=None, model_name="modello-prova", prompt_hash="prova")
    pubblica_snapshot(conn, admin, snapshot, nota="copertura di riserva sintetica")
    soglia = proponi_parametro(conn, admin, codice="soglia_stabilita_quadrante", valore={"valore": 0.8},
                               descrizione="soglia di stabilità del quadrante", motivazione="dati di prova", org_id=None)
    approva_parametro(conn, admin, soglia, motivazione="dati di prova")
    ctx.parametri["soglia_stabilita_quadrante"] = soglia
    # Questionario degli indirizzi in bozza (docs/governance): approvato solo nei dati di prova.
    bozza = json.loads((RADICE / "docs" / "governance" / "questionario-indirizzi-bozza-1.json").read_text(encoding="utf-8"))
    questionario = proponi_parametro(conn, admin, codice="questionario_indirizzi", valore=bozza,
                                     descrizione="questionario degli indirizzi (bozza)", motivazione="dati di prova",
                                     org_id=None)
    approva_parametro(conn, admin, questionario, motivazione="dati di prova")
    ctx.parametri["questionario_indirizzi"] = questionario
    ctx.utenti["prova|auditor"] = crea_utente(conn, "prova|auditor")
    assegna_ruolo(conn, ctx.utenti["prova|auditor"], "auditor", assegnata_da=admin)
    # Pipeline dei documenti (fetta 5): vettori di prova dei task, quota e metrica degli abbinamenti, prezzi.
    # I prezzi sono valori di prova per vedere la stima, non un listino.
    for titolo, tid in task_id.items():
        conn.execute("INSERT INTO task_embeddings (task_id, model_name, vec) VALUES (%s, %s, %s::vector)",
                     (tid, MODELLO_EMBEDDING, str(incorpora_prova([titolo])[0])))
    for codice, valore in (("quota_revisione_abbinamenti", {"valore": 0.5}),
                           ("soglia_precisione_abbinamento", {"valore": 0.8}),
                           ("regola_parziali", {"valore": "errore"}), ("livello_confidenza", {"valore": 0.95}),
                           (PARAMETRO_PREZZI, {"modello": MODEL_ID, "ingresso_eur_mtok": 3, "uscita_eur_mtok": 15,
                                               "caratteri_per_token": 3.5, "uscita_su_ingresso": 0.6})):
        p = proponi_parametro(conn, admin, codice=codice, valore=valore, descrizione=f"{codice} (prova)",
                              motivazione="dati di prova", org_id=None)
        approva_parametro(conn, admin, p, motivazione="dati di prova")
        ctx.parametri[codice] = p
    esito = calcola_organizzazione(conn, admin, org, seme=20261017, estrazioni=500)
    ctx.calcolo = esito
    print(f"ACME S.p.A.: {len(task_id)} task, {esito['occorrenze']} occorrenze, {esito['nuove']} risultati")
