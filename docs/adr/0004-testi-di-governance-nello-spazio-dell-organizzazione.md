# ADR-0004: I testi di governance dell'organizzazione stanno nel suo spazio

**Data:** 2026-10-16
**Stato:** accettato; realizzato il 2026-10-17 (migrazioni 0025 e org 0006)
**Chi decide:** responsabile del progetto (integra l'ADR 0001 e modifica in parte l'ADR 0003)

## Contesto

L'ADR 0001 tiene fuori dal dataset condiviso il testo dei documenti del cliente. Restano però in `public` testi scritti dall'organizzazione: gli indirizzi del comitato guida (`indirizzi_comitato`), le descrizioni dei parametri dell'organizzazione e le motivazioni negli atti del registro. Dopo l'uscita del cliente non si possono togliere, perché le tabelle sono append-only, e non stanno insieme al resto della sua analisi.

## Decisione

1. I testi di governance dell'organizzazione (indirizzi, descrizioni e motivazioni dei suoi parametri, motivazioni e dettagli dei suoi atti) si salvano nello spazio `org_<codice>`, insieme a occorrenze, ruoli e documenti.
2. Il registro delle decisioni condiviso conserva la catena di hash e i riferimenti, con l'hash del testo, non il testo.
3. Per ogni organizzazione si può estrarre un **unico report di audit**: analisi, parametri usati, indirizzi, giudizi, segnalazioni, misure e catena delle decisioni, verificabile.

## Alternative considerate

### Lasciare i testi in `public`
- **Pro:** nessuna modifica.
- **Contro:** il testo dell'organizzazione resta nel database condiviso anche dopo l'uscita; il report di audit va ricostruito da più posti.
- **Perché no:** contraddice l'obiettivo di un report unico e lo spirito dell'ADR 0001.

### Spostare anche il registro delle decisioni nello spazio dell'organizzazione
- **Pro:** separazione completa.
- **Contro:** la catena di hash comune verifica tutti gli atti in un solo ordine; spezzarla per organizzazione indebolisce la verifica degli atti comuni (parametri NEARTECH, amministrazione).
- **Perché no:** basta togliere il testo dal registro e tenerne l'hash.

## Conseguenze

### Positive
- Uscita del cliente con lo schema dell'organizzazione, testi compresi.
- Un report di audit unico per organizzazione.

### Negative
- Serve una migrazione che sposti `indirizzi_comitato` e i testi dei parametri dell'organizzazione nello spazio dell'organizzazione, e il codice di governance va adattato.
- Il registro va esteso con l'hash del testo spostato, per poterne verificare l'integrità.

### Rischi
- Gli atti già scritti in `public` restano dove sono (append-only). Oggi in produzione non ce ne sono: lo spostamento va fatto prima che il comitato guida inizi a usare il sistema.

## Realizzazione (2026-10-17)

- `neartech.registro.registra`: per un atto di un'organizzazione, motivazione e `dettagli_riservati` vanno in `org_<codice>.testi_atti`, nella stessa transazione; nel registro restano il marcatore `nello spazio dell'organizzazione`, i dettagli strutturali e `hash_testo`. `verifica_testi` confronta lo spazio con l'impronta.
- **Impronte con chiave:** `hash_testo`, `hash_descrizione` e `hash_contenuto` sono `sha256(chiave || testo)` con la chiave casuale dello spazio (`chiave_impronte`, migrazione 0006 degli spazi). Chi legge solo `public` non conferma un testo breve indovinato; all'uscita del cliente la chiave si cancella con lo spazio.
- **Vincoli nel database (0025):** per ogni atto con `org_id` il registro accetta solo il marcatore, un'impronta di 64 caratteri esadecimali e dettagli fatti di numeri, valori logici, codici e identificativi senza spazi; a fine transazione l'atto deve avere il suo testo nello spazio. Un'organizzazione senza spazio non registra atti. I testi di uno spazio riguardano solo oggetti della sua organizzazione.
- Indirizzi: testo e ambito in `testi_indirizzi`; parametri dell'organizzazione: descrizione in `testi_parametri`, hash nella proposta. `verifica_contenuti` li controlla nello spazio. Le descrizioni dei parametri comuni restano in `public`.
- Segnalazioni dei revisori: motivazione e dettagli nello spazio.
- Gli atti scritti prima della 0025 (5 in produzione, tutti dell'amministratore tecnico) restano in `public`, append-only.
- Applicazione: la 0025 e la 0006 degli spazi si applicano nello stesso giro di `scripts/migra.py`, con l'applicazione ferma.
