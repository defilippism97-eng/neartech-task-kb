# Estensioni operative alla metodologia (piano V2)

Questo documento registra le scelte operative prese durante l'implementazione che il piano V2 non prevedeva
o prevedeva in modo diverso. Ogni voce indica la data, il motivo e l'approvazione.

## 1. Task senza corrispondenza nelle tassonomie (2026-10-12, approvato)

Un task che il crosswalk non collega a nessun nodo delle tassonomie ufficiali **resta nella knowledge base**.
- Il giudizio "nessuna corrispondenza" è registrato per task e per schema in `crosswalk_giudizi` (esito `nessuna`).
- L'origine del task è visibile in `v_task_origine` (fonti da cui proviene, es. "Job Società Dolce", e numero di relazioni con le tassonomie).
- Scopo: alimentare il ciclo dei dati nel tempo. I task non presenti nelle tassonomie principali sono il materiale
  per nuove fonti di secondo livello, e vanno aggregati con task simili provenienti da altre fonti per ampliare lo
  spazio semantico della knowledge base.

## 2. Aree di responsabilità non sono task (2026-10-12, approvato)

Le voci di granularità 3 (aree di responsabilità) sono insiemi di task, non task. Sono ritirate (`status = retired`),
escluse dal crosswalk e dal Canonicalizer. Le loro relazioni con le tassonomie sono state eliminate.
Se le aree non rappresentano correttamente l'insieme dei task sottostanti, la nomenclatura va corretta nelle job description:
per ora si ignora la questione.

## 3. Canonicalizer: fusione dei task equivalenti (2026-10-12, approvato)

- Per ogni task attivo di granularità 1 o 2 si confrontano i **5 task più vicini** per embedding. Non si usano soglie di similarità:
  il numero di vicini è un parametro di recupero, le decisioni le prende il modello.
- Il modello decide per ciascun vicino: `stessa_attivita` oppure `diversa`, con una motivazione. Ogni decisione è registrata
  in `fusioni_proposte` e non viene sovrascritta.
- Le coppie `stessa_attivita` vengono fuse per chiusura transitiva. Il task superstite è quello con più occorrenze.
  Gli altri diventano `merged` e puntano al superstite: occorrenze e relazioni vengono spostate, senza perdere i passi originali.
- Il piano prevede una revisione a campione del curatore sulle fusioni. Le fusioni sono state applicate prima di quella
  revisione, su indicazione del responsabile del progetto; il campione va comunque estratto e verificato (vedi `STATO.md`).

## 4. Revisione del crosswalk (2026-10-12)

- Gli esiti della revisione umana sono registrati in `revisioni_crosswalk` (un record per relazione, mai sovrascritto).
- Solo le relazioni confermate dal revisore sono marcate `validated = true`.
- Le relazioni dubbie vengono mantenute come proposte, senza correzione automatica, finché il revisore non indica quella corretta.
