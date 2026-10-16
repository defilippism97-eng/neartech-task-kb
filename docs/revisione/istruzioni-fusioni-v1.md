# Istruzioni di revisione: fusioni del Canonicalizer (versione `istruzioni-fusioni-v1`)

**Stato: bozza, da approvare.** Una rubrica di revisione è una decisione di governance: questa versione entra in uso solo dopo l'approvazione del responsabile del progetto, registrata in `docs/metodologia-estensioni.md`. Il codice della versione (`istruzioni-fusioni-v1`) va indicato in ogni campione e in ogni giudizio.

## Cosa si rivede

Coppie di task del dataset consolidato su cui il Canonicalizer ha deciso se descrivono la stessa attività. Per ogni coppia vedete i due titoli e la proposta del sistema ("stessa attività" oppure "attività diverse"). Non vedete la motivazione né il modello: la revisione è cieca rispetto al ragionamento del sistema.

## Definizione

Due task sono **la stessa attività** quando descrivono lo stesso compito di lavoro: stesso risultato e stesso oggetto, anche con parole diverse. Sono **attività diverse** quando cambiano il risultato o l'oggetto, anche se sono affini, o quando uno dei due è chiaramente più ampio e comprende l'altro.

## Esiti

| Esito | Quando |
|---|---|
| `corretto` | La proposta del sistema è giusta. |
| `parziale` | La proposta non è sbagliata ma è imprecisa: per esempio i task si sovrappongono molto ma uno è più ampio, o la differenza dipende dal contesto dell'organizzazione. Scrivete il motivo nella nota. |
| `errato` | La proposta del sistema è sbagliata. Scrivete nella nota quale sarebbe stata la decisione giusta. |

Come conta "parziale" nella precisione non lo decidete voi: lo fissa il parametro `regola_parziali` (oggi: conta come errore, decisione del 2026-10-16).

## Regole pratiche

- Giudicate la coppia così come è scritta, senza cercare il documento di origine.
- Un dubbio non risolto è un `parziale` con nota, non un `corretto`.
- Se cambiate idea, registrate un nuovo giudizio: il precedente resta nello storico e conta l'ultimo.
- Se due revisori danno esiti diversi, il calcolo della metrica si ferma finché non concordate.

## Campioni previsti per il pilota (decisione del 2026-10-16)

1. Tutte le 61 coppie proposte come "stessa attività" (criterio `tutte`).
2. Un campione casuale, con seme registrato, delle 1.684 coppie proposte come "attività diverse". La dimensione la decide chi crea il campione e resta registrata.
