"""Copertura di riserva proposta dal modello per i task del dataset (fase 4; metodo, sezione 17).

Uso (DATABASE_URL dall'ambiente; chiave del modello da NEARTECH_ANTHROPIC_API_KEY):
  python scripts/copertura_riserva.py --utente-sso S --data 2026-10-17 --stima
  python scripts/copertura_riserva.py --utente-sso S --data 2026-10-17 --limite-uscita 120000

--stima: solo lettura, nessuna chiamata; conta i task da valutare e stima i token in ingresso.
Senza --stima chiama l'API (costo da approvare prima) e salva le evidenze di riserva; si ferma al limite.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neartech.copertura_riserva import (  # noqa: E402
    MAX_ATTEMPTS,
    MAX_TOKENS,
    SYSTEM_PROMPT,
    _messaggio,
    valuta_task_senza_copertura,
)
from neartech.db import connect  # noqa: E402
from neartech.permessi import configura_log  # noqa: E402

CARATTERI_PER_TOKEN = 3.0  # prudente per l'italiano


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--utente-sso", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--stima", action="store_true")
    ap.add_argument("--limite-uscita", type=int)
    args = ap.parse_args()
    with connect() as conn:
        if args.stima:
            conn.read_only = True
            titoli = [r[0] for r in conn.execute(
                "SELECT title_it FROM canonical_tasks WHERE status = 'active' AND granularity IN (1, 2)")]
            caratteri = sum(len(SYSTEM_PROMPT) + len(_messaggio(t)) for t in titoli)
            print(f"task attivi: {len(titoli)}; token stimati in ingresso: {caratteri / CARATTERI_PER_TOKEN:.0f}; "
                  f"in uscita al massimo {len(titoli) * MAX_ATTEMPTS * MAX_TOKENS} (limite di risposta per tentativo)")
            return
        api_key = os.environ.get("NEARTECH_ANTHROPIC_API_KEY")
        if not api_key:
            raise SystemExit("NEARTECH_ANTHROPIC_API_KEY non configurata")
        import anthropic

        with connect() as conn_log:
            conn_log.autocommit = True
            configura_log(conn_log)
            try:
                conn.autocommit = True  # ogni task valutato si conferma da sé
                riga = conn.execute("SELECT utente_id FROM utenti WHERE soggetto_sso = %s",
                                    (args.utente_sso,)).fetchone()
                if riga is None:
                    raise SystemExit("utente sconosciuto")
                esito = valuta_task_senza_copertura(conn, anthropic.Anthropic(api_key=api_key), str(riga[0]),
                                                    data=args.data, limite_uscita=args.limite_uscita)
                print(esito)
            except (LookupError, ValueError, PermissionError) as errore:
                raise SystemExit(f"errore ({type(errore).__name__}): {errore}") from None
            finally:
                configura_log(None)


if __name__ == "__main__":
    main()
