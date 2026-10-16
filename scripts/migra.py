"""Verifica e applica le migrazioni del database condiviso.

Uso:
  DATABASE_URL=... python scripts/migra.py                     # verifica, sola lettura
  DATABASE_URL=... python scripts/migra.py --applica           # applica le mancanti
  DATABASE_URL=... python scripts/migra.py --registra-esistenti 0002_... 0003_...

--registra-esistenti segna come applicate, senza eseguirle, le migrazioni applicate a
mano prima del registro (0007). Va usato solo dopo aver verificato che i loro oggetti
esistono. Su produzione, --applica e --registra-esistenti richiedono l'approvazione
del responsabile del progetto.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.db import connect  # noqa: E402
from neartech.migrazioni import (  # noqa: E402
    CARTELLA_CONDIVISA,
    applica,
    da_applicare,
    registra_senza_eseguire,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    gruppo = parser.add_mutually_exclusive_group()
    gruppo.add_argument("--applica", action="store_true")
    gruppo.add_argument("--registra-esistenti", nargs="+", metavar="NOME")
    args = parser.parse_args()

    with connect() as conn:
        if args.applica:
            for percorso in applica(conn, CARTELLA_CONDIVISA):
                print(f"applicata: {percorso.name}")
            conn.commit()
            return
        if args.registra_esistenti:
            percorsi = [CARTELLA_CONDIVISA / nome for nome in args.registra_esistenti]
            mancanti = [p.name for p in percorsi if not p.exists()]
            if mancanti:
                raise SystemExit(f"file non trovati: {', '.join(mancanti)}")
            registra_senza_eseguire(conn, percorsi)
            conn.commit()
            print(f"registrate senza eseguire: {len(percorsi)}")
            return
        conn.read_only = True
        mancanti = da_applicare(conn, CARTELLA_CONDIVISA)
        print("nessuna migrazione da applicare" if not mancanti else "da applicare:")
        for percorso in mancanti:
            print(f"  {percorso.name}")


if __name__ == "__main__":
    main()
