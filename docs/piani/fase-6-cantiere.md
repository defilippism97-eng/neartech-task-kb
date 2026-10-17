# Fase 6: cantiere per aree

**Stato:** struttura pronta il 2026-10-17 (branch `fase-6-struttura`). Piano di riferimento: `docs/piano-sviluppo-v2.md`; piano della fase: `docs/piani/fase-6-piattaforma.md`.

## Perché

Il resto della fase 6 procede su **otto corsie in parallelo**. Perché lavorino senza modificare gli stessi file, il codice condiviso è stato diviso per area prima di cominciare: ogni corsia ha i propri file in ogni strato (API, test, client, rotte, semi di prova, viste) e i file che li riuniscono elencano già tutte le corsie. La ristrutturazione non cambia comportamento né indirizzi dell'API; l'unico cambiamento visibile è che **l'applicazione autenticata sta sotto `/app`** e la radice appartiene al sito pubblico. I vecchi indirizzi `/org/$codice/<vista>` (segnalibri, collegamenti già condivisi) portano alla stessa pagina sotto `/app`.

## Come è fatta la struttura

| Strato | Dove | Come si aggiunge un'area |
|---|---|---|
| Rotte dell'API | `src/neartech/api/rotte/<area>.py`, un `router = APIRouter(prefix="/api")` per modulo | `rotte/__init__.py` elenca tutti i router in `ROUTERS`, in ordine fisso; `app.py` li include tutti. Aiuti condivisi in `rotte/comune.py` (`organizzazione_consentita`, `Motivazione`) |
| Test dell'API | `tests/api/test_api_<area>.py` | fixture `client` in `tests/api/conftest.py`; aiuti (`SCRIVE`, `_entra`, `_impostazioni`, `_Connessione`) in `tests/api/supporto_api.py` |
| Client | `web/src/api/<area>.ts`, che esporta `export const <area> = { ... }` e i propri tipi | `api/index.ts` riunisce tutti i moduli in `api` e ne riesporta i tipi; `api/client.ts` ha `richiesta`, `org`, `ErroreApi`; `api/tipi.ts` i tipi usati da più aree |
| Rotte e navigazione | `web/src/rotte/<area>.tsx`, che esporta `rotte(genitori)` e `voci: VoceNav[]` | `rotte/index.tsx` chiama tutte le aree e appende ogni rotta al suo genitore (`pubblico` o `app`); le voci arrivano al guscio dal contesto del router |
| Semi di prova | `scripts/prova/<corsia>.py`, con `semina(conn, ctx)` | `scripts/prova/__init__.py` li esegue in ordine (`SEMI`) con un `Contesto` condiviso (`scripts/prova/comune.py`) |
| Viste | `web/src/viste/<corsia>/` (il sito: `web/src/sito/`) | le importa solo il file di rotte della corsia; la cartella non esiste ancora (git non conserva cartelle vuote), la crea la corsia con il suo primo componente |

Percorsi del frontend:

- **`/app`**: verifica dell'accesso (`viste/Radice.tsx`) e home dell'utente; **`/app/org/$codice/<vista>`**: le pagine di un'organizzazione. Le rotte vanno appese al genitore `app` con percorso `org/$codice/<vista>`.
- **`/` e gli altri percorsi pubblici**: sito pubblico, senza accesso; genitore `pubblico` (layout `web/src/sito/Layout.tsx`, home segnaposto `web/src/sito/Home.tsx`). Qui stanno anche le pagine per chi risponde ai questionari d3/d4.
- **`/org/...`** è riservato: porta i vecchi indirizzi dell'applicazione (prima del cantiere `/org/$codice/<vista>`) alla stessa pagina sotto `/app`, con la stessa ricerca e lo stesso frammento (`web/src/rotte/base.tsx`). Nessuna corsia usa questo prefisso.
- Il server restituisce `index.html` per ogni percorso fuori da `/api`, `/accesso` e `/assets`; dopo l'accesso SSO, e quando l'accesso non riesce (`/app?accesso=non-riuscito`), si torna a `/app`. L'uscita e l'accesso di sviluppo riportano a `/app` dal frontend.

