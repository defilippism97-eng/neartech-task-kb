# Carenza di evidenze di capacità per N

Traccia lo stato di copertura del calcolo di N. Ogni promozione di un dato di contesto a N
va registrata qui, con la ragione e la fonte.

## Stato al 2026-10-11

| Fonte | Livello | Evidenza di capacità a livello di task | Nodi coperti |
|---|---|---|---|
| WORKBank (Ae, esperti) | task | sì, ma scala di Ae da verificare | 0 con score (bloccata) |
| GDPval (win+tie) | occupazione | no, collegamento task mancante | 0 |
| AEI (uso) | task | solo uso, classificato contesto | 17.033 exact (non in N) |
| METR (run 1.0 e 1.1) | task METR, non O\*NET | sì come capacità del modello, ma nessun collegamento a un nodo | 0 |
| Microsoft (IWA e SOC) | uso osservato | solo uso, contesto | 0 (contesto) |
| ILO, INAPP | occupazione / ponte | non estratti / non raggiungibili | 0 |

Dati raggiunti tramite raw.githubusercontent.com: METR e Microsoft sono ora scaricati. Nessuno dei due
collega a un task O\*NET per ID, quindi restano fuori da N finché non c'è un ponte.

**Risultato:** oggi nessun nodo O\*NET ha un'evidenza di capacità utilizzabile per N.
La carenza è totale. Ogni copertura futura parte da zero e va documentata.

## Regole di promozione

1. Un dato di contesto (uso osservato) entra in N solo dopo che le fonti di capacità
   sono esaurite per quel nodo.
2. Ogni promozione è una riga in questa tabella: nodo, fonte, motivo, data, approvazione.
3. Il valore promosso è marcato `promosso da uso osservato` e pesa di meno nel calcolo
   (il peso è una scelta di governance, non nel codice).
