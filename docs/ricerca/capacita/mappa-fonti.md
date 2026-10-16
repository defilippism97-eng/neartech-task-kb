# Mappa delle fonti sulla capacità tecnologica (c_k)

**Data della ricerca:** 2026-10-16. **Stato:** mappa preliminare. Nessuna fonte è stata calibrata sulla nostra scala 0–4, e nessuna è stata validata da esperti umani sul nostro perimetro.

## 1. La domanda

N richiede, per ciascun asse k, un confronto fra la domanda del task (dk) e la capacità tecnologica (ck). Il silver etichetta solo la domanda. Qui si mappano le fonti che possono misurare la capacità a livello di task, con la loro granularità, licenza e limiti.

## 2. Risposta breve

Esistono fonti di capacità a livello di task, ma nessuna risponde direttamente al nostro schema. Nessuna dà un punteggio separato per k1, k2 e k3 su scala 0–4 per i task O*NET. Il lavoro di calibrazione e di verifica della licenza resta da fare.

## 3. Fonti

### 3.1 Li Gan (2026), "Execution and Evaluation: A New Occupational Measure and Long-Run Employment Gradients"
- **Fonte:** arXiv:2607.20807, preprint, un solo autore, luglio 2026.
- **Cosa misura:** un punteggio di capacità per tutti i 19.265 task O*NET, su scala 0–100. La domanda del rubric è se un modello linguistico di frontiera, con accesso agli strumenti, può eseguire il task come scritto a uno standard professionale.
- **Granularità:** task O*NET. Collegamento esatto ai nostri task di origine O*NET.
- **Versione O\*NET:** 26.1 come base; ricostruzione dell'esecuzione su 30.3.
- **Validazione:** solo accordo fra due valutatori automatici (correlazione 0,991 su 500 affermazioni). L'autore dichiara "non validato da umani".
- **Licenza e dati:** non dichiarate nel testo letto. Per usarlo serve verificare se i punteggi per task sono pubblicati e con quale licenza.
- **Limite per noi:** è un punteggio unico, non separato per k1, k2 e k3. Va mappato, e la mappatura richiede calibrazione umana.

### 3.2 Mertens, Kuzee, Harris, Lyu, Li, Rosenfeld, Anto, Fleming, Thompson (2026), "Crashing Waves vs. Rising Tides"
- **Fonte:** arXiv:2604.01363v3, CC BY 4.0.
- **Cosa misura:** qualità di una risposta a un'istanza di task, su scala 1–9. Il valore principale è se l'output è utilizzabile senza modifiche (punteggio 7).
- **Granularità:** 6.648 task O*NET analizzati, con 12.078 istanze generate da un modello. Copertura limitata ai task con almeno il 10% di tempo risparmiabile stimato.
- **Valutazione:** il testo non è chiaro. Si dice sia "judged by 5 of 41 LLMs" e allo stesso tempo che i partecipanti sono residenti USA su Prolific con almeno sei mesi di esperienza. Va chiarito nel PDF completo prima di usarlo.
- **Licenza:** CC BY 4.0. Dati per task: non dichiarati nel testo letto.
- **Limiti dichiarati:** task autosufficienti (esclusi lavori con file, software o più turni), risposte limitate a 700 parole, giudicato solo l'output finale.

### 3.3 GDPval (OpenAI, 2025)
- **Fonte:** benchmark con 1.320 task, 44 professioni, 9 settori. Open subset su Hugging Face: 220 task.
- **Cosa misura:** tasso di vittoria di un modello contro il lavoro di un esperto umano, giudicato da esperti della stessa professione in cieco.
- **Granularità:** professione, non task O*NET. Nessun codice O*NET o BLS nel dataset. Il collegamento va costruito.
- **Licenza:** il paper dichiara CC BY 4.0 (fonte secondaria). La scheda del dataset non riporta una licenza nel testo letto: va verificata direttamente.
- **Uso per noi:** utile come ancora di esempi per la capacità su compiti reali, non come punteggio per task.

### 3.4 ILO Working Paper 140 (Gmyrek, Berg e altri, 2025)
- **Fonte:** CC BY 4.0.
- **Cosa misura:** esposizione dei task ISCO-08 alla GenAI, ricavata da un sondaggio di lavoratori (52.558 punti dati su 2.861 task), validato da esperti in un Delphi, poi replicato da un assistente AI.
- **Granularità:** task ISCO-08, non O*NET. Il collegamento richiede una tabella di corrispondenza fra le classificazioni.
- **Limite:** misura il potenziale di automazione percepito dai lavoratori, non la capacità tecnica. Serve come confronto, non come c_k.

### 3.5 Skill-level benchmark (aprile 2026, preprint)
- **Cosa misura:** un indice di fattibilità di automazione per 35 competenze O*NET, con 263 task testuali su quattro modelli.
- **Granularità:** competenze, non task. Troppo grossolana per N a livello di task.

### 3.6 Eloundou et al. (2023), "GPTs are GPTs"
- **Cosa misura:** esposizione dei task O*NET ai modelli GPT-4, su tre livelli (E0, E1, E2).
- **Limite:** modello del 2023, già superato. Utile come confronto storico.

## 4. Cosa manca e cosa va fatto

1. **Verificare la licenza e la disponibilità dei punteggi per task** di Li Gan e di Mertens et al. Senza dati scaricabili, non si può costruire c_k.
2. **Leggere i PDF completi.** Lo strumento di ricerca non li legge per intero. Serve il testo integrale per il rubric di Li Gan e per le istruzioni dei valutatori di Mertens et al.
3. **Calibrare la scala.** Il punteggio di Li Gan (0–100) e quello di Mertens et al. (1–9) vanno convertiti in livelli 0–4 per ciascun k. La conversione richiede un campione etichettato da persone, e il campione non è ancora disponibile.
4. **Collegare GDPval ai task O*NET** per professione, come controllo esterno.
5. **Registrare la versione del modello** che ha prodotto ogni punteggio, perché la capacità cambia nel tempo (piano: versione bloccata e ritaratura a ogni cambio).

## 5. Cosa non si può fare oggi

- Non si può dichiarare che ck è misurata sulla scala 0–4 per nessun task.
- Non si possono usare questi punteggi come capacità dimostrata in produzione. Sono misure di capacità di un modello in condizioni di test.
- Non si possono usare come sostituto della validazione umana del panel.
