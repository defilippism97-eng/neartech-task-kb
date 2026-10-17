# ADR-0007: Stack della piattaforma web (fase 6)

**Data:** 2026-10-17
**Stato:** accettato (responsabile del progetto, 2026-10-17)
**Chi decide:** responsabile del progetto

## Contesto

Il motore (fasi 1–5) è una libreria Python su PostgreSQL con permessi, registro append-only e testi dell'organizzazione nel suo schema. La piattaforma deve portarlo davanti a sette ruoli con viste e azioni diverse, avere una presentazione curata per conquistare le aziende pilota, funzionare da telefono per i questionari, e non duplicare nessuna regola del motore. Il team è piccolo: ogni componente in più è un costo di esercizio.

## Decisione

1. **API:** FastAPI nello stesso pacchetto `neartech` (`neartech.api`), che chiama le funzioni esistenti e non scrive SQL di dominio proprio. Una connessione e una transazione per richiesta; il log di accesso su una connessione dedicata come negli script. Le regole (permessi, soglie, registro) restano nel motore e nel database.
2. **Frontend:** React con TypeScript, costruito con Vite, servito come file statici; TanStack Query per i dati, TanStack Router per le viste per ruolo; grafici in SVG con D3 per la mappa dei quadranti (serve controllo fine su incertezza e probabilità, che le librerie di grafici pronte non danno). Il sistema di design nasce dai token di `docs/identita/neartech-identita.css`.
3. **Pagina pubblica:** pagine statiche generate dallo stesso progetto Vite (prerender), senza un secondo server.
4. **Accesso:** SSO aziendale con OpenID Connect (Microsoft Entra ID e Google Workspace), gestito dall'API; sessione in cookie `HttpOnly`, `Secure`, `SameSite=Lax`; il soggetto SSO corrisponde a `utenti.soggetto_sso`. I questionari non richiedono un account: inviti con token monouso, senza anagrafica.
5. **Ospitalità:** un contenitore per l'API con i file statici, in UE. Proposta: **Azure Container Apps, regione West Europe**, vicino all'ecosistema Microsoft dei clienti e a Entra ID. Database: Neon (già in UE).
6. **Ambiente di prova:** ramo Neon separato (copia della struttura, dati sintetici) e un secondo contenitore; la produzione si aggiorna solo da `main`.
7. **CI:** GitHub Actions a ogni PR: test Python con PostgreSQL 16 e pgvector, controlli e test del frontend, build, end to end con Playwright, controllo di accessibilità.

## Alternative considerate

### Next.js
- **Pro:** rendering lato server, pagine pubbliche e applicazione in un solo framework.
- **Contro:** un secondo server Node accanto all'API Python, con un secondo luogo dove mettere logica e permessi.
- **Perché no:** l'applicazione è tutta dietro accesso e non ha bisogno di rendering lato server; il prerender di Vite basta per la pagina pubblica.

### Pagine generate dal server (Jinja con HTMX)
- **Pro:** un solo linguaggio, pochissimo JavaScript, molto semplice da mantenere.
- **Contro:** mappa dei quadranti interattiva, filtri incrociati e animazioni curate diventano faticosi; meno strumenti per un'interfaccia di livello marketing.
- **Perché no:** la qualità dell'esperienza è il requisito principale di questa fase.

### Ospitalità su Fly.io o Scaleway
- **Pro:** più semplici e più economici di Azure; Scaleway è un fornitore europeo.
- **Contro:** meno vicini a Entra ID e alle richieste di conformità dei clienti medio-grandi.
- **Perché no:** proposta, non vincolo: il contenitore è lo stesso e si sposta senza riscrivere nulla.

## Conseguenze

### Positive
- Nessuna regola duplicata: l'API è un sottile strato sopra il motore già testato.
- Un solo linguaggio lato server, un solo artefatto da distribuire.
- Il frontend può raggiungere la qualità grafica richiesta, con test end to end sui percorsi di ogni ruolo.

### Negative
- Due ecosistemi da mantenere (Python e TypeScript).
- Il prerender della pagina pubblica è più limitato di un sito costruito con un CMS: i testi si cambiano nel codice.

### Rischi
- **Permessi aggirati dal frontend:** ogni controllo resta nell'API e nel motore (`richiedi`); il frontend nasconde solo ciò che l'utente non può fare. Test di permesso negato per ogni endpoint.
- **Testi dell'organizzazione in cache del browser o nei log:** risposte con `Cache-Control: no-store`, log senza contenuti.
- **Anonimato dei questionari:** token monouso, nessun legame con l'utente, aggregazione con il minimo di rispondenti approvato.
