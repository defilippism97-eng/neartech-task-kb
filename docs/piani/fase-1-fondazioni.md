# Piano: Fase 1, fondazioni del software

**Branch:** `fondazioni`. **Riferimenti:** `docs/HANDOVER.md` sezione 4, ADR 0001 e 0002, `CLAUDE.md`.
**Complessità:** media-alta. Nessuna chiamata a modelli e nessuna scrittura in produzione in questa fase.

## 1. Requisiti

1. **Spazio condiviso e spazio dell'organizzazione (ADR 0001).** Il dataset NEARTECH contiene solo task canonici, stato di validazione e dati derivati. Il testo del cliente (estratti, note di contesto, ruoli, documenti) sta in uno spazio per organizzazione.
2. **Utenti, ruoli e permessi.** Ruoli: amministratore tecnico, comitato guida, revisore, rappresentante dei lavoratori (facoltativo), auditor (sola lettura su tutto). Permessi in tabella, non nel codice. Gli utenti del sistema sono identificati da un identificativo opaco dell'SSO: nomi ed email restano nel fornitore di identità.
3. **Registro delle decisioni.** Append-only: proposte, approvazioni, rifiuti, segnalazioni dei revisori, blocchi dei rappresentanti dei lavoratori. Una correzione è una riga nuova che rimanda alla precedente. Catena di hash per rendere visibile all'auditor ogni manomissione.
4. **Parametri di governance versionati.** Una tabella generica (codice, versione, valore, organizzazione, stato, proposta e approvazione legate al registro). Ospiterà soglia di precisione, livello di revisione iniziale, percentuale minima di revisione, regola sui parziali. Nessun valore inserito dal codice.
5. **Indirizzi del comitato guida (ADR 0002).** Tabella degli indirizzi, versionati e motivati. Le ricadute sui singoli task arrivano nella fase 4.
6. **Stato di validazione dei task.** `validato`, `stima del modello`, `da integrare`, con storia (un record per ogni cambio di stato).
7. **Coda dei job.** La tabella `jobs` esiste: si estende con presa in carico (`FOR UPDATE SKIP LOCKED`), errori, tentativi e organizzazione. Worker Python pianificato, senza piattaforma di orchestrazione.
8. **Log di accesso.** Append-only: chi, quale organizzazione, quale risorsa, quale azione, esito.
9. **Registro delle migrazioni.** Oggi le migrazioni si applicano a mano e nessuna tabella ricorda quali sono state applicate. Serve `migrazioni_applicate` con hash del file.

## 2. Modelli da seguire nel codice esistente

| Categoria | Fonte | Modello |
|---|---|---|
| Migrazioni | `db/migrations/0002_*.sql` | Intestazione con scopo e ordine; mai modifiche in place a `schema.sql` |
| Record non sovrascrivibili | `db/migrations/0005_revisioni_crosswalk.sql` | Ogni esito è una riga; `UNIQUE` sul campione |
| Accesso ai dati | `src/neartech/canonicalizer.py:69` | Funzioni con `conn: psycopg.Connection` come primo argomento, SQL esplicito |
| Connessione | `src/neartech/db.py:15` | DSN dall'ambiente, mai dal codice |
| Test | `tests/conftest.py`, `tests/test_f0.py` | Database dedicato con "test" nel nome, schema e migrazioni applicati per sessione, rollback per test, dati sintetici |
| Nomi | `scomposizione.py`, `revisioni_crosswalk` | Tabelle e funzioni nuove in italiano; le tabelle esistenti in inglese restano |

## 3. Scelte tecniche (da registrare nell'ADR 0003)

- **Uno schema PostgreSQL per organizzazione** (`org_<codice>`), con le tabelle con testo del cliente. Il dataset condiviso resta in `public`. Motivi: confine netto richiesto dall'ADR 0001; uscita del cliente con un solo `DROP SCHEMA`; permessi per schema a livello di database. Le migrazioni dello spazio organizzazione stanno in `db/migrations_org/` e si applicano a ogni schema con `search_path` impostato: nessun template di testo SQL.
- **Append-only nel database, non solo nel codice:** trigger che rifiutano `UPDATE` e `DELETE` su registro, log di accesso, giudizi e storia degli stati.
- **Permessi verificati in un solo punto** (`neartech.permessi`), con lettura della tabella ruoli-azioni. L'API e l'interfaccia (fasi successive) passano tutte da qui.
- **Valori di default con significato di policy da togliere dallo schema:** `weight_profiles.theta_n`, `theta_d` e `lambda_r` hanno default (0.50, 0.50, 0.5) scritti in `schema.sql`. Una migrazione li rimuove: il valore deve venire dal profilo approvato.

## 4. Passi

