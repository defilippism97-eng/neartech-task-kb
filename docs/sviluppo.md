# Ambiente di sviluppo

## Python

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

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
