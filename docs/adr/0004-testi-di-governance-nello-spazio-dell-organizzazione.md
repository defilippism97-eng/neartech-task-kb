# ADR-0004: I testi di governance dell'organizzazione stanno nel suo spazio

**Data:** 2026-10-16
**Stato:** accettato; realizzazione in corso
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
