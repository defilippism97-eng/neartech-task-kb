# Set di controllo del prompt v2 del Canonicalizer (2026-10-17)

Esecuzione approvata dal responsabile del progetto. Script: `scripts/controllo_canonicalizer.py`. Nessuna scrittura nel database.

- **Campione:** le 61 fusioni "stessa attività" della prima esecuzione, giudicate dal responsabile (campione `86199f1e-ca89-42d3-af9e-b5837b3675c1`: 46 corrette, 12 parziali, 3 errate).
- **Chiamate:** 59, una per task di riferimento, con gli stessi 5 vicini della prima esecuzione. 295 giudizi.
- **Modello e prompt:** `claude-haiku-5-5`, `prompt_hash` `f72fc194015ea806e1a8b29d614e220dfcc084b04fe262b0e167ba85c7fbcd7d`.
- **Consumo:** 39.099 token in ingresso e 57.692 in uscita. La stima era ~30.000 e ~18.000: il modello scrive molto più della sola risposta JSON.
- **Dati:** `canonicalizer-v2-2026-10-17.jsonl`, una riga per giudizio. Riepilogo in `canonicalizer-v2-2026-10-17.jsonl.riepilogo.json`.

## Esito

| | v1 | v2 |
|---|---|---|
| Proposte "stessa attività" sulle 61 coppie | 61 | 17 |
| Precisione (parziali come errori, parametro vigente) | 75,4% | **82,4%** (14/17; intervallo di Wilson al 95%: 59,0–93,8%) |
| Fusioni corrette mantenute | 46/46 | **14/46** |
| Fusioni parziali o errate respinte | 0/15 | 12/15 (10 parziali, 2 errate) |

Sulle altre 234 coppie, una sola passa da "diversa" a "stessa attività": "Elaborare dati e prospetti a fini decisionali, programmatici e di controllo" e "Predisporre report periodici a supporto delle decisioni strategiche e delle verifiche di conformità".

Restano proposte sbagliate da v2:
- parziale: "Collaborare con le funzioni interne per allineare le informazioni contabili" e "Collaborare con il controllo di gestione alla riconciliazione dei dati economico-finanziari";
- errata: "Controllare la qualità dei materiali stampati e digitali" e "Verificare la correttezza e l'aggiornamento dei materiali informativi pubblici e interni";
- parziale: "Coordinare le pratiche di recupero crediti affidate a legali esterni" e "Coordinare le pratiche legali affidate a professionisti esterni".

## Lettura

Il prompt v2 **non supera il controllo**: la precisione resta sotto la soglia di 0,9, e l'intervallo, su sole 17 proposte, è largo. Il prompt è diventato molto più prudente: respinge quasi tutte le fusioni sbagliate, ma anche 32 delle 46 corrette. Il Canonicalizer non va eseguito con questa versione. Serve una versione 3 che recuperi le fusioni corrette (stesso compito con formulazioni diverse) senza riaprire le distinzioni fra esecuzione e responsabilità, seguita da un nuovo set di controllo.
