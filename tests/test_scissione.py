"""Separazione di una fusione del Canonicalizer giudicata sbagliata da un revisore.

La fusione originale non ha lasciato traccia: le occorrenze si ricostruiscono dalla scomposizione
approvata (ruolo, documento, titolo, testo originale), in public e nello spazio dell'organizzazione.
"""

import pytest

from neartech.canonicalizer import _gruppi_da_fondere, fondi
from neartech.permessi import PermessoNegato, assegna_ruolo, crea_utente, inizializza_amministratore
from neartech.scissione import piano_scissione, scindi
from neartech.spostamento import sposta_testo_cliente

TITOLO_A = "Fornire documentazione agli organi di controllo"
TITOLO_M = "Scansionare e trasmettere documenti"


@pytest.fixture
def fusione(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    org = str(conn.execute("INSERT INTO organizations (name) VALUES ('Org sintetica') RETURNING org_id").fetchone()[0])
    fonte = conn.execute(
        """INSERT INTO sources (kind, name, version, license, content_hash)
           VALUES ('org_document', 'mansionario.docx', '1', 'interno', 'h') RETURNING source_id"""
    ).fetchone()[0]
    ruoli = {nome: conn.execute(
        "INSERT INTO roles (org_id, name) VALUES (%s, %s) RETURNING role_id", (org, nome)
    ).fetchone()[0] for nome in ("RUOLO UNO", "RUOLO DUE", "RUOLO TRE")}
    a = conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2) RETURNING task_id",
                     (TITOLO_A,)).fetchone()[0]
    m = conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2) RETURNING task_id",
                     (TITOLO_M,)).fetchone()[0]
    occorrenze = [(a, "RUOLO UNO", "fornisce documenti"), (a, "RUOLO DUE", "fornisce documentazione"),
                  (m, "RUOLO UNO", "scansiona i documenti"), (m, "RUOLO TRE", "trasmette i documenti")]
    for task, ruolo, testo in occorrenze:
        conn.execute(
            """INSERT INTO task_occurrences (task_id, role_id, raw_snippet, source_id, model_name, prompt_hash)
               VALUES (%s, %s, %s, %s, 'modello', 'hash')""",
            (task, ruoli[ruolo], testo, fonte),
        )
    proposta = conn.execute(
        """INSERT INTO fusioni_proposte (task_id, altro_task_id, decisione, motivazione, model_name, prompt_hash)
           VALUES (%s, %s, 'stessa_attivita', 'm', 'modello', 'hash') RETURNING proposal_id""",
        (m, a),
    ).fetchone()[0]
    assert fondi(conn, [str(a), str(m)]) == str(a)  # M ha meno occorrenze: viene fuso in A
    sposta_testo_cliente(conn, admin, org, codice="sintetica")  # come in produzione: copia dopo le fusioni
    scomposizione = [
        {"ruolo": ruolo, "documento": "mansionario.docx", "titolo": TITOLO_A if t == a else TITOLO_M,
         "testo_originale": testo, "nota_contesto": None}
        for t, ruolo, testo in occorrenze
    ]
    return {"admin": admin, "org": org, "a": str(a), "m": str(m), "scomposizione": scomposizione,
            "proposta": str(proposta)}


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
    attese_a = ["fornisce documentazione", "fornisce documenti"]
    assert _occorrenze(conn, "task_occurrences", "raw_snippet", fusione["m"]) == attese_m
    assert _occorrenze(conn, "org_sintetica.occorrenze", "estratto", fusione["m"]) == attese_m
    assert _occorrenze(conn, "task_occurrences", "raw_snippet", fusione["a"]) == attese_a
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
