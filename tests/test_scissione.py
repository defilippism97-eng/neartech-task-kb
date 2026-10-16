"""Separazione di una fusione del Canonicalizer giudicata sbagliata da un revisore.

La fusione originale non ha lasciato traccia: le occorrenze si ricostruiscono dalla scomposizione
approvata (ruolo, documento, titolo, testo originale), in public e nello spazio dell'organizzazione.
"""

import pytest

from neartech.canonicalizer import _gruppi_da_fondere, fondi
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore
from neartech.scissione import piano_scissione, scindi
from neartech.occorrenze import documento, registra_occorrenza, ruolo
from neartech.organizzazioni import crea_organizzazione

TITOLO_A = "Fornire documentazione agli organi di controllo"
TITOLO_M = "Scansionare e trasmettere documenti"


@pytest.fixture
def fusione(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    org = crea_organizzazione(conn, admin, nome="Org sintetica", codice="sintetica")
    fonte = documento(conn, org, nome_file="mansionario.docx", sha256="h", licenza="interno")
    ruoli = {nome: ruolo(conn, org, nome) for nome in ("RUOLO UNO", "RUOLO DUE", "RUOLO TRE", "RUOLO QUATTRO")}
    a = str(conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2) RETURNING task_id",
                         (TITOLO_A,)).fetchone()[0])
    m = str(conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2) RETURNING task_id",
                         (TITOLO_M,)).fetchone()[0])
    occorrenze = [(a, "RUOLO UNO", "fornisce documenti"), (a, "RUOLO DUE", "fornisce documentazione"),
                  (a, "RUOLO QUATTRO", "consegna documenti"),
                  (m, "RUOLO UNO", "scansiona i documenti"), (m, "RUOLO TRE", "trasmette i documenti")]
    for task, nome_ruolo, testo in occorrenze:
        registra_occorrenza(conn, org, task_id=task, ruolo_id=ruoli[nome_ruolo], documento_id=fonte, estratto=testo,
                            nota_contesto=None, model_name="modello", prompt_hash="hash")
    proposta = conn.execute(
        """INSERT INTO fusioni_proposte (task_id, altro_task_id, decisione, motivazione, model_name, prompt_hash)
           VALUES (%s, %s, 'stessa_attivita', 'm', 'modello', 'hash') RETURNING proposal_id""",
        (m, a),
    ).fetchone()[0]
    assert fondi(conn, [a, m]) == a  # M ha meno occorrenze: viene fuso in A
    scomposizione = [
        {"ruolo": nome_ruolo, "documento": "mansionario.docx", "titolo": TITOLO_A if t == a else TITOLO_M,
         "testo_originale": testo, "nota_contesto": None}
        for t, nome_ruolo, testo in occorrenze
    ]
    return {"admin": admin, "org": org, "a": a, "m": m, "scomposizione": scomposizione, "proposta": str(proposta)}


def _occorrenze(conn, schema_tabella, colonna_testo, task):
    return sorted(r[0] for r in conn.execute(
        f"SELECT {colonna_testo} FROM {schema_tabella} WHERE task_id = %s", (task,)
    ).fetchall())


def test_piano_distingue_occorrenze_da_spostare_e_da_ricreare(conn, fusione):
    piano = piano_scissione(conn, fusione["m"], fusione["scomposizione"], fusione["org"])
    assert piano["superstite"] == fusione["a"]
    assert len(piano["da_spostare"]) == 1  # RUOLO TRE, spostata sul superstite dalla fusione
    assert [v["ruolo"] for v in piano["da_ricreare"]] == ["RUOLO UNO"]  # cancellata perché doppia


def test_scissione_ricostruisce_il_task(conn, fusione):
    esito = scindi(conn, fusione["admin"], task_id=fusione["m"], scomposizione=fusione["scomposizione"],
                   org_id=fusione["org"], motivazione="giudicata errata dal revisore")
    assert esito == {"spostate": 1, "ricreate": 1}
    assert conn.execute("SELECT status, merged_into FROM canonical_tasks WHERE task_id = %s",
                        (fusione["m"],)).fetchone() == ("active", None)
    attese_m = ["scansiona i documenti", "trasmette i documenti"]
    attese_a = ["consegna documenti", "fornisce documentazione", "fornisce documenti"]
    assert conn.execute("SELECT count(*) FROM task_occurrences WHERE task_id = %s", (fusione["m"],)).fetchone()[0] == 2
    assert _occorrenze(conn, "org_sintetica.occorrenze", "estratto", fusione["m"]) == attese_m
    assert conn.execute("SELECT count(*) FROM task_occurrences WHERE task_id = %s", (fusione["a"],)).fetchone()[0] == 3
    assert _occorrenze(conn, "org_sintetica.occorrenze", "estratto", fusione["a"]) == attese_a
    atto = conn.execute(
        "SELECT atto, dettagli ->> 'superstite' FROM registro_decisioni WHERE tipo_oggetto = 'task_canonico'"
    ).fetchone()
    assert atto == ("correzione", fusione["a"])


def test_solo_chi_gestisce_il_dataset_centrale_separa(conn, fusione):
    revisore = crea_utente(conn, "sso|revisore")
    assegna_ruolo(conn, revisore, "revisore", fusione["org"], assegnata_da=fusione["admin"])
    with pytest.raises(PermessoNegato):
        scindi(conn, revisore, task_id=fusione["m"], scomposizione=fusione["scomposizione"],
               org_id=fusione["org"], motivazione="x")


def test_un_task_non_fuso_non_si_separa(conn, fusione):
    with pytest.raises(ValueError):
        piano_scissione(conn, fusione["a"], fusione["scomposizione"], fusione["org"])


def test_il_canonicalizer_non_rifonde_un_task_separato(conn, fusione):
    scindi(conn, fusione["admin"], task_id=fusione["m"], scomposizione=fusione["scomposizione"],
           org_id=fusione["org"], motivazione="giudicata errata dal revisore")
    assert _gruppi_da_fondere(conn) == []
