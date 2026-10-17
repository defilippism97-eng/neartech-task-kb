# Fase 6: la piattaforma per le aziende pilota

**Stato:** bozza, da approvare dal responsabile del progetto (2026-10-17). Stack: ADR 0007. Bozze delle schermate: `docs/piattaforma/mockup.html`.

## Perché

Le fasi 1–5 hanno costruito il motore: base di conoscenza, abbinamento, calcolo di N e D, restituzione, governance con registro. Oggi si usa con gli script. La fase 6 lo porta in superficie con una piattaforma web per le aziende pilota.

**Strategia (decisa dal responsabile):** la validazione avviene dentro il prodotto. Le aziende pilota sanno di essere in sperimentazione; ogni giudizio dei revisori e ogni questionario raccolto nella piattaforma sostituisce la stima del modello, e il calcolo toglie da solo lo stato "provvisorio" voce per voce. Gli avvisi restano visibili, ma come **avanzamento della sperimentazione** e invito all'azione ("conferma questi 41 risultati"), mai come blocco.

## Il principio di esperienza

Una piattaforma, un punto di vista per ogni ruolo della metodologia. Ogni ruolo entra in una home costruita attorno alle **sue decisioni**, non a un menu comune. Nessun ruolo nuovo: si usano quelli esistenti.

| Ruolo | Decisione principale | Home | Azioni |
|---|---|---|---|
| Comitato guida | Accettare la lettura dei ruoli e le regole del gioco | Mappa dei quadranti, ruoli, avanzamento della sperimentazione | Approva la restituzione (impronta), adotta o ricalibra parametri, emana indirizzi, prepara e chiude i questionari, nomina il rappresentante dei lavoratori |
| Revisore | Questa proposta è giusta? Quanto vale questo task? | "Il mio lavoro": coda e valutazione sulla rubrica | Giudica abbinamenti e campioni, decide e applica i lotti, dà i giudizi sulla rubrica (k1–k3, r, d1, d2) che sostituiscono quelli del modello |
| Rappresentante dei lavoratori (facoltativo) | Questa riduzione di D va portata al comitato? | Variazioni di D dell'ultimo calcolo | Accetta la variazione, oppure la sospende e la porta al comitato |
| Amministratore NEARTECH | Il pilota procede? | Organizzazioni, pipeline dei documenti, costi | Crea l'organizzazione, carica i mansionari, avvia scomposizione, abbinamento e calcolo, assegna i ruoli |
| Auditor | Il processo è integro? | Catena del registro e report di audit | Sola lettura, esporta il report |

**Chi risponde ai questionari** (lavoratori per d3, beneficiari o chi li rappresenta per d4) non ha un account né un ruolo: riceve un'email con un link monouso.

Più una **pagina pubblica** che presenta il metodo e raccoglie le candidature delle aziende pilota.

Regole valide ovunque:
- **Ogni dato dichiara da dove viene** (identità visiva: `giudicato da persone`, `stima del modello`, `nuovo`), sempre con testo, mai solo colore.
- **Nessun output riguarda una persona.** Le risposte ai questionari si leggono solo aggregate, con almeno N rispondenti per gruppo (parametro di governance `minimo_rispondenti_gruppo`, il piano indica 5).
- **Ogni azione diventa un atto nel registro**, tramite le funzioni del motore; i permessi passano da `richiedi`; i testi dell'organizzazione restano in `org_<codice>`.

### Il revisore valuta anche sulla rubrica

Il revisore è anche il valutatore della rubrica: non c'è un ruolo "esperto" separato. Nella sua home ha due modi di lavoro: la **coda** (abbinamenti e risultati incerti, dal più incerto) e la **valutazione sulla rubrica** (un task alla volta, la scala con gli esempi, la stima del modello visibile come riferimento). Dalla coda un risultato incerto porta direttamente alla sua valutazione. I giudizi si registrano come giudizi di persona (`rater_kind = 'expert'`) e prevalgono su quelli del modello nel calcolo.

### I questionari nel flusso del metodo

1. **Domande:** la piattaforma propone il questionario a partire dai task di una famiglia professionale (al massimo 12, con la domanda della rubrica per d3 o d4). Il comitato guida le rivede e le approva.
2. **Destinatari:** il comitato carica gli indirizzi email. Gli indirizzi restano nello spazio dell'organizzazione, separati dalle risposte; servono solo all'invio e ai promemoria.
3. **Invio:** la piattaforma invia l'email con un link monouso che non contiene l'identità.
4. **Risposte:** pseudonimizzate alla raccolta; visibili solo per gruppi sopra il minimo di rispondenti.
5. **Ricalibrazione:** alla chiusura della campagna (atto del comitato), la piattaforma registra per ogni task il giudizio aggregato del gruppo come giudizio di persona (`worker` per d3, `beneficiary` per d4) e ricalcola N e D. I risultati della campagna tornano a chi ha risposto.

### Il rappresentante dei lavoratori

Facoltativo. Lo nomina il comitato guida, anche fra i propri membri, senza vincoli. Se nessuno è nominato, la vista non compare. Quando un calcolo abbassa D di un task, il rappresentante può accettare la variazione o sospenderla: resta vigente il D precedente finché il comitato decide. Il tono è quello di una verifica di qualità sulla desiderabilità, non di un veto.

## Canali

