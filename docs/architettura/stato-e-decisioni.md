# Workflow e ruoli rivisti: stato e decisioni aperte

**Fonte:** `workflow-e-metodologia-rivisti.docx` (versione del 2026-10-16), salvato in questa cartella. Le note tra parentesi quadre sono quelle dell'autore del documento.

**Stato:** le modifiche sotto sono proposte. Il piano e le regole di progetto restano in vigore finché il comitato guida non approva il cambio. Quattro punti (sezione 2) vanno decisi prima di costruire il software.

## 1. Cosa cambia rispetto al piano

| Passo | Piano attuale | Versione rivista |
|---|---|---|
| Ingestione | Controllo di integrità e di licenza per ogni documento | Il controllo di licenza riguarda le fonti esterne. Per i documenti del cliente serve il controllo del trattamento dei dati, a cura del DPO |
| Canonicalizzazione | Confronto con i 5 task più vicini, decisione del modello | Abbinamento al task più vicino del database consolidato. Il curatore approva in blocco o rifiuta. Un task non abbinato entra nel database con fonte "Neartech" e una colonna riservata al cliente |
| Collegamento alle tassonomie | Passo separato con revisione del 10% | Superfluo, perché il passo precedente lo assorbe |
| Evidenze di capacità | Calcolo di N con capacità collegata | Per un task già consolidato, N e D si trasferiscono dal database. Il modello classifica solo i task nuovi, usando i task più vicini come riferimento |
| Revisione | Coda con regole approvate | Priorità di revisione per i task nuovi, con una percentuale minima di revisione umana da fissare |
| Budget AI | Non previsto | Gestito dall'amministratore tecnico, come nella console di Anthropic |
| Ruoli | Otto ruoli, poi cinque | Amministratore tecnico, Comitato guida, Revisori, Auditor |
| Calcolo | N e D dal profilo di pesi approvato | N dall'analisi tecnologica. D aggiornato dal comitato a partire dal punteggio di partenza nel database |

**Ruoli nella versione rivista.**
- **Amministratore tecnico:** super user, governa i parametri del frontend ed è il fornitore del servizio.
- **Comitato guida:** unisce metodologo e comitato. Fornisce dati e parametri, calibra rubrica e valori dell'impresa, vede i cruscotti e le restituzioni finali.
- **Revisori:** controllano che il sistema funzioni, con visibilità configurabile. Valutano concretamente D sul piano soggettivo.
- **Auditor:** vede tutto come il super user, solo in lettura.

## 2. Conflitti da decidere prima di costruire

1. **D condiviso tra aziende.** Il piano dice che D è per organizzazione: sono i valori che l'azienda decide di proteggere. Un database condiviso, in cui un task classificato per Dolce vale anche per un'altra azienda, contraddice questo principio. Opzione: un punteggio di partenza condiviso, personalizzato da ogni comitato guida.

2. **Database condiviso e dati dei clienti.** Il testo dei task del cliente entrerebbe nel database comune. La colonna riservata al cliente non basta da sola a rendere i dati anonimi. Serve una base giuridica, una clausola nel contratto con il cliente e una valutazione del DPO.

3. **Proposta e approvazione nello stesso ruolo.** Il comitato guida unisce metodologo e comitato. Il piano separa le due funzioni per evitare che una stessa persona proponga e approvi. Accettabile solo con la regola del conflitto registrata nel sistema.

4. **Lacune da non eliminare con il software.** La capacità di test sulla scala 0–4 richiede un campione etichettato da persone. D3 e d4 richiedono survey su lavoratori e utenti reali. Il software può essere costruito con queste lacune marcate. Non può farle sparire.

## 3. Cosa resta valido

- Gli agenti propongono, il calcolo è deterministico, le persone decidono.
- Nessuna soglia o peso nel codice: stanno in tabelle approvate dal comitato.
- Ogni giudizio porta la versione della rubrica e il modello.
- Nessun output riguarda una persona.
- Modifiche allo schema solo con migrazioni nuove.

## 4. Passi per il software

1. Decidere i quattro punti della sezione 2.
2. Aggiornare il documento di architettura con i ruoli rivisti.
3. Costruire le fondazioni: schema multi-organizzazione, tabella dei ruoli, registro delle decisioni, coda dei job.
4. Costruire l'abbinamento al database consolidato e la priorità di revisione.
5. Costruire il calcolo deterministico e gli output aggregati.
## 5. Decisione: D per organizzazione con punto di partenza condiviso (2026-10-16)

Scelta del responsabile del progetto. D resta un valore dell'organizzazione. Il punto di partenza è condiviso, ma ogni comitato guida lo personalizza.

**Formula:** `D_finale = max( pavimento legale ; base NEARTECH + variazione dell'organizzazione )`, limitato alla scala 0–4.

**Pavimento legale.** Per ogni task, il livello minimo che una norma verificata impone. Non può essere abbassato dall'organizzazione. Oggi nessuna norma è verificata in questo senso, quindi il pavimento è vuoto per tutti i task. Ogni pavimento deve citare la norma.

**Base NEARTECH.** Presentata all'organizzazione come "valutazione basata su dati NEARTECH". Nel record interno l'origine resta esplicita: oggi d1 e d2 sono stime del modello, provvisorie, e d3 e d4 mancano. La dicitura verso il cliente è neutra, ma il record deve dire il vero.

**Variazione dell'organizzazione.** Motivazione obbligatoria, approvazione del comitato guida, registrazione di chi l'ha proposta e quando. I rappresentanti dei lavoratori possono bloccare un ribasso.

**Ribassi forti.** Una variazione che porta D sotto la base di una soglia viene segnalata in revisione e riportata nel report finale. La soglia è un parametro del comitato guida, non una costante del codice.

**Record per task.** Tre valori separati: pavimento legale con norma, base con fonte e versione, variazione con motivazione e approvazione.
