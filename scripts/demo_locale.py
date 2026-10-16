"""Dimostrazione locale delle fondazioni, con dati sintetici.

Uso:
  .venv/Scripts/python.exe scripts/demo_locale.py

Avvia un Postgres temporaneo (stessi binari dei test, vedi docs/sviluppo.md), applica schema
e migrazioni, percorre un flusso completo e distrugge tutto alla fine. Non usa DATABASE_URL
e non tocca il database di produzione. Il valore del parametro è un esempio, non una decisione.
"""

import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "src"))
sys.path.insert(0, str(RADICE / "tests"))

import psycopg  # noqa: E402

from neartech.governance import (  # noqa: E402
    approva_indirizzo,
    approva_parametro,
    indirizzi_vigenti,
    parametro_vigente,
    proponi_indirizzo,
    proponi_parametro,
    segnala,
)
from neartech.migrazioni import CARTELLA_CONDIVISA, applica  # noqa: E402
from neartech.organizzazioni import crea_organizzazione  # noqa: E402
from neartech.permessi import (  # noqa: E402
    PermessoNegato,
    assegna_ruolo,
    configura_log,
    crea_utente,
    inizializza_amministratore,
)
from neartech.registro import ancora_catena, verifica_catena  # noqa: E402
from neartech.stato_task import imposta_stato, stato_corrente  # noqa: E402
from pg_locale import cartella_binari, postgres_temporaneo  # noqa: E402


def titolo(testo: str) -> None:
    print(f"\n== {testo}")


def main() -> None:
    binari = cartella_binari()
    if binari is None:
        raise SystemExit("binari di Postgres non trovati: vedi docs/sviluppo.md")

    with postgres_temporaneo(binari) as dsn, psycopg.connect(dsn, autocommit=True) as conn, \
            psycopg.connect(dsn, autocommit=True) as conn_log:
        titolo("1. Database temporaneo: schema e migrazioni")
        conn.execute((RADICE / "db" / "schema.sql").read_text(encoding="utf-8"))
        applicate = applica(conn, CARTELLA_CONDIVISA)
        print(f"migrazioni applicate: {len(applicate)} ({applicate[0].name} ... {applicate[-1].name})")
        # Come farà l'API: il log di accesso su una connessione dedicata, così i rifiuti restano
        # anche quando la transazione dell'operazione rifiutata viene annullata.
        configura_log(conn_log)

        titolo("2. Amministratore tecnico iniziale e organizzazione")
        admin = inizializza_amministratore(conn, "sso|amministratore-demo")
        org = crea_organizzazione(conn, admin, nome="Organizzazione dimostrativa", codice="demo")
        print("creato lo spazio org_demo per il testo del cliente; il dataset condiviso resta in public")

        titolo("3. Ruoli dell'organizzazione")
        comitato = crea_utente(conn, "sso|comitato-demo")
        revisore = crea_utente(conn, "sso|revisore-demo")
        rappresentante = crea_utente(conn, "sso|rappresentante-demo")
        assegna_ruolo(conn, comitato, "comitato_guida", org, assegnata_da=admin)
        assegna_ruolo(conn, revisore, "revisore", org, assegnata_da=admin)
        assegna_ruolo(conn, rappresentante, "rappresentante_lavoratori", org, assegnata_da=admin)
        print("comitato guida, revisore e rappresentante dei lavoratori assegnati dall'amministratore")

        titolo("4. Un task del dataset e la sua occorrenza nello spazio dell'organizzazione")
        task = str(conn.execute(
            "INSERT INTO canonical_tasks (title_it, granularity) VALUES "
            "('Accogliere gli utenti e raccogliere le richieste', 2) RETURNING task_id"
        ).fetchone()[0])
        ruolo = conn.execute(
            "INSERT INTO org_demo.ruoli_organizzativi (nome) VALUES ('Addetto accoglienza') RETURNING ruolo_id"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO org_demo.occorrenze (task_id, ruolo_id, estratto) VALUES (%s, %s, 'estratto sintetico')",
            (task, ruolo),
        )
        print(f"stato iniziale del task: {stato_corrente(conn, task)}")

        titolo("5. Parametro di governance: proposta e approvazione del comitato")
        parametro = proponi_parametro(
            conn, comitato, codice="parametro_di_esempio", valore={"valore": 0.9},
            descrizione="valore dimostrativo, non una decisione", motivazione="esempio", org_id=org,
        )
        try:
            parametro_vigente(conn, "parametro_di_esempio", org)
        except LookupError as errore:
            print(f"prima dell'approvazione: {type(errore).__name__}")
        approva_parametro(conn, comitato, parametro, motivazione="approvato in seduta (esempio)")
        vigente = parametro_vigente(conn, "parametro_di_esempio", org)
        print(f"dopo l'approvazione: versione {vigente.versione}, valore {vigente.valore}, "
              f"atto di approvazione n. {vigente.approvazione_id}")

        titolo("6. Il revisore non può approvare parametri")
        try:
            approva_parametro(conn, revisore, parametro, motivazione="tentativo")
        except PermessoNegato as errore:
            print(f"rifiutato: {errore}")

        titolo("7. Indirizzo del comitato e segnalazione del revisore")
        indirizzo = proponi_indirizzo(
            conn, comitato, org_id=org, codice="relazione_diretta",
            testo="Tutelare la relazione diretta con gli utenti", ambito="Task di accoglienza",
            motivazione="valore dell'organizzazione (esempio)",
        )
        approva_indirizzo(conn, comitato, indirizzo, motivazione="approvato (esempio)")
        print(f"indirizzi vigenti: {[i.codice for i in indirizzi_vigenti(conn, org)]}")
        segnala(conn, revisore, org_id=org, tipo_oggetto="indirizzo", oggetto_id=indirizzo,
                motivazione="ricaduta da verificare su un solo task (esempio)")
        print("segnalazione registrata, visibile a comitato, auditor e rappresentanti")

        titolo("8. Il revisore valida il task")
        imposta_stato(conn, revisore, task, "validato", org_id=org, motivazione="rivisto (esempio)")
        print(f"stato del task: {stato_corrente(conn, task)}")

        titolo("9. Registro delle decisioni e verifica della catena")
        for posizione, atto, tipo in conn.execute(
            "SELECT posizione, atto, tipo_oggetto FROM registro_decisioni ORDER BY posizione"
        ):
            print(f"  {posizione:>2}  {atto:<13} {tipo}")
        ancora = ancora_catena(conn)
        print(f"catena integra: {verifica_catena(conn, ancora=ancora) is None}; "
              f"ancora da conservare fuori dal database: posizione {ancora[0]}, hash {ancora[1][:16]}...")

        titolo("10. Log di accesso")
        for esito, quante in conn.execute(
            "SELECT esito, count(*) FROM log_accessi GROUP BY esito ORDER BY esito"
        ):
            print(f"  {esito}: {quante}")
        configura_log(None)

    print("\nDatabase temporaneo distrutto.")


if __name__ == "__main__":
    main()
