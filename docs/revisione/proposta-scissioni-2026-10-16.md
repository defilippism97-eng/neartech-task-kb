# Proposta: cosa fare delle 15 fusioni non corrette (2026-10-16)

Fonte: revisione completa delle 61 fusioni "stessa attività" (`campioni/fusioni-stessa-attivita-2026-10-16.csv`), misura ufficiale 46/61 = 75,4% (intervallo 63,3–84,5%), sotto la soglia di 0,9.

**Criterio usato per le parziali.** La rubrica approvata (`istruzioni-fusioni-v1`) dice che due task sono attività diverse quando uno è chiaramente più ampio e comprende l'altro. In più, se la differenza indicata nella nota riguarda la responsabilità o la relazione, incide su D: anche in quel caso conviene separare. Quando la nota descrive solo una sfumatura di formulazione, conviene tenere la fusione.

## Errate: separazione approvata (3)

| N. | Task da riattivare | Resta nel gruppo di |
|---|---|---|
| 13 | Scansionare e trasmettere documenti a soggetti esterni | Fornire documentazione a revisori, organi di controllo e soggetti esterni autorizzati |
| 26 | Verificare la correttezza e l'aggiornamento dei materiali informativi pubblici e interni | Controllare la qualità dei materiali stampati e digitali |
| 39 | Informare la direzione sul programma e sui risultati degli audit | Elaborare dati e prospetti a fini decisionali, programmatici e di controllo (gruppo di 6 task: gli altri 4 parlano di report e dati per la direzione) |

## Parziali: proposta approvata dal responsabile il 2026-10-16 (12)

| N. | Coppia | Nota del revisore | Proposta | Perché |
|---|---|---|---|---|
| 5 | Prima nota ↔ scritture contabili del ciclo attivo e passivo | il secondo è più ampio | **Separare** | Uno comprende l'altro: per la rubrica sono attività diverse |
| 9 | Richieste del personale su temi contrattuali ↔ fabbisogni dei dipendenti | A più ampio | **Separare** | Uno comprende l'altro |
| 32 | Recupero crediti affidato a legali ↔ pratiche legali affidate a professionisti | B più ampio | **Separare** | Uno comprende l'altro |
| 59 | Allineare informazioni con le funzioni interne ↔ riconciliazione con il controllo di gestione | A più generico, richiede meno competenze | **Separare** | Ampiezza e competenze diverse |
| 33 | Formazione operativa del personale ↔ sviluppo professionale e delle competenze | B legato alla carriera, A adempimento | **Separare** | Responsabilità diversa: incide su D |
| 41 | Gestire il contenzioso extragiudiziale ↔ rappresentare l'ente | rappresentare espone di più | **Separare** | Responsabilità ed esposizione: incide su D |
| 43 | Consultazioni su salute e sicurezza ↔ consultare il rappresentante dei lavoratori | B più relazionale e delicato | **Separare** | Dimensione relazionale: incide su D |
| 55 | Dati sulle attività di prevenzione ↔ report su segnalazioni e infortuni | in B il dato viene creato | **Separare** | Fase diversa del processo, con responsabilità diversa |
| 21 | Supportare l'applicazione dei contratti collettivi ↔ garantirla | A meno enfatico | Tenere fusi | Differenza di formulazione |
| 28 | Adempimenti civilistici del bilancio ↔ redigere i bilanci civilistici | stessa attività, B più diretto | Tenere fusi | Il revisore la indica come stessa attività |
| 49 | Richieste e suggerimenti delle funzioni ↔ fabbisogni dei dipendenti | dipende cosa si intende | Tenere fusi, con nota | Dubbio interpretativo, non una differenza dichiarata |
| 54 | Sintesi economico-finanziaria ↔ report sintetici per la direzione | il destinatario in A non è specificato | Tenere fusi | Differenza di destinatario non essenziale |

## Effetti di ogni separazione

- Il task riattivato torna `active`, con le sue occorrenze ricostruite dalla scomposizione approvata dell'11 ottobre (`docs/dati/scomposizione-approvata-2026-10-11.jsonl`), sia in `public` sia in `org_societa_dolce`.
- Il crosswalk verso le tassonomie del task riattivato era stato cancellato dalla fusione: va rifatto, con chiamate API e quindi con una stima dei costi prima.
- Il task riattivato parte con stato di validazione `da_integrare`.
- Ogni separazione è un atto nel registro (correzione), e il Canonicalizer non rifonde più le coppie che un revisore ha giudicato errate.

## Esito (2026-10-16)

Eseguite in produzione le 11 separazioni (3 errate, 8 parziali): task attivi da 295 a 306. Ogni separazione è un atto di correzione nel registro (ancore in `docs/audit/ancore-registro.md`, posizioni 14 e 22). Restano fuse le coppie 21, 28, 49, 54.

**Da rivedere in seguito:** nel gruppo di "Gestire i rapporti con consulenti legali esterni" restano fusi "Collaborare alla gestione del recupero crediti con l'ufficio legale o agenzie esterne" e "Gestire la riscossione dei crediti", che non erano nel campione e sembrano più vicini al task separato sul recupero crediti che ai rapporti con i consulenti legali.
