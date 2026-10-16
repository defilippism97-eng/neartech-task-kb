# ADR-0001: Il testo del cliente resta fuori dal dataset condiviso

**Data:** 2026-10-16
**Stato:** accettato
**Chi decide:** responsabile del progetto (risolve il conflitto 2 di `docs/architettura/stato-e-decisioni.md`)

## Contesto

Il dataset NEARTECH è condiviso tra organizzazioni e cresce con il data flywheel. Il workflow rivisto prevedeva che un task non abbinato entrasse nel database comune con una colonna riservata al cliente. Una colonna non basta a separare i dati: il testo dei mansionari e delle job description è dato del cliente. Oggi lo schema unico conserva il testo originale in `task_occurrences.raw_snippet` e `task_occurrences.context_note`, accanto ai task canonici.

## Decisione

Nel dataset condiviso entra solo la **rielaborazione** del task: il titolo canonico e le informazioni derivate (N, D di base, stato, versioni). Il testo originale del cliente (documenti, estratti, note di contesto delle occorrenze, nomi dei ruoli) resta nello spazio dell'organizzazione. Il legame tra il task canonico e il cliente è un riferimento all'organizzazione, senza testo.

## Alternative considerate

### Colonna riservata al cliente nel database comune
- **Pro:** schema semplice, un solo database.
- **Contro:** il testo del cliente resta in un archivio condiviso; la separazione dipende dai permessi di lettura.
- **Perché no:** non rende i dati anonimi e richiederebbe una base giuridica per ogni cliente.

### Nessuna condivisione
- **Pro:** isolamento completo.
- **Contro:** niente data flywheel; due aziende con lo stesso task possono ricevere punteggi diversi.
- **Perché no:** contraddice la base di conoscenza come fondamento del software (`stato-e-decisioni.md`, sezione 6).

## Conseguenze

### Positive
- Il dataset condiviso si può riusare tra clienti senza trasferire testi del cliente.
- Lo schema multi-organizzazione ha un confine netto: dataset condiviso da una parte, spazio dell'organizzazione dall'altra.

### Negative
- I dati esistenti vanno spostati: `raw_snippet` e `context_note` delle occorrenze di Società Dolce passano nello spazio dell'organizzazione. È una scrittura sul database di produzione e richiede l'approvazione del responsabile.
- Il curatore che rivede un abbinamento deve poter leggere il testo originale dallo spazio dell'organizzazione: serve un permesso per organizzazione.

### Rischi
- Un titolo canonico molto vicino al testo originale, soprattutto per i task non abbinati, può riprodurre il testo del cliente. Mitigazione: la rielaborazione è prodotta dall'agente e approvata dal curatore prima di entrare nel dataset.
- In ruoli con pochi occupati, il task canonico legato a ruolo e organizzazione può identificare persone. La verifica resta al DPO, oggi sospesa.
