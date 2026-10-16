# ADR-0005: In `public` resta uno scheletro senza testo del cliente

**Data:** 2026-10-17
**Stato:** accettato; realizzato
**Chi decide:** responsabile del progetto (realizza l'ADR 0001)

## Contesto

L'ADR 0001 vuole il testo del cliente fuori dal dataset condiviso. Il testo di Società Dolce era in `public` in tre posti: `task_occurrences.raw_snippet` e `context_note` (estratti dei mansionari), `roles.name` (nomi dei ruoli) e `sources.name` (nomi dei file). Le viste, il Canonicalizer e il crosswalk usano però i legami task–ruolo–documento di `public`, e le chiavi esterne del dataset puntano lì.

## Decisione

1. In `public` restano i legami con gli stessi identificativi dello spazio dell'organizzazione, senza testo: `raw_snippet` e `context_note` vuoti, nomi neutri `ruolo <id>` e `documento <id>`.
2. Il testo sta solo in `org_<codice>` (`occorrenze`, `ruoli_organizzativi`, `documenti`). Il codice scrive in entrambi i posti con `neartech.occorrenze` (`ruolo`, `documento`, `registra_occorrenza`, `sposta_occorrenze`).
3. I vincoli della migrazione 0023 impediscono che il testo torni in `public`; la 0024 li convalida su tutte le righe dopo la pulizia.
4. La pulizia di un'organizzazione già caricata (`togli_testo_da_public`) si fa solo se ogni riga ha nello spazio la copia identica con lo stesso identificativo, ed è un atto `correzione` nel registro.

## Alternative considerate

### Togliere da `public` anche i legami
- **Pro:** separazione completa.
- **Contro:** cambiano viste, Canonicalizer, crosswalk e chiavi esterne del dataset; il conteggio delle occorrenze per task (che decide il superstite di una fusione) andrebbe calcolato su tutti gli spazi.
- **Perché no:** i legami senza testo non rivelano il contenuto dei documenti; il costo non è giustificato per il pilota.

### Cifrare il testo in `public`
- **Pro:** nessuna modifica alla struttura.
- **Contro:** la chiave diventa un segreto da gestire; il testo resterebbe comunque nel database condiviso dopo l'uscita del cliente.
- **Perché no:** contraddice l'ADR 0001.

## Conseguenze

### Positive
- All'uscita del cliente il suo testo esce con il suo schema; in `public` restano solo identificativi e task canonici.
- La separazione è garantita dal database, non solo dal codice.

### Negative
- Ogni scrittura di occorrenze tocca due schemi; gli spazi devono esistere prima di caricare documenti.
- La rimozione degli estratti da `public` è un aggiornamento che `public` non conserva: la copia nello spazio è l'unica fonte.

### Rischi
- Un codice che scrivesse direttamente in `task_occurrences` con testo fallisce per il vincolo: è il comportamento voluto.
- In produzione la pulizia di Società Dolce è stata fatta il 2026-10-17 (504 occorrenze, 36 ruoli, 36 documenti), ancora del registro alla posizione 23.