- **Primario:** desktop e laptop per comitato, revisore, amministratore, auditor (lavoro analitico, seduto, spesso in riunione: la dashboard del comitato regge la proiezione su schermo 16:9).
- **Email e smartphone verticale:** questionari (operatori in turno, pochi minuti).
- **Stampa e PDF:** la restituzione approvata, per il consiglio di amministrazione.

## Che cosa esiste e che cosa manca nel motore

| Schermata | Funzioni esistenti | Da aggiungere |
|---|---|---|
| Dashboard del comitato e restituzione | `restituzione_organizzazione`, `approva_restituzione`, `parametri_comuni`, `adotta_parametro_comune`, `chiedi_ricalibrazione`, `proponi_indirizzo`/`approva_indirizzo` | Avanzamento della sperimentazione per voce (giudizi di persona sul totale); storico delle restituzioni approvate |
| Revisore: coda | `coda_revisione`, `imposta_livello`, `crea_campione_del_lotto`, `esporta_campione`, `registra_giudizio`, `decidi_lotto`, `applica_lotto`, `imposta_stato`, `calcola_precisione` | Coda unica che unisce abbinamenti e occorrenze instabili della restituzione |
| Revisore: rubrica | rubrica corrente, `assessment_runs` con `rater_kind = 'expert'`, calcolo che già fa prevalere le persone, permesso `giudicare_task` del revisore | Funzione `registra_giudizio_rubrica` con atto nel registro e nota nello spazio; distribuzione dei task da valutare fra i revisori |
| Questionari d3/d4 | voci d3 e d4 in `assessment_runs`, `rater_kind` `worker` e `beneficiary` | Campagne, destinatari, inviti monouso, risposte pseudonimizzate (migrazione, tabelle nello spazio dell'organizzazione); invio email; aggregazione e registrazione del giudizio di gruppo; permessi del comitato per preparare e chiudere le campagne |
| Rappresentante dei lavoratori | ruolo `rappresentante_lavoratori`, permesso `bloccare_ribasso`, atto `blocco` nel registro | Nomina da parte del comitato (permesso nuovo al comitato guida); rilevazione delle riduzioni di D fra due calcoli; sospensione con atto; effetto della sospensione sul calcolo |
| Amministratore | `crea_organizzazione`, `assegna_ruolo`, scomposizione, `proponi_abbinamenti`, `calcola_organizzazione`, coda dei job `neartech.coda` | Worker che esegue i job; caricamento dei documenti dal browser; stima dei costi prima delle chiamate a pagamento (la conferma resta umana) |
| Auditor | `report_organizzazione`, `verifica_catena` | Solo esposizione |

## Costruzione, a fette consegnabili

Ogni fetta: API con test, schermate con test, revisione (Python, database, sicurezza, accessibilità), PR verso `main` con approvazione del responsabile.

0. **Fondamenta** (ADR 0007): applicazione FastAPI con accesso SSO e sessione, connessione per richiesta e log di accesso dedicato; frontend con il sistema di design derivato da `docs/identita/`; CI su GitHub; ambiente di prova su un ramo Neon. Pagina pubblica.
1. **Comitato guida:** dashboard dei quadranti e dei ruoli, restituzione con avvisi come avanzamento, approvazione con impronta, parametri e adozioni.
2. **Revisore:** coda unica, campioni, lotti; valutazione sulla rubrica. Da qui gli avvisi "provvisorio" iniziano a scendere.
3. **Questionari d3/d4:** preparazione, invio email, risposta da telefono, aggregazione, ricalibrazione, restituzione ai partecipanti.
4. **Rappresentante, amministratore, auditor:** nomina e variazioni di D; pipeline dei documenti con il worker; registro e audit.

## Test

- API: test con il database di prova come oggi (`tests/`), un test per ogni permesso negato.
- Frontend: test dei componenti; **end to end** con Playwright sui percorsi critici (approvare una restituzione, decidere un lotto, dare un giudizio sulla rubrica, rispondere al questionario).
- Accessibilità: WCAG 2.2 AA, controllo automatico nella CI e verifica da tastiera.

## Esercizio

- **Ospitalità in UE**, database Neon già in UE; ambiente di **prova** su un ramo Neon separato dalla produzione, con dati sintetici.
- **Email:** un servizio di invio con server in UE, mittente verificato per dominio.
- **CI su GitHub:** test Python con PostgreSQL e pgvector, test e build del frontend, end to end, a ogni PR.
- **Backup:** ripristino puntuale di Neon e prova di ripristino periodica documentata.

## Decisioni del responsabile

1. Approvazione di questo piano, delle bozze e dell'ADR 0007.
2. Coppia di caratteri (Inter + JetBrains Mono oppure Geist + Geist Mono): oggi Inter, cambio di un solo token.
3. Fornitore di ospitalità in UE (proposta nell'ADR 0007).
4. Questionari, regole di metodo: come si aggrega il gruppo in un giudizio (proposta: mediana delle risposte sulla scala 0–4); se il giudizio del gruppo sostituisce o si affianca a una stima del modello su d3/d4 (proposta: sostituisce, come gli altri giudizi di persona); `minimo_rispondenti_gruppo` (il piano indica 5).
5. Sospensione di una riduzione di D: resta vigente il D precedente fino alla decisione del comitato (proposta).
