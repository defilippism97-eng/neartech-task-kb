# Relazione sulla conoscenza raccolta per il calcolo di N

Stato: **preliminare**. Nessun dato di questa relazione è calibrato e nessuna soglia o peso è approvato.
Data: 2026-10-12. Branch: `ricerca/workbank`.

## 1. Domanda

Per ogni task O\*NET di staff, quanto serve l'intervento umano (N)? N dipende dal divario fra la domanda del task sugli assi k1, k2, k3 e la capacità della tecnologia su quegli stessi assi, amplificato dalla criticità r. La domanda di questa fase è se abbiamo evidenze di capacità utilizzabili per N, e quanto sono affidabili.

## 2. Risposta breve

- **Non abbiamo evidenze di capacità utilizzabili a livello di task O\*NET per N.** Il file `carenza-evidenze.md` lo riporta: zero nodi coperti da una fonte di capacità con collegamento esatto.
- Abbiamo una **stima preliminare** di k1, k2, k3, r per tutti i 3.083 task di staff, fatta da un modello linguistico (Claude Haiku 5.5) con una rubrica in bozza. Non è una misura di capacità: è una stima di difficoltà del task per l'AI.
- Abbiamo una **verifica parziale** di coerenza con WORKBank: sulle voci k1 e k2 il segno è quello atteso rispetto alla capacità giudicata dagli esperti, ma la correlazione è moderata.

## 3. Cosa abbiamo

### 3.1 Tassonomie e database
- O\*NET 31.0: 18.838 task (schema `ONET_TASK`, lingua inglese).
- Atlante del Lavoro INAPP (snapshot 2026-10-10): 961 ADA, 2.482 RA, 7.129 attività.
- ESCO 1.2.1 in italiano: 3.039 occupazioni, 13.939 competenze.
- Embedding bge-m3 per 46.388 nodi.

Schema PostgreSQL 16 con pgvector, applicato e verificato in locale. **Il database non è persistente**: il caricamento va rifatto dopo un cambio di sessione, e i vettori sono da recuperare dalle parti salvate (vedi `STATO.md`).

### 3.2 Stima preliminare di N
- 3.083 task di staff in totale.
- **739 task**: k1 e k3 con 5 campioni, k2 e r con 1 campione.
- **2.344 task**: tutte e quattro le voci con 1 campione.
- Rubrica: bozza-2 per k2 e r; k1 e k3 bozza-1 nei 739 task della prima fase, bozza-2 nei nuovi.
- Ogni record conserva la versione della rubrica per voce, come richiesto dal piano.

La stima è in `docs/ricerca/estratti/llm-prior-staff-finale.jsonl`. Stato: "preliminare, non calibrato".

### 3.3 Verifica umana della rubrica
Il file del repo (`verifica-umana-campione.md`) riporta la prima verifica: 15 task, rubrica v1, giudizi del responsabile espressi senza vedere le stime, confronto con la mediana di cinque campioni:

| Voce | Accordo esatto | Entro 1 punto | Bias (modello − umano) | Correlazione |
|---|---|---|---|---|
| k1 | 8/15 | 15/15 | +0,07 | 0,59 |
| k2 | 5/15 | 14/15 | −0,33 | 0,28 |
| k3 | 9/15 | 14/15 | −0,47 | 0,50 |
| r | 6/15 | 11/15 | **−0,73** | 0,54 |

Il punto debole è k2, con accordo esatto solo 5 volte su 15. Il modello sottostima sistematicamente r di quasi tre quarti di punto, e r pesa sul calcolo di N.

Una seconda verifica alla cieca su 20 task sulla rubrica v2 ha dato accordi esatti di 14/20, 16/20, 16/20 e 18/20, con correlazioni di 0,37, 0,46, 0,72 e 0,89. Non ho però l'attribuzione delle correlazioni alle voci, e quella verifica non è versionata nel repo: va riportata da chi l'ha condotta.

Entrambe le verifiche sono piccole, coprono tre famiglie di professioni e hanno un solo valutatore.

