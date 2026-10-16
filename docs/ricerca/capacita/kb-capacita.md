# Base di conoscenza sulla capacità e sull'uso dell'AI per N

**Versione:** v1, 2026-10-16. **Sostituisce:** `mappa-fonti.md`, di cui riprende i dati corretti.
**Catalogo leggibile dalla macchina:** `fonti.csv` (separatore `;`), una riga per fonte, con id, tipo, licenza e stato di verifica.

## 1. Struttura

La conoscenza su N è divisa in tre strati, che restano separati:

- **Strato A, capacità di test** (per task O*NET): quanto un modello di frontiera, in condizioni controllate, sa svolgere il task. Definizione approvata il 2026-10-16. Fonti: C01, C02, C03.
- **Strato B, uso osservato** (per task O*NET, per occupazione o per funzione): quanto l'AI viene usata nella pratica. Fonti: C04, C05, C06, C07, C08.
- **Strato C, domanda del task** (k1, k2, k3, r): dal silver, da completare con il sistema di etichettatura. D è trattato a parte.

## 2. Regole di unione

1. **Tutte le fonti entrano nel catalogo**, con il loro tipo. Nessuna è scartata a priori.
2. **Strato A e strato B non si sommano.** Restano colonne separate. Come combinarli in N è una decisione da approvare.
3. **L'uso osservato non è capacità.** Un task molto usato non è per questo un task che la tecnologia sa fare. Il piano lo indica come rischio esplicito ("uso osservato scambiato per capacità").
4. **Le fonti dello strato A sono in parte misurate con modelli Claude.** Li Gan usa Claude Sonnet 4.6 come valutatore (C01). Il nostro sistema di etichettatura, se basato su Claude, avrebbe la stessa dipendenza. Prima di usare i due insieme serve una verifica di indipendenza, che il golden dovrà fare.
5. **Ogni dato porta la fonte, la versione, la data e lo stato di verifica.**

## 3. Correzioni rispetto alla mappa precedente

- **Mertens et al. (C02):** la valutazione è di esperti umani sull'output dei modelli, non di LLM. La nota precedente era errata. Questa fonte ha quindi una validazione umana, più solida di quelle automatiche.
- **Li Gan (C01):** lo scorer è Claude Sonnet 4.6, non un modello generico. Esiste un archivio di replica con prompt e punteggi, la licenza non è dichiarata.
- **GDPval (C03):** la licenza del paper è CC BY 4.0 (fonte secondaria). La scheda del dataset, verificata, non dichiara una licenza nel testo letto.

## 4. Dal caso d'uso al task

McKinsey (C06), BCG (C07) e ISTAT (C08) descrivono l'uso per funzione, non per task. Per arrivare al task:

1. Estrarre i casi d'uso dai report, con la fonte e l'anno.
2. Mappare ogni caso d'uso ai task O*NET, con embedding e poi revisione umana a campione.
3. Registrare la corrispondenza in una tabella `caso_uso → task_id`, con confidenza e stato di revisione.

L'Anthropic Economic Index (C04) ha già una mappatura a task O*NET: è la prima fonte da usare per lo strato B a livello di task.

## 5. Fattori di N per task

| Fattore | Simbolo | Fonte | Stato |
|---|---|---|---|
| Domanda sugli assi k1, k2, k3 | dk | silver | da etichettare |
| Affidabilità richiesta | r | silver | da etichettare |
| Capacità di test | c_test | C01, C02, C03 | da calibrare sulla scala 0–4 |
| Uso osservato per task | u_task | C04 | disponibile per i task O*NET mappati |
| Uso per funzione (contesto) | u_funzione | C06, C07, C08 | disponibile solo per funzione |
| Capacità in produzione | c_prod | nessuna fonte diretta | lacuna |
| Vincoli normativi | riserva | AI Act, legge 132/2025 | in verifica (confluisce in d2) |

## 6. Lacune aperte

1. **Calibrazione di c_test** sulla scala 0–4. Serve un campione etichettato da persone: il golden.
2. **Licenze e dati per task** di Li Gan (C01) e Mertens (C02): da verificare nei repository e nelle pagine degli autori.
3. **Dettaglio per funzione** dei report McKinsey (C06) e ISTAT (C08). Lo statreport ISTAT 2025 va consultato direttamente.
4. **Capacità in produzione:** nessuna fonte la misura per task. La proxy disponibile è l'uso osservato (strato B) con le avvertenze della sezione 2.
5. **Sistema di etichettatura** da costruire al posto di Gemini. Richiede una chiave API e un budget approvato.
6. **Due fonti dello strato A non verificate sul testo completo:** SAFI (preprint, aprile 2026) ed Eloundou et al. (2023). Il loro link non è stato reperito.