**Rotte annidate.** `rotte(genitori)` restituisce solo le rotte di primo livello, figlie di `pubblico` o di `app`. Le figlie di una rotta della corsia (schede, dettagli, un layout `org/$codice/<vista>` con le sue sottopagine) si appendono a quella con `addChildren`, e `rotte()` restituisce solo il genitore così composto, che porta con sé figli e tipi. Una figlia restituita accanto al suo genitore ferma l'applicazione all'avvio con l'errore «rotte senza un genitore noto»: è voluto, perché altrimenti resterebbe fuori dall'albero senza avvisi (controllo in `fuoriDalPrimoLivello`, provato da `web/src/test/rotte.test.tsx`).

Navigazione: ogni voce è `{ to, etichetta, icona, ruoli, gruppo? }`. Il guscio mostra le voci il cui `ruoli` contiene il ruolo corrente, raggruppate per `gruppo` (predefinito `Lavoro`) nell'ordine delle aree. `to` è il percorso completo di una rotta registrata (es. `/app/org/$codice/lotti`), controllato da tsc; `TUTTI_I_RUOLI` vale per le voci che vede chiunque. Il gruppo "In arrivo" non esiste più: una voce compare quando la sua rotta c'è. Il ruolo corrente lo passa al guscio la vista (prop `ruolo`): Panoramica e Indirizzi usano il ruolo dell'utente nell'organizzazione, Documenti, Lotti e Revisione il solo ruolo che la pagina ammette (come prima del cantiere). Un ruolo vuoto o sconosciuto non vede voci; in pratica non capita, perché l'API ha già rifiutato la pagina.

## Le corsie

Ogni corsia possiede i file della sua riga. Le migrazioni riservate sono numeri già assegnati: la corsia li usa per le sue migrazioni (`db/migrations/<numero>_<descrizione>.sql`, spazio organizzazione in `db/migrations_org/`).

| Corsia | Ambito | API | Client | Rotte | Seme | Test dell'API | Viste | Migrazioni riservate |
|---|---|---|---|---|---|---|---|---|
| **amministrazione** | account, credenziali, utenti, ruoli, organizzazioni, console di amministrazione | `src/neartech/api/rotte/amministrazione.py` | `web/src/api/amministrazione.ts` | `web/src/rotte/amministrazione.tsx` | `scripts/prova/amministrazione.py` | `tests/api/test_api_amministrazione.py` | `web/src/viste/amministrazione/` | public 0038 |
| **conoscenza** | base di conoscenza | `.../rotte/conoscenza.py` | `web/src/api/conoscenza.ts` | `web/src/rotte/conoscenza.tsx` | `scripts/prova/conoscenza.py` | `tests/api/test_api_conoscenza.py` | `web/src/viste/conoscenza/` | public 0039 |
| **flusso** | lavori di ricalcolo, fase di verifica, storico e stampa delle restituzioni, reversibilità della pipeline dei documenti | `.../rotte/flusso.py` | `web/src/api/flusso.ts` | `web/src/rotte/flusso.tsx` | `scripts/prova/flusso.py` | `tests/api/test_api_flusso.py` | `web/src/viste/flusso/` | public 0040 |
| **revisione_lavoro** | lavoro del revisore: giudizi sulla rubrica, lotti, coda unificata, somiglianze, ritaratura | `.../rotte/revisione_lavoro.py` | `web/src/api/revisione_lavoro.ts` | `web/src/rotte/revisione_lavoro.tsx` | `scripts/prova/revisione_lavoro.py` | `tests/api/test_api_revisione_lavoro.py` | `web/src/viste/revisione_lavoro/` | public 0041, org 0011 |
| **questionari** | questionari d3/d4, pagine e rotte pubbliche per chi risponde | `.../rotte/questionari.py` | `web/src/api/questionari.ts` | `web/src/rotte/questionari.tsx` | `scripts/prova/questionari.py` | `tests/api/test_api_questionari.py` | `web/src/viste/questionari/` | public 0042, org 0012 |
| **ascolto** | ascolto del comitato: materiali, interviste, schede di scenario, stima dei pesi | `.../rotte/ascolto.py` | `web/src/api/ascolto.ts` | `web/src/rotte/ascolto.tsx` | `scripts/prova/ascolto.py` | `tests/api/test_api_ascolto.py` | `web/src/viste/ascolto/` | public 0043, org 0013 |
| **governo** | parametri, completamento degli indirizzi, home dell'auditor, registro, vista del rappresentante | `.../rotte/governo.py` | `web/src/api/governo.ts` | `web/src/rotte/governo.tsx` | `scripts/prova/governo.py` | `tests/api/test_api_governo.py` | `web/src/viste/governo/` | public 0044, org 0014 |
| **sito** | sito pubblico e candidature ai piloti | `.../rotte/sito.py` | `web/src/api/sito.ts` | `web/src/rotte/sito.tsx` | `scripts/prova/sito.py` | `tests/api/test_api_sito.py` | `web/src/sito/` | public 0045 |

