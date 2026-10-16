# Piano di ricerca per le evidenze di N

Perimetro: tutti i ruoli di staff in azienda, non solo i servizi alla persona.
Fonti: quelle del piano V2. Gli studi su D si registrano quando emergono, ma non si cercano
fuori dalle fonti del piano in questa fase.

## Obiettivo

Un insieme di evidenze per task O\*NET, ciascuna con: fonte e pagina, data, tipo di evidenza,
dimensione (k1, k2, k3 o `any`), valore convertibile su 0–4, collegamento esatto a un nodo.

## Stato

| Fonte | Tipo di dato | Collegamento | Stato |
|---|---|---|---|
| WORKBank | Ae di esperti (capacità), Aw e Hw (D) | task O\*NET (ID) | 6 record estratti; scala di Ae da verificare |
| Anthropic Economic Index | uso per task, MIT | testo esatto: 17.033 exact, 403 ambigui, 562 senza | script pronto; contesto, non capacità |
| GDPval | confronto modello-esperto su 220 task gold, 44 occupazioni | solo occupazione | 1 record: 47,6% win+tie di Claude Opus 4.1; collegamento task mancante |
| METR | durata dei task | — | repository non leggibile da questo ambiente |
| Microsoft (arXiv 2507.07935) | applicabilità per attività O\*NET | ID O\*NET nel dataset | dataset non leggibile da questo ambiente |
| ILO WP140 | esposizione per occupazione ISCO-08 | occupazione | letto; non estratto |
| INAPP WP125 | esposizione Atlante | ADA | sito non raggiungibile; scarico manuale |

## Decisioni da approvare

1. **Mappe di scala** (`config/mappe_scala.json`): nessuna è approvata.
   - Uso osservato (AEI): nessuna conversione a capacità, resta contesto.
   - GDPval: proposta `score_0_4 = 4 × quota win+tie`, bloccata finché manca il collegamento a task.
   - WORKBank Ae: bloccata finché non si legge la scala nell'appendice B.
2. **Collegamento GDPval a task.** Serve la classificazione per task O\*NET che il paper dice
   di aver fatto (sezione 2): probabilmente nel set completo di 1.320 task, non nel dataset pubblico.
3. **Licenze** di GDPval, WORKBank, METR e Microsoft: da verificare.

## Come si riproduce

- AEI: `python scripts/estrai_aei.py --penetration <task_penetration.csv> --onet31 <Task Statements.txt> --out <file>`
  Il file generato non è nel repository (circa 18.000 righe): si ricostruisce dalla fonte.
- Test: `pytest tests/test_estrai_aei.py`.
