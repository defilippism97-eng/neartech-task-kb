# Ambiente di sviluppo

## Python

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev,api]"
```

### Piattaforma web (fase 6)

API FastAPI in `src/neartech/api`, frontend React in `web/` (ADR 0007). Per provarla in locale con dati sintetici,
senza toccare il database di produzione:

```bash
cd web && npm ci && npm run build && cd ..
.venv/Scripts/python.exe scripts/prova_locale.py
```

Poi `http://localhost:8000`, accesso di sviluppo con `prova|comitato`. Per lavorare sul frontend con il ricaricamento
a caldo: lo script sopra in un terminale, `npm run dev` in `web/` in un altro (il server di Vite inoltra `/api` e
`/accesso` alla porta 8000). Test del frontend: `npm test`; tipi e controlli: `npx tsc -b`, `npx oxlint src`.

### Ambiente per l'embedding (bge-m3)

L'abbinamento al dataset (`scripts/abbina.py proponi`), il crosswalk (`scripts/esegui_crosswalk.py`) e gli embedding
delle tassonomie (`scripts/calcola_embedding.py`) calcolano gli embedding bge-m3 in locale con `sentence-transformers`,
che richiede `torch`. Per Python 3.15 `torch` non esiste ancora: serve un secondo ambiente con Python 3.13.

```bash
.venv/Scripts/python.exe -m pip install uv
.venv/Scripts/uv python install 3.13
.venv/Scripts/uv venv .venv-embedding --python 3.13
.venv/Scripts/uv pip install --python .venv-embedding/Scripts/python.exe -e ".[dev]" -r requirements-embedding.txt
```

- Versioni bloccate in `requirements-embedding.txt`; revisione del modello bloccata in
  `neartech.crosswalk.EMBEDDING_REVISION`. Alla prima esecuzione il modello si scarica da Hugging Face
  (circa 2,3 GB, nella cache dell'utente); poi funziona senza rete (`HF_HUB_OFFLINE=1`).
- Verificato il 2026-10-17: i vettori del nuovo ambiente coincidono con quelli dei task nel database (coseno
  1,000000 su 40 task, vicino corretto 40 su 40); tutta la suite passa anche in questo ambiente.
- Un cambio di modello, di revisione o di versione di `sentence-transformers` richiede di ricalcolare gli embedding
  dei task e di ripetere questa verifica: vettori diversi spostano le proposte di abbinamento.
- Su Windows senza modalità sviluppatore la cache di Hugging Face non usa i link simbolici: funziona, con un avviso.

## Database per i test

I test usano un database PostgreSQL 16 con pgvector, ripulito e ricreato a ogni sessione. Due modi:

1. **`NEARTECH_TEST_DSN`**: un database dedicato il cui nome contiene `test`. Mai il database di produzione.
2. **Postgres locale temporaneo** (predefinito se `NEARTECH_TEST_DSN` manca): i test avviano un cluster in una cartella temporanea, su `127.0.0.1` e porta libera, e lo distruggono a fine sessione (`tests/pg_locale.py`).

I binari per il punto 2 si prendono dal pacchetto `pgserver` 0.1.4, che contiene PostgreSQL 16.2 e pgvector 0.6.2 già compilati. Il pacchetto esiste solo per Python 3.12, ma i binari non dipendono da Python: basta estrarli.

```bash
.venv/Scripts/python.exe -m pip download pgserver==0.1.4 --no-deps --only-binary=:all: --platform win_amd64 --python-version 3.12 -d %TEMP%/pgserver
```

Verificare l'hash SHA-256 del file scaricato: `406e9355334e40754160a33d93f18a848720a38cd0b68da50be2ea272c89ed2d`. Poi estrarre la cartella `pgserver/pginstall/` del file `.whl` (è uno zip) in `%LOCALAPPDATA%/neartech/pgserver-0.1.4/`. In alternativa, impostare `NEARTECH_PG_BIN` con la cartella `bin` di un'altra installazione di PostgreSQL 16 con pgvector.

```bash
.venv/Scripts/python.exe -m pytest -q
```

Il cluster locale usa una password casuale (scram-sha-256) e ascolta solo su 127.0.0.1.
Con `NEARTECH_TEST_DSN` si accetta solo un database con `test` nel nome, su host locale;
per un host remoto serve `NEARTECH_TEST_DSN_REMOTO_CONSENTITO=1`.
