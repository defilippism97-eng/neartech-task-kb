# Neartech — Knowledge base dei task

Knowledge base che descrive il lavoro attività per attività (i "task") e per ciascuno misura:

- **N**, necessità dell'apporto umano: quanto serve ancora una persona, per limiti tecnici, oggi.
- **D**, desiderabilità dell'apporto umano: quanto vale che a farlo sia una persona, per ragioni etiche, relazionali, di fiducia e di senso del lavoro.

Incrociando N e D ogni task cade in uno di quattro quadranti (Q1 Baluardo umano, Q2 Collo di bottiglia transitorio, Q3 Scelta di valore, Q4 Automazione pura).

## Documentazione

- [`docs/piano-sviluppo-v2.md`](docs/piano-sviluppo-v2.md): piano di sviluppo V2 completo (metodo, fonti, architettura, validazione, roadmap, rischi).
- [`db/schema.sql`](db/schema.sql): schema PostgreSQL 16 + pgvector della fase F0, con la vista `v_role_metrics`.

## Stato

Fase F0 (Fondazioni), in corso:

- schema PostgreSQL 16 + pgvector applicato e verificato;
- caricatore delle tassonomie da CSV (idempotente, con controllo dell'hash per versione);
- inserimento di evidenze collegate a un nodo di tassonomia, con validazione della scala 0–4;
- test delle tre verifiche di F0 del piano, su dati sintetici.

Da fare in F0: caricatori dei dati reali (O*NET, ESCO, Atlante INAPP), collegamenti con il Crosswalk Mapper (richiede il modello linguistico), Canonicalizer e Scorer, job di calcolo di N e D. Questi componenti richiedono le credenziali del fornitore del modello e non sono ancora implementati.

## Sviluppo

Requisiti: Python 3.12, PostgreSQL 16 con l'estensione `vector`.

```bash
uv venv -p 3.12 .venv
uv pip install -p .venv -e ".[dev]"

# database di test (il nome deve contenere "test": lo schema viene ricreato a ogni run)
createdb neartech_test
psql neartech_test -c "CREATE EXTENSION vector;"
NEARTECH_TEST_DSN="postgresql://localhost/neartech_test" .venv/bin/pytest
```
