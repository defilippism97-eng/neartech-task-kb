# Neartech — Knowledge base dei task

Knowledge base che descrive il lavoro attività per attività (i "task") e per ciascuno misura:

- **N**, necessità dell'apporto umano: quanto serve ancora una persona, per limiti tecnici, oggi.
- **D**, desiderabilità dell'apporto umano: quanto vale che a farlo sia una persona, per ragioni etiche, relazionali, di fiducia e di senso del lavoro.

Incrociando N e D ogni task cade in uno di quattro quadranti (Q1 Baluardo umano, Q2 Collo di bottiglia transitorio, Q3 Scelta di valore, Q4 Automazione pura).

## Documentazione

- [`docs/piano-sviluppo-v2.md`](docs/piano-sviluppo-v2.md): piano di sviluppo V2 completo (metodo, fonti, architettura, validazione, roadmap, rischi).
- [`db/schema.sql`](db/schema.sql): schema PostgreSQL 16 + pgvector della fase F0, con la vista `v_role_metrics`.

## Stato

Fase F0 (Fondazioni) in avvio. Lo schema è applicato e verificato su PostgreSQL 16 con pgvector; caricatori delle tassonomie, pipeline di calcolo e test di F0 sono da realizzare.

## Sviluppo

```bash
createdb neartech_dev
psql neartech_dev -f db/schema.sql
```

Requisiti: PostgreSQL 16 con l'estensione `vector`.