### 3.4 Confronto con WORKBank
- 538 task in comune. Spearman con la capacità AI media degli esperti (Ae):
  - k1 −0,24; k2 −0,29; k3 +0,07; r −0,05.
- Il segno di k1 e k2 è quello atteso: più il task è complesso, meno gli esperti lo ritengono automatizzabile.
- Il tetto teorico per l'accordo fra esperti (α = 0,54) è circa 0,73: il nostro indicatore cattura solo una parte.
- Le ancore di Ae non sono disponibili. È stata usata un'ipotesi (`config/mappe_scala.json`) che non cambia il ρ ma rende inaffidabili i confronti di livello.

### 3.5 Altre fonti raccolte
| Fonte | Che cosa dà | Uso oggi |
|---|---|---|
| WORKBank (arXiv 2506.06576) | Ae e He di 52 esperti su 846 task | confronto di coerenza; licenza non dichiarata |
| Anthropic Economic Index | uso osservato per task (17.033 collegamenti esatti su O\*NET) | solo contesto; non è capacità |
| GDPval | 47,6% win+tie di un modello sul confronto con esperti (occupazione) | sospeso: manca il collegamento a task |
| METR | durata dei task per modelli, su task non O\*NET | non collegato |
| Microsoft (arXiv 2507.07935) | applicabilità GenAI per attività O\*NET | solo contesto |
| ILO WP140, INAPP WP125 | esposizione per occupazione o per Atlante | letti o non raggiungibili |

Il registro fonti è `docs/ricerca/fonti.csv`. Le licenze sono da verificare per GDPval, WORKBank, METR e Microsoft; per O\*NET, Atlante ed ESCO sono confermate dal responsabile il 2026-10-10, ma il testo della licenza va ancora allegato.

## 4. Che cosa non sappiamo
- **Se k e r predicono la necessità di intervento umano.** Abbiamo solo la coerenza di direzione con una fonte di capacità.
- **Quali pesi e soglie usare.** Nessuno è approvato. Con pesi e soglie diversi cambiano i quadranti.
- **La calibrazione di N.** Non c'è alcun confronto diretto fra il punteggio N e un risultato osservato.
- **La rappresentatività.** Le fonti coprono in parte i task O\*NET, e i 538 task WORKBank non sono un campione casuale.
- **La stabilità della stima.** La maggior parte dei task ha un solo campione per voce, e non abbiamo misurato la dispersione fra campioni sull'intero insieme.

## 5. Decisioni aperte per il responsabile metodologico
1. Budget della raccolta e della verifica (piano, riga 653).
2. Sostituzione della regola di divergenza a 5 campioni nella coda di revisione (piano, riga 563).
3. Ancore di Ae: l'ipotesi va confermata, sostituita, o si attende una risposta degli autori.
4. Licenze di GDPval, WORKBank, METR e Microsoft.
5. Approvazione delle mappe di scala (`config/mappe_scala.json`). Solo GDPval è approvata, ma è sospesa.
6. Regola per la coerenza fra task simili, con la soglia di similarità da scegliere.
7. Approvazione formale della rubrica bozza-2.

## 6. Prossimi passi possibili
- Verificare la stabilità: rieseguire un sottoinsieme con 5 campioni per k2 e r, per misurare la dispersione.
- Controllo di coerenza fra task simili, usando gli embedding già calcolati.
- Collegare GDPval e METR a task O\*NET, con un'analisi a parte sul loro perimetro.
- Persistere il database e i vettori, per non rifare il caricamento a ogni sessione.

## 7. Limiti di questa relazione
- I numeri del punto 3.1 vengono da `STATO.md` (aggiornato al 2026-10-10) e vanno verificati ricaricando, perché il database non è persistente.
- La seconda verifica alla cieca (punto 3.3) non è nel repo: i suoi numeri vengono dalla conversazione.
- La relazione non ricalcola niente: i numeri del punto 3.2 vanno controllati sul file `llm-prior-staff-finale.jsonl` se servono per una decisione.
