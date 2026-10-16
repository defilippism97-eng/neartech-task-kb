"""Esegue il Canonicalizer: giudica i task vicini e fonde quelli equivalenti.

Uso (chiave da NEARTECH_ANTHROPIC_API_KEY):
  DATABASE_URL=... [NEARTECH_DB_VIA=https] python scripts/canonicalizza.py
Si può rilanciare: i task già esaminati non vengono giudicati di nuovo.
"""

import os
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.canonicalizer import canonicalizza  # noqa: E402
from neartech.db import connect  # noqa: E402


def main() -> None:
    api_key = os.environ.get("NEARTECH_ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("NEARTECH_ANTHROPIC_API_KEY non configurata")
    client = anthropic.Anthropic(api_key=api_key)
    with connect() as conn:
        esito = canonicalizza(conn, client)
    print(esito, flush=True)


if __name__ == "__main__":
    main()
