# Piano: Fase 2, metrica di abbinamento sul campione rivisto

**Branch:** `fase-2-metrica` (da `fondazioni`). **Riferimenti:** `docs/HANDOVER.md` sezioni 3, 4 e 9; ADR 0001–0003.
**Complessità:** media. Nessuna chiamata a modelli a pagamento. Nessuna scrittura in produzione senza approvazione.

## 1. Obiettivo

Misurare, in modo deterministico e ripetibile, quanto sono corrette le proposte del sistema rispetto al giudizio di una persona, prima di qualunque altra metrica. La soglia (oggi 90% nel piano) è un parametro di governance, non una costante.

La stessa infrastruttura serve tre tipi di proposta:

| Tipo | Proposta | Esiste oggi |
|---|---|---|
| `crosswalk` | task canonico → nodo di tassonomia | sì: 5.672 collegamenti, 40 rivisti da persone |
| `fusione` | task canonico ↔ task canonico (Canonicalizer) | sì: 1.745 giudizi del modello, 61 "stessa attività", nessuno rivisto |
| `abbinamento` | task dell'organizzazione → task del dataset consolidato | no: lo produce la fase 3 |

## 2. Requisiti

1. **Campioni di revisione.** Un campione estrae, con seme registrato, elementi da un insieme di proposte. Metodo e dimensione vengono da parametri di governance. Il campione è registrato nel registro delle decisioni e non si modifica.
2. **Revisione cieca.** Il revisore vede la coppia proposta senza la motivazione né la fiducia del modello. Esportazione in JSONL o CSV per chi rivede fuori dal sistema; importazione dei giudizi.
3. **Giudizi.** Un record per giudizio: esito `corretto`, `parziale` o `errato`, nota, revisore, versione delle istruzioni di revisione. Un ripensamento è un record nuovo.
4. **Calcolo deterministico.** Precisione con la regola sui parziali presa da un parametro; intervallo di confidenza con il livello preso da un parametro; confronto con la soglia presa da un parametro. Senza parametri approvati il calcolo si ferma (`ParametroAssente`).
5. **Disaccordi.** Se due revisori danno esiti diversi sullo stesso elemento, il calcolo si ferma e li elenca: nessuna regola di risoluzione inventata dal codice.
6. **Risultati con le loro chiavi.** Ogni misura registra campione, parametri usati (id e versione), modello e versione del prompt che hanno prodotto le proposte, versione del codice di calcolo. Append-only.
7. **Dati esistenti.** Il campione del crosswalk (`revisioni_crosswalk`, 40 giudizi) si importa come primo campione misurabile, con uno script che in produzione gira prima in sola lettura.

## 3. Passi (test prima del codice)

1. Migrazione `0018`: `campioni_revisione`, `elementi_campione`, `giudizi_revisione`, `misure_precisione`, tutte append-only; permesso `gestire_campioni` ai revisori.
2. `neartech.campioni`: creazione del campione con seme, esportazione cieca, importazione e registrazione dei giudizi.
3. `neartech.metrica`: calcolo della precisione e dell'intervallo, confronto con la soglia, registrazione della misura.
4. Adattatori per i tre tipi di proposta (crosswalk e fusione subito; abbinamento come interfaccia per la fase 3).
5. `scripts/metrica.py`: crea campione, esporta, importa giudizi, calcola. `scripts/importa_revisioni_crosswalk.py` con `--dry-run`.
6. Revisioni Python e database; aggiornamento di handover, ADR e registro di metodo.

## 4. Decisioni del responsabile (2026-10-16, `docs/metodologia-estensioni.md` sezione 9)

1. Parametri comuni: li propone e approva l'amministratore tecnico (permessi `proporre_parametro_comune`, `approvare_parametro_comune`).
2. Parziali: contano come errori (parametro comune `regola_parziali`).
3. Primo campione: le 61 fusioni "stessa attività" in revisione completa, più un campione casuale delle "diversa".
4. Revisione iniziale dei task nuovi: a campione, quota come parametro (fase 3).

## 5. Rischi

| Rischio | Mitigazione |
|---|---|
| Il campione del crosswalk misura il collegamento alle tassonomie, non l'abbinamento al dataset | Dichiararlo nella misura (tipo di proposta) e non presentarlo come metrica di abbinamento |
| Campioni piccoli (40) danno intervalli larghi | Riportare sempre l'intervallo, non solo la precisione |
| Revisione non cieca se il revisore vede la motivazione del modello | Esportazione senza motivazione e fiducia |
