"""Verifica e applica le migrazioni del database condiviso e degli spazi delle organizzazioni.

Uso:
  DATABASE_URL=... python scripts/migra.py                       # verifica, sola lettura
  DATABASE_URL=... python scripts/migra.py --inizializza 0002_... 0003_... 0004_... 0005_... 0006_...
  DATABASE_URL=... python scripts/migra.py --applica             # applica le mancanti, poi gli spazi

Connessione: NEARTECH_DATABASE_URL_PROPRIETARIO (ruolo proprietario) se impostata, altrimenti DATABASE_URL.

--inizializza crea il registro (0007) su un database migrato a mano prima del registro
e vi segna, senza eseguirle, le migrazioni indicate. Va usato una volta sola, dopo aver
verificato che i loro oggetti esistono. Su produzione, --inizializza e --applica
richiedono l'approvazione del responsabile del progetto.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.db import connect  # noqa: E402
from neartech.migrazioni import (  # noqa: E402
    CARTELLA_CONDIVISA,
    applica,
    da_applicare,
    inizializza_registro,
)
from neartech.organizzazioni import aggiorna_spazi  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    gruppo = parser.add_mutually_exclusive_group()
    gruppo.add_argument("--applica", action="store_true")
    gruppo.add_argument("--inizializza", nargs="+", metavar="NOME")
    args = parser.parse_args()

    # Le migrazioni girano con il ruolo proprietario (migrazione 0022): connessione separata da quella
    # dell'applicazione, se configurata.
    with connect(os.environ.get("NEARTECH_DATABASE_URL_PROPRIETARIO")) as conn:
        if args.inizializza:
            inizializza_registro(conn, args.inizializza)
            conn.commit()
            print(f"registro creato, migrazioni segnate come applicate: {len(args.inizializza) + 1}")
            return
        if args.applica:
            conn.autocommit = True
            for percorso in applica(conn, CARTELLA_CONDIVISA):
                print(f"applicata: {percorso.name}")
            with conn.transaction():
                for schema, nomi in aggiorna_spazi(conn).items():
                    for nome in nomi:
                        print(f"applicata in {schema}: {nome}")
            return
        conn.read_only = True
        mancanti = da_applicare(conn, CARTELLA_CONDIVISA)
        print("nessuna migrazione da applicare" if not mancanti else "da applicare:")
        for percorso in mancanti:
            print(f"  {percorso.name}")


if __name__ == "__main__":
    main()
