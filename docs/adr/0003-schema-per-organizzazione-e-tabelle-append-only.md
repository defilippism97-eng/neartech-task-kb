# ADR-0003: Uno schema per organizzazione, tabelle append-only nel database, registro delle migrazioni

**Data:** 2026-10-16
**Stato:** accettato
**Chi decide:** sviluppo (scelta tecnica e reversibile), in attuazione dell'ADR 0001

## Contesto

L'ADR 0001 richiede che il testo del cliente resti fuori dal dataset condiviso. Le regole di progetto chiedono un record per ogni giudizio e nessuna sovrascrittura. Oggi tutto sta nello schema `public`, le migrazioni si applicano a mano e nessuna tabella ricorda quali sono state applicate.

## Decisione

1. **Uno schema PostgreSQL per organizzazione** (`org_<codice>`) con le tabelle che contengono testo del cliente (`ruoli_organizzativi`, `documenti`, `occorrenze`). Il dataset condiviso resta in `public`. Le migrazioni dello spazio organizzazione stanno in `db/migrations_org/` e si applicano a ogni schema con `search_path` impostato.
2. **Append-only nel database**: trigger che rifiutano `UPDATE`, `DELETE` e `TRUNCATE` su registro delle decisioni, log di accesso, parametri, indirizzi e storia degli stati. Il registro ha una catena di hash verificabile dall'auditor.
3. **Registro delle migrazioni** (`migrazioni_applicate`) con l'hash di ogni file; una migrazione già applicata che cambia blocca la verifica.
4. **Stato derivato dal registro**: approvato, rifiutato e ritirato non sono colonne aggiornate, ma l'ultimo atto nel registro delle decisioni.

## Alternative considerate

### Un solo schema con `org_id` e Row Level Security
- **Pro:** migrazioni uniche, join semplici.
- **Contro:** il testo del cliente sta nelle stesse tabelle del dataset condiviso; l'isolamento dipende da policy che vanno sempre attive.
- **Perché no:** l'ADR 0001 chiede un confine netto; l'uscita di un cliente con RLS richiede cancellazioni riga per riga.

### Un database per organizzazione
- **Pro:** isolamento massimo.
- **Contro:** niente chiavi esterne verso il dataset condiviso; abbinamento e flywheel diventano join applicativi.
- **Perché no:** costo sproporzionato per il pilota. Resta possibile spostare uno schema in un database proprio.

### Append-only solo nel codice
- **Pro:** nessun trigger.
- **Contro:** uno script o una query manuale può riscrivere la storia.
- **Perché no:** la regola "le correzioni non sovrascrivono" deve reggere anche fuori dall'applicazione.

## Conseguenze

### Positive
- Uscita di un cliente con un solo `DROP SCHEMA`; permessi di database per schema quando ci saranno ruoli di database per organizzazione.
- Ogni stato di governance è ricostruibile e verificabile dal registro.

### Negative
- Ogni migrazione dello spazio organizzazione va applicata a tutti gli schemi (`neartech.organizzazioni.aggiorna_spazi`).
- Il proprietario delle tabelle o un superuser può disattivare i trigger: la catena di hash rende visibile la manomissione, ma non la impedisce. In produzione l'applicazione dovrà usare un ruolo di database senza proprietà sulle tabelle.

### Rischi
- Le tabelle `public.roles` e `public.task_occurrences` contengono ancora il testo di Società Dolce. Lo spostamento nello spazio dell'organizzazione è una scrittura in produzione e richiede l'approvazione del responsabile.
- In produzione le migrazioni 0002–0006 sono applicate ma non registrate: vanno registrate con `scripts/migra.py --registra-esistenti` dopo una verifica, anche questa con approvazione.
