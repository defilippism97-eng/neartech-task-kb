"""Ambiente di prova locale della piattaforma (fase 6), con dati sintetici.

Avvia un PostgreSQL temporaneo (tests/pg_locale.py), applica schema e migrazioni, crea un'organizzazione
immaginaria ("ACME S.p.A.", ruoli di staff) con ruoli, task, giudizi, snapshot di riserva e calcolo, poi avvia la
piattaforma su http://127.0.0.1:8000 con l'accesso di sviluppo. Alla chiusura il database viene distrutto.

Non usa mai DATABASE_URL: nessun contatto con il database di produzione.

Uso:
  (cd web && npm run build)
  python scripts/prova_locale.py [--porta 8000]
Soggetti di prova: prova|comitato (comitato guida), prova|auditor, prova|revisore, prova|admin.
"""

import argparse
import io
import json
import sys
import tempfile
import threading
import time
import zipfile
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from xml.sax.saxutils import escape

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "src"))
sys.path.insert(0, str(RADICE / "tests"))

import psycopg  # noqa: E402
import uvicorn  # noqa: E402
from pg_locale import cartella_binari, postgres_temporaneo  # noqa: E402

from neartech.api.app import crea_app  # noqa: E402
from neartech.coda import completa, fallisci, prendi  # noqa: E402
from neartech.pipeline import gestori  # noqa: E402
from neartech.api.config import Impostazioni  # noqa: E402
from neartech.migrazioni import CARTELLA_CONDIVISA, applica  # noqa: E402
# Dati sintetici: scripts/prova/, il seme di base (ACME S.p.A.) e un seme per ogni corsia del cantiere
# (docs/piani/fase-6-cantiere.md), eseguiti in ordine con un contesto condiviso.
from prova import incorpora_prova, popola  # noqa: E402

MANSIONARI = {
    "mansionario-tesoreria.docx": ["TITOLO DELLA POSIZIONE", "Addetto tesoreria", "PRINCIPALI ATTIVITÀ",
                                   "Riconciliazioni bancarie giornaliere", "Gestione dei solleciti ai clienti",
                                   "Previsione dei flussi di cassa settimanali"],
    "mansionario-ufficio-gare.docx": ["TITOLO DELLA POSIZIONE", "Specialista gare e appalti", "PRINCIPALI ATTIVITÀ",
                                      "Qualifica dei nuovi fornitori", "Preparazione della documentazione di gara",
                                      "Negoziazione con i fornitori"],
}


def docx(righe: list[str]) -> bytes:
    """Un .docx minimo: un paragrafo per riga."""
    corpo = "".join(f"<w:p><w:r><w:t>{escape(r)}</w:t></w:r></w:p>" for r in righe)
    xml = ('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/'
           f'wordprocessingml/2006/main"><w:body>{corpo}</w:body></w:document>')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("word/document.xml", xml)
    return buffer.getvalue()


class ModelloProva:
    """Al posto del modello a pagamento: ogni riga dopo «PRINCIPALI ATTIVITÀ» è un'attività, citata alla lettera."""

    def __init__(self):
        self.messages = self

    def create(self, *, messages, **_):
        testo = messages[0]["content"].split("<documento>", 1)[1].split("</documento>", 1)[0]
        righe = [r.strip() for r in testo.splitlines() if r.strip()]
        inizio = next((i + 1 for i, r in enumerate(righe) if r.upper() == "PRINCIPALI ATTIVITÀ"), len(righe))
        attivita = [{"titolo": r[:200], "granularita": 2, "testo_originale": r, "nota_contesto": None}
                    for r in righe[inizio:] if len(r) >= 5]
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=json.dumps({"attivita": attivita}))])


def lavoratore_prova(url: str) -> None:
    """Lavoratore della coda nel processo di prova, con modello ed embedding finti."""
    gestori_prova = gestori(client=ModelloProva(), incorpora=incorpora_prova)
    with psycopg.connect(url, autocommit=True) as conn:
        while True:
            with conn.transaction():
                job = prendi(conn, "prova", tipi=list(gestori_prova))
            if job is None:
                time.sleep(2)
                continue
            time.sleep(1.5)  # per vedere lo stato «in lavorazione»
            try:
                with conn.transaction():
                    gestori_prova[job.tipo](conn, job.payload)
                    completa(conn, job.job_id, "prova")
            except Exception as errore:  # noqa: BLE001 - come scripts/worker.py
                with conn.transaction():
                    fallisci(conn, job.job_id, "prova", f"{type(errore).__name__}: {errore}"[:300],
                             riprova_tra=timedelta(minutes=5))


def _prepara(url: str) -> None:
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute((RADICE / "db" / "schema.sql").read_text(encoding="utf-8"))
        applica(conn, CARTELLA_CONDIVISA)


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
        threading.Thread(target=lavoratore_prova, args=(url,), daemon=True).start()
        cartella = Path(tempfile.mkdtemp(prefix="mansionari-prova-"))
        for nome, righe in MANSIONARI.items():
            (cartella / nome).write_bytes(docx(righe))
        print(f"Mansionari di prova da caricare: {cartella}")
        print(f"Piattaforma su http://127.0.0.1:{args.porta} · entra con prova|comitato")
        uvicorn.run(app, host="127.0.0.1", port=args.porta, log_level="warning")


if __name__ == "__main__":
    main()
