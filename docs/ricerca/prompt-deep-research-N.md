# Prompt per la ricerca di fonti per il calcolo di N

Sei un ricercatore incaricato di trovare fonti per un progetto di misurazione.

## Obiettivo

Costruire una knowledge base dei task di lavoro di **tutti i ruoli di staff in azienda**
(amministrazione, finanza, risorse umane, acquisti, qualità, legale, IT, marketing,
segreteria e simili), che misuri per ogni task:

- **N**, la necessità dell'apporto umano oggi, cioè quanto la tecnologia IA dimostra di
  saper fare il task (capacità misurata, non uso osservato);
- **D**, quanto è desiderabile che il task resti umano (solo se trovi fonti, senza cercarle fuori
  dal perimetro indicato sotto).

Non cercare fonti su servizi alla persona, sanità o assistenza: sono fuori perimetro in questa fase.

## Cosa cerco, in ordine di priorità

1. **Valutazioni di capacità su task reali o su task equivalenti a compiti di lavoro d'ufficio**:
   benchmark con compiti da professionisti, valutazioni di qualità dei risultati, confronti
   con esperti umani.
2. **Tassi di successo misurati per task o per famiglia di task** (non solo quota d'uso).
3. **Dataset pubblici** che si possono scaricare e rielaborare, con licenza esplicita
   (CC BY, MIT, Apache, dominio pubblico o simile).
4. **Collegamenti a O\*NET** (ID di task, attività intermedie o professioni): sono essenziali,
   perché senza di essi il dato non si può agganciare ai nostri task.
5. **Dati su desiderabilità** dell'automazione per lavoratori o utenti di mansioni d'ufficio,
   solo se emergono dalle stesse ricerche.

## Criteri di autorevolezza

- preferisci pubblicazioni peer-reviewed, report di istituzioni (OCSE, ILO, Banca d'Italia,
  Eurostat, BLS, INAPP) o di laboratori che pubblicano il dataset e il metodo;
- per ogni fonte, indica se il dato è misurato (benchmark, esperimento, log di sistemi) o stimato
  (giudizio di esperti, modello predittivo, uso osservato);
- segnala conflitti di interesse: fonti prodotte da chi vende il prodotto valutato.

## Cosa restituire

Una tabella con una riga per fonte, con queste colonne:

| campo | contenuto |
|---|---|
| fonte | autori, titolo, anno |
| link | URL verificato (non inventato) |
| tipo_dato | benchmark / successo / uso / esperti / stima modello |
| misura | cosa misura esattamente, con l'unità e la scala |
| livello | task / famiglia di task / occupazione (SOC) / attività O\*NET |
| collegamento_O*NET | sì (come: ID, testo, SOC) / no / parziale |
| dataset_pubblico | URL del dataset, se esiste |
| licenza | testo esatto della licenza, o "non dichiarata" |
| n | dimensione del campione o numero di task |
| data | data di pubblicazione o rilascio dei dati |
| qualità | alta / media / bassa, con una riga di motivazione |
| limiti | avvertenze dichiarate dagli autori |

## Regole

- Non inventare link, licenze o numeri: se un dato non lo trovi, scrivi "non trovato".
- Verifica ogni URL aprendolo. Se un sito non è raggiungibile, segnalalo.
- Ordina le fonti per utilità: prima quelle con dataset pubblico, licenza e collegamento a O\*NET.
- Alla fine elenca le **lacune**: quali task o famiglie di lavoro d'ufficio restano senza alcuna fonte.
