# ADR-0002: Il comitato guida dà indirizzi, i revisori giudicano i singoli task

**Data:** 2026-10-16
**Stato:** accettato
**Chi decide:** responsabile del progetto (risolve il conflitto 3 di `docs/architettura/stato-e-decisioni.md`)

## Contesto

Il workflow rivisto unisce metodologo e comitato nel comitato guida. Se il comitato decidesse anche sul singolo task, la stessa persona potrebbe proporre e approvare una variazione di D. Esempio: un membro propone di abbassare D per "Garantire un'accoglienza professionale nel rispetto dei protocolli", e lo stesso comitato approva. Nessuno indipendente controlla la motivazione, e un rialzo non viene bloccato nemmeno dai rappresentanti dei lavoratori.

## Decisione

Le responsabilità si separano **per livello**, non per persona dentro lo stesso livello:

- **Comitato guida:** emette **indirizzi** di alto livello e direzionali, cioè criteri sui valori dell'organizzazione e sulle classi di task. Non decide sul singolo task. Ogni indirizzo è versionato, motivato e registrato con chi lo ha proposto e quando.
- **Revisori:** valutano se la classificazione del singolo task è corretta. Verificano le ricadute pratiche degli indirizzi sui task e **segnalano** le situazioni anomale: per esempio un indirizzo che sposta in modo forte o concentrato i punteggi, o che sembra servire un interesse particolare.
- Il sistema propone le ricadute di un indirizzo sui task, i revisori le giudicano: ogni giudizio è un record. Le segnalazioni entrano nel registro delle decisioni e sono visibili al comitato guida, all'auditor e ai rappresentanti dei lavoratori.

## Alternative considerate

### Quattro occhi dentro il comitato
- **Pro:** si fa rispettare con un vincolo nello schema (chi approva è diverso da chi propone).
- **Contro:** il comitato resta il luogo delle decisioni sul singolo task.
- **Perché no:** non separa il livello degli indirizzi dal livello della classificazione.

### Astensione del proponente e quorum
- **Pro:** controllo collegiale.
- **Contro:** dipende dalla dimensione del comitato; stesso limite del punto precedente.
- **Perché no:** come sopra.

### Solo segnalazione a posteriori
- **Pro:** nessun vincolo operativo.
- **Contro:** il controllo arriva dopo la restituzione.
- **Perché no:** troppo debole.

## Conseguenze

### Positive
- Il comitato lavora su criteri, non su punteggi; i punteggi per task restano giudizi registrati dei revisori.
- Il conflitto tra proporre e approvare si risolve con la struttura, senza soglie nel codice.

### Negative
- La "variazione dell'organizzazione" nella formula di D (`stato-e-decisioni.md`, sezione 5) non è più approvata task per task dal comitato. Deriva dagli indirizzi del comitato e dal giudizio dei revisori sul singolo task.
- Serve un oggetto nuovo nello schema: l'indirizzo, con versione, motivazione, proponente, approvazione e i task su cui ricade.

### Rischi
- Un indirizzo molto specifico può di fatto riguardare un solo task. Mitigazione: il revisore lo segnala.
- La separazione funziona se le persone sono diverse. Il responsabile ha deciso (2026-10-16) che una stessa persona può essere membro del comitato guida e revisore: il sistema non impone vincoli (`docs/metodologia-estensioni.md`, sezione 8).
- Il blocco dei ribassi da parte dei rappresentanti dei lavoratori resta in vigore e si applica alle ricadute degli indirizzi.
