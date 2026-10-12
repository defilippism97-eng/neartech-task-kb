# Verifica di coerenza con WORKBank (Ae)

Stato: **preliminare, non calibrato**. Il confronto è di rango e non modifica nessun punteggio.

## Fonte

- WORKBank, Shao et al. 2025, arXiv 2506.06576, dataset `SALT-NLP/WORKBank` su Hugging Face.
- File usati: `expert_ratings/expert_rated_technological_capability.csv` (2.057 valutazioni, 846 task, Ae su scala 1–5) e il codebook.
- Accordo fra esperti: α = 0,539 per Ae (appendice B.1). È un tetto alla correlazione osservabile.
- **Licenza non dichiarata** sulla scheda del dataset: il file grezzo non è committato nel repo.

## Scala di Ae

Nel testo dell'articolo e nel codebook non ci sono le ancore 1–5 di Ae, solo "scala Likert a 5 punti" e le frequenze per valore. Per questo:

- il confronto usa la **correlazione di Spearman**, invariante a una mappa monotona come v−1;
- la conversione di Ae a 0–4 resta **bloccata** (già indicata in `config/mappe_scala.json`).

## Risultato

Sovrapposizione con la stima preliminare: **538 task** su 846 (tutti i quattro punteggi presenti). Ae per task = media delle valutazioni esperte. Punteggio per voce = media dei campioni: cinque campioni per k1 e k3 nei 739 task della prima fase, un campione per ogni voce negli altri 2.344 task.

| Voce | ρ di Spearman con Ae medio | Atteso | Lettura |
|---|---|---|---|
| k1 (variabilità dell'input) | −0,235 | negativo | coerente |
| k2 (giudizio) | −0,289 | negativo | coerente |
| k3 (componente fisico-percettiva) | +0,070 | debole | non distinguibile da zero a questo n |
| r (criticità) | −0,049 | ~0 | coerente: r misura conseguenze, non capacità |
| somma k1+k2+k3 | −0,279 | negativo | coerente |

Errore standard approssimato con n = 538: ±0,043. k1 e k2 sono distanti da zero di circa cinque–sei errori standard. Il tetto dato dall'accordo fra esperti (√0,539 ≈ 0,73) è ben sopra i valori osservati.

## Cosa questo non dice

- Non è una calibrazione di N: la stima preliminare non ha ancora i pesi del profilo approvato, quindi il confronto riguarda le singole voci k e r, non il punteggio N.
- Il segno atteso è negativo perché k misura difficoltà e Ae misura capacità. Il confronto verifica la direzione, non l'ampiezza.
- Il campione di 538 task è quello in comune con O\*NET; gli esperti sono 52 e il loro accordo è moderato.
- La licenza del dataset è da verificare prima di qualunque uso pubblico dei dati grezzi.

## Decisioni per il responsabile metodologico

1. **Approvata** dal responsabile metodologico (2026-10-12): la correlazione di rango è il criterio di coerenza con WORKBank, in attesa delle ancore di Ae.
2. Chiedere agli autori le ancore 1–5 di Ae, necessarie per la conversione a 0–4: non compaiono né nel paper né nel codebook.
3. Verificare la licenza di WORKBank prima di conservare i dati grezzi nel repo.

Script riproducibile: `scripts/confronta_workbank.py <percorso del CSV delle valutazioni esperte>`.
