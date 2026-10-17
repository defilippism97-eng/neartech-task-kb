# ADR-0006: Abbinamento al dataset: candidati e proposte nello spazio, decisione in blocco, applicazione deterministica

**Data:** 2026-10-17
**Stato:** accettato
**Chi decide:** responsabile del progetto (realizza la canonicalizzazione rivista dell'handover, sezione 3)

## Contesto

Nella prima scomposizione ogni attività di Società Dolce è diventata subito un task del dataset condiviso, e il Canonicalizer le ha poi fuse a posteriori: 15 fusioni su 61 erano sbagliate o parziali. La versione rivista del metodo vuole il contrario: il task dell'organizzazione si abbina al task più vicino del dataset consolidato, il revisore approva o rifiuta, e solo i task senza corrispondenza entrano nel dataset. N e D di un task già consolidato si trasferiscono.

## Decisione

1. Le attività estratte sono **candidati** nello spazio dell'organizzazione: titolo, estratto e nota sono dati dell'organizzazione finché una decisione non le porta nel dataset.
2. Le **proposte** sono il task attivo più vicino per embedding, con distanza, margine sul secondo e vicini salvati. Nessuna soglia di distanza: la vicinanza ordina la coda di revisione, non decide.
3. Il **lotto** dichiara il livello di revisione (`campione`, `completa`, `nulla`) e, con `campione`, il parametro della quota; la misura di precisione si fa sul campione del lotto.
4. Il revisore **decide in blocco**: approva il lotto tranne le proposte che rifiuta. Ogni proposta ha il suo record, legato all'atto nel registro.
5. L'**applicazione** è deterministica e registrata: proposta approvata, occorrenza sul task esistente; proposta rifiutata o senza vicini, task nuovo con il titolo rielaborato in public e il testo del cliente nello spazio.

## Alternative considerate

### Creare subito i task e fondere dopo (prima scomposizione)
- **Pro:** nessun passo di revisione prima dell'ingresso nel dataset.
- **Contro:** gli errori di fusione si correggono solo a posteriori, con separazioni.
- **Perché no:** è ciò che la revisione delle 61 fusioni ha mostrato non affidabile.

### Proposte giudicate dal modello
- **Pro:** filtrerebbe i candidati senza corrispondenza.
- **Contro:** il prompt di confronto v2 non ha superato il set di controllo.
- **Perché no, per ora:** resta una decisione metodologica aperta (piano della fase 3).

## Conseguenze

### Positive
- Nessun task entra nel dataset senza una decisione umana sul lotto.
- Due organizzazioni con lo stesso task ottengono lo stesso N e D.
- La precisione dell'abbinamento si misura per lotto con la metrica della fase 2.

### Negative
- Tabelle nuove nello spazio di ogni organizzazione; l'embedding dei candidati richiede il modello locale.

### Rischi
- Un lotto approvato in blocco con misura sotto soglia: l'atto lo registra; se vada impedito è una decisione aperta.