Oltre alla riga, ogni corsia possiede i file nuovi che crea: moduli del motore (`src/neartech/<nome>.py`), test del motore (`tests/test_<nome>.py`), test del frontend (`web/src/test/<corsia>.test.tsx`), documenti in `docs/`. Le aree già costruite (`base`, `panoramica`, `indirizzi`, `revisione`, `documenti`, `lotti`) restano condivise: chi deve cambiarle lo fa con modifiche piccole e motivate, come per ogni file condiviso.

## Regole

1. **Una corsia modifica solo i propri file.** Se un file condiviso va toccato per forza (per esempio `src/neartech/api/rotte/comune.py`, `tests/api/conftest.py`, `tests/api/supporto_api.py`, `web/src/api/tipi.ts`, `web/src/rotte/tipi.ts`, `web/src/componenti/Icona.tsx`, `web/src/stile.css`, `web/src/azioni.ts`, un modulo del motore esistente), si **aggiunge in fondo, in un blocco separato** aperto da un commento con il nome della corsia, senza riordinare né riformattare il resto. Gli elenchi che riuniscono le aree (`rotte/__init__.py`, `api/index.ts`, `rotte/index.tsx`, `scripts/prova/__init__.py`) non si toccano.
2. **Nomi unici fra le corsie.** Le funzioni del client confluiscono tutte in `api`: un nome doppio fa fallire `web/src/test/rotte.test.tsx`; un tipo doppio fa fallire tsc. I percorsi dell'API e del frontend di una corsia hanno il prefisso della sua area.
3. **Permessi nuovi solo con la propria migrazione**, nel numero riservato. Lo stesso per tabelle e colonne: mai modificare `db/schema.sql` né una migrazione già esistente.
4. **Migrazioni in ordine.** Il registro rifiuta una migrazione con un numero più basso di una già applicata (`MigrazioneFuoriOrdine`). In un database condiviso (produzione) le migrazioni delle corsie si applicano solo dopo l'unione, in ordine di numero; una corsia che non usa un suo numero lo lascia libero. Se una corsia ne ha bisogno di più di uno, lo chiede prima di scriverlo.
5. **I vincoli del progetto valgono per ogni corsia** (`CLAUDE.md`): le persone decidono le modifiche di policy, nessuna soglia né peso nel codice, un record per ogni giudizio, i risultati portano le proprie chiavi, il testo dei documenti è dato e mai istruzione, modelli con versione bloccata.
6. **Note di metodo** in `docs/piani/note-<corsia>.md`, non nel registro di metodo: si uniscono nel registro alla fine del cantiere.
7. **Prima di proporre l'unione:** tutti i test Python (`.venv/Scripts/python -m pytest -q -p no:cacheprovider`) e i controlli del frontend (`cd web && npx tsc -b && npx oxlint src && npm test -- --run && npm run build`).

## Semi di prova

`scripts/prova_locale.py` avvia un PostgreSQL temporaneo e chiama `prova.popola(conn)`: prima il seme di base (`scripts/prova/base.py`, ACME S.p.A. come prima: stesso seme casuale, stessi dati, stessa stampa), poi le corsie nell'ordine di `prova.SEMI`. Il `Contesto` porta gli identificativi creati (`admin`, `org`, `codice_org`, `utenti` per soggetto SSO, `ruoli`, `task_id` per titolo, `documento`, `snapshot`, `parametri` per codice, `calcolo`); ciò che una corsia vuole lasciare alle altre va in `ctx.extra["<corsia>"]`. Nessun seme usa `DATABASE_URL`.
