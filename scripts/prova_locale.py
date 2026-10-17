"""Ambiente di prova locale della piattaforma (fase 6), con dati sintetici.

Avvia un PostgreSQL temporaneo (tests/pg_locale.py), applica schema e migrazioni, crea un'organizzazione
immaginaria ("ACME S.p.A.", ruoli di staff) con ruoli, task, giudizi, snapshot di riserva e calcolo, poi avvia la
piattaforma su http://127.0.0.1:8000 con l'accesso di sviluppo. Alla chiusura il database viene distrutto.

Non usa mai DATABASE_URL: nessun contatto con il database di produzione.

Uso:
  (cd web && npm run build)
  python scripts/prova_locale.py [--porta 8000]
Soggetti di prova: prova|comitato (comitato guida), prova|revisore, prova|admin.
"""

import argparse
import random
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "src"))
sys.path.insert(0, str(RADICE / "tests"))

import psycopg  # noqa: E402
import uvicorn  # noqa: E402
from pg_locale import cartella_binari, postgres_temporaneo  # noqa: E402

from neartech.api.app import crea_app  # noqa: E402
from neartech.api.config import Impostazioni  # noqa: E402
from neartech.calcolo import calcola_organizzazione  # noqa: E402
from neartech.capacita import pubblica_snapshot  # noqa: E402
from neartech.governance import approva_parametro, proponi_parametro  # noqa: E402
from neartech.migrazioni import CARTELLA_CONDIVISA, applica  # noqa: E402
from neartech.occorrenze import documento, registra_occorrenza, ruolo  # noqa: E402
from neartech.organizzazioni import crea_organizzazione  # noqa: E402
from neartech.permessi import assegna_ruolo, crea_utente, inizializza_amministratore  # noqa: E402

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


def _prepara(url: str) -> None:
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute((RADICE / "db" / "schema.sql").read_text(encoding="utf-8"))
        applica(conn, CARTELLA_CONDIVISA)


def _limita(x: float) -> float:
    return max(0.0, min(4.0, x))


def popola(conn: psycopg.Connection) -> None:
    """Organizzazione sintetica con risultati calcolati dal motore, come in un pilota vero."""
    caso = random.Random(20261017)
    admin = inizializza_amministratore(conn, "prova|admin")
    org = crea_organizzazione(conn, admin, nome="ACME S.p.A.", codice="acme")
    for soggetto, nome_ruolo in (("prova|comitato", "comitato_guida"), ("prova|revisore", "revisore")):
        assegna_ruolo(conn, crea_utente(conn, soggetto), nome_ruolo, org, assegnata_da=admin)

    conn.execute("INSERT INTO rubric_versions (version, is_current, approved_by, approved_at) "
                 "VALUES ('rubrica-prova', true, 'comitato di prova', now())")
    conn.execute("""INSERT INTO weight_profiles (profile_id, org_id, w_k1, w_k2, w_k3, lambda_r, w_d1, w_d2, w_d3, w_d4,
                                                 theta_n, theta_d, is_active, approved_by, approved_at)
                    VALUES ('neartech-comune-prova', NULL, 0.4, 0.4, 0.2, 0.5, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5, true,
                            'comitato di prova', now())""")
    snapshot = str(conn.execute(
        """INSERT INTO capability_snapshots (as_of, method_version, half_life_days, status, tipo_capacita)
           VALUES ('2026-10-17', 'riserva-prova', 180, 'proposed', 'riserva') RETURNING snapshot_id""").fetchone()[0])

    task_id: dict[str, str] = {}
    doc = documento(conn, org, nome_file="mansionari.docx", sha256="ab" * 32, licenza="interno")
    for nome_ruolo, compiti in RUOLI.items():
        r = ruolo(conn, org, nome_ruolo)
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
                                        VALUES ('task', %s, %s, %s, 'llm', 'modello-prova', 'rubrica-prova')""",
                                     (task_id[titolo], voce, _limita(valore + scarto)))
                if caso.random() < 0.3:  # alcuni task già giudicati dai revisori
                    for voce in ("k2", "d1"):
                        conn.execute("""INSERT INTO assessment_runs (target_kind, target_id, item, value, rater_kind,
                                                                     rater_ref, rubric_version)
                                        VALUES ('task', %s, %s, %s, 'expert', 'revisore-prova', 'rubrica-prova')""",
                                     (task_id[titolo], voce, valori[voce]))
            registra_occorrenza(conn, org, task_id=task_id[titolo], ruolo_id=r, documento_id=doc,
                                estratto=titolo, nota_contesto=None, model_name="modello-prova", prompt_hash="prova")
    pubblica_snapshot(conn, admin, snapshot, nota="copertura di riserva sintetica")
    soglia = proponi_parametro(conn, admin, codice="soglia_stabilita_quadrante", valore={"valore": 0.8},
                               descrizione="soglia di stabilità del quadrante", motivazione="dati di prova", org_id=None)
    approva_parametro(conn, admin, soglia, motivazione="dati di prova")
    esito = calcola_organizzazione(conn, admin, org, seme=20261017, estrazioni=500)
    print(f"ACME S.p.A.: {len(task_id)} task, {esito['occorrenze']} occorrenze, {esito['nuove']} risultati")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", type=int, default=8000)
    args = ap.parse_args()
    binari = cartella_binari()
    if binari is None:
        raise SystemExit("servono i binari di PostgreSQL con pgvector (NEARTECH_PG_BIN, vedi docs/sviluppo.md)")
    web = RADICE / "web" / "dist"
    if not (web / "index.html").is_file():
        raise SystemExit("frontend non compilato: eseguire prima 'npm run build' in web/")
    with postgres_temporaneo(binari) as url:
        _prepara(url)
        with psycopg.connect(url) as conn:
            popola(conn)
        impostazioni = Impostazioni(ambiente="sviluppo", chiave_sessione="", cartella_web=web, accesso_sviluppo=True)
        app = crea_app(impostazioni, connetti=lambda: psycopg.connect(url))
        print(f"Piattaforma su http://127.0.0.1:{args.porta} · entra con prova|comitato")
        uvicorn.run(app, host="127.0.0.1", port=args.porta, log_level="warning")


if __name__ == "__main__":
    main()
