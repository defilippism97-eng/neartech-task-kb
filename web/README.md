# Frontend della piattaforma Neartech

React con TypeScript e Vite (ADR 0007). Viste per ruolo sopra l'API in `src/neartech/api`.

- `src/api/`: client dell'API e tipi del JSON, un modulo per area; `src/api/index.ts` li riunisce in `api`.
- `src/rotte/`, `src/viste/`: rotte e viste per ruolo, un file di rotte per area con le sue voci del guscio;
  applicazione sotto `/app`, sito pubblico (`src/sito/`) alla radice. Aree e corsie: `docs/piani/fase-6-cantiere.md`.
- `src/componenti/`: mappa dei quadranti, avanzamento della sperimentazione, guscio.
- `src/stile.css`: sistema di design dai token dell'identità v3.1.
- Testi: `docs/piattaforma/voce-e-testi.md`.

Comandi: `npm run dev` (con l'API su 127.0.0.1:8000), `npm test`, `npx tsc -b`, `npx oxlint src`, `npm run build`.
Prova completa in locale con dati sintetici: `docs/sviluppo.md`.