Ogni passo: test prima (`ecc:tdd-workflow`), poi migrazione o codice, poi revisione.

0. **Database di test locale.** Provare `pgserver` (Postgres con pgvector incluso, installabile con pip) nel `.venv`; in alternativa un branch Neon dedicato ai test, che però richiede una credenziale e quindi il responsabile. Aggiornare `conftest.py` per avviarlo quando `NEARTECH_TEST_DSN` manca.
1. **Registro delle migrazioni** (`0007`) e script `scripts/migra.py` con modalità `--verifica` (sola lettura: elenca cosa manca) e applicazione. In produzione si usa solo `--verifica` finché il responsabile non approva.
2. **Organizzazioni, utenti, ruoli, permessi** (`0008`): `utenti`, `ruoli` (codici), `assegnazioni_ruolo` (utente, ruolo, organizzazione, validità), `permessi_ruolo` (ruolo, azione). Modulo `neartech.permessi` con `puo(conn, utente, azione, org)`.
3. **Registro delle decisioni** (`0009`): tabella append-only con catena di hash, trigger di protezione, funzione di verifica della catena per l'auditor.
4. **Parametri di governance e indirizzi del comitato** (`0010`): tabelle versionate legate al registro; un parametro diventa attivo solo con un'approvazione registrata da un ruolo abilitato.
5. **Stato di validazione dei task** (`0011`): storia degli stati per task canonico; vista con lo stato corrente.
6. **Spazio dell'organizzazione** (`migrations_org/0001`): ruoli organizzativi, occorrenze con testo, documenti. Funzione `crea_spazio_organizzazione(conn, codice)`. Le tabelle `public.roles` e `public.task_occurrences` restano finché i dati non sono spostati (passo 9).
7. **Coda dei job** (`0012`) e `neartech.coda` (accoda, prendi, completa, fallisci) con worker `scripts/worker.py`.
8. **Log di accesso** (`0013`), scritto da `neartech.permessi` a ogni verifica.
9. **Piano di spostamento dei dati di Società Dolce** nello spazio dell'organizzazione: script con `--dry-run` che legge e conta. **L'esecuzione in produzione si chiede al responsabile.**
10. **Revisioni:** `ecc:python-reviewer`, `ecc:database-reviewer`, `ecc:security-review`; `ecc:santa-loop` su registro, permessi e spazio organizzazione. Poi pull request verso `main` (l'unione si chiede al responsabile).

## 5. Rischi

| Rischio | Probabilità | Mitigazione |
|---|---|---|
| Nessun database di test disponibile | Alta oggi | Passo 0; senza database i test vengono saltati e nessun passo si considera chiuso |
| `pgserver` non disponibile per Python 3.15 su Windows | Media | Branch Neon di test o Postgres installato dal responsabile |
| Le migrazioni esistenti non sono tracciate in produzione | Certa | Il registro parte con le 0002–0006 marcate come già applicate, dopo una verifica in sola lettura che le tabelle esistano |
| Rimuovere i default di `theta` rompe inserimenti esistenti | Bassa | Solo i test inseriscono profili oggi; si aggiornano nello stesso passo |
| Gli utenti del sistema sono persone | Certa | Solo identificativo opaco dell'SSO e ruolo; nessun output sugli utenti. Da sottoporre al DPO insieme al resto |
| Il codice esistente (`scomposizione.py`) scrive testo del cliente in `public` | Certa | Resta così fino al passo 9; poi si aggiorna per scrivere nello spazio dell'organizzazione |

## 6. Decisioni del responsabile (2026-10-16)

Registrate in `docs/metodologia-estensioni.md`, sezione 8.

1. **Curatore:** compito dei revisori (abbinamenti e fusioni); fonti e snapshot all'amministratore tecnico. Nessun ruolo a sé.
2. **Rappresentanti dei lavoratori:** ruolo distinto, che può restare vuoto. Senza rappresentanti il blocco dei ribassi non si applica. Proposta tecnica: il report finale dichiara se l'organizzazione ha rappresentanti assegnati.
3. **Incompatibilità:** nessun vincolo tra comitato guida e revisore. La tabella `incompatibilita_ruoli` non si crea.
4. **59 task non attivi:** etichette dei 54 fusi come giudizi sul task superstite; i 5 ritirati fuori. Si applica nella fase 2. Resta da decidere la regola sui collegamenti parziali.

## 7. Criteri di chiusura

- Tutte le migrazioni si applicano su un database vuoto e i test passano su un database reale, non saltati.
- `UPDATE` e `DELETE` sulle tabelle append-only falliscono nei test.
- Nessun valore di soglia, peso o quorum nel codice o nello schema.
- `HANDOVER.md` aggiornato e ADR 0003 registrato.
