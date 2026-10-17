# Fase 6: la piattaforma per le aziende pilota

**Stato:** bozza, da approvare dal responsabile del progetto (2026-10-17). Stack: ADR 0007. Bozze delle schermate: `docs/piattaforma/mockup.html`. Decisioni di metodo: registro di metodo, sezione 27.

## Perché

Le fasi 1–5 hanno costruito il motore: base di conoscenza, abbinamento, calcolo di N e D, restituzione, governance con registro. Oggi si usa con gli script. La fase 6 lo porta in superficie con una piattaforma web per le aziende pilota.

**Strategia (decisa dal responsabile):** la validazione avviene dentro il prodotto. Le aziende pilota sanno di essere in sperimentazione; ogni giudizio dei revisori, ogni indirizzo del comitato e ogni questionario raccolto nella piattaforma sostituisce la stima del modello, e il calcolo toglie da solo lo stato "provvisorio" voce per voce. Gli avvisi restano visibili come **avanzamento della sperimentazione** e invito all'azione ("conferma questi 41 risultati"), mai come blocco.

## Il flusso per un'impresa

| # | Passo | Chi | Nel motore |
|---|---|---|---|
| 1 | Le job description vengono scomposte in task | sistema | esiste |
| 2 | Ogni task viene abbinato, se possibile, al database NEARTECH | sistema | esiste |
| 3a | Abbinato: eredita il punteggio del task del database | sistema | esiste |
| 3b | Non abbinato: media dei task più simili del database, pesata per somiglianza, marcata "derivato per somiglianza"; entra nel database come task nuovo | sistema | da costruire |
| 4 | Il comitato guida vede i task (fino al singolo), ma agisce soprattutto con gli **indirizzi** e i parametri di alto livello, partendo da quelli di default | comitato | parametri esistono; indirizzi solo testuali |
| 5 | Gli indirizzi si raccolgono con interviste e questionari strutturati sulla visione dell'innovazione dell'impresa e producono il **profilo di pesi di D** dell'organizzazione (w_d1–w_d4, ed enfasi per classi di task se serve). Il profilo diventa vigente con l'**approvazione del comitato e l'ok dell'auditor**. Gli indirizzi danno enfasi solo sopra il pavimento legale, mai sotto | comitato, auditor | da costruire |
| 6 | Con D calibrato, il sistema aggiorna la classificazione di tutti i task | sistema | esiste (calcolo) |
| 7 | I revisori controllano le classificazioni a campione | revisori | esiste (campioni e misura) |
| 8 | La correzione di un revisore vale per quel task in tutte le sue occorrenze. Uno scostamento sistematico nel campione diventa una proposta di ricalibrare i pesi, segnalata al comitato | sistema, comitato | in parte |
| 9 | Il comitato vede l'esito finale e approva la restituzione | comitato | esiste |

L'auditor segue ogni fase; l'amministratore tecnico la segue e può intervenire. Nel database NEARTECH restano solo dati anonimi; log e azioni restano nella sezione dell'impresa, per l'audit (ADR 0001, 0004, 0005).

## I ruoli e le loro viste

Nessun ruolo nuovo: si usano quelli esistenti.

| Ruolo | Decisione principale | Home | Azioni |
|---|---|---|---|
| Comitato guida | Quale visione dell'innovazione vale per noi? Accettiamo il risultato? | Panoramica: mappa dei quadranti, avanzamento della sperimentazione, indirizzi | Questionario degli indirizzi, approvazione del profilo di pesi, parametri, questionari d3/d4, approvazione della restituzione |
| Revisore | Questa proposta è giusta? Quanto vale questo task? | "Il mio lavoro": coda e valutazione sulla rubrica | Giudica abbinamenti e campioni, decide e applica i lotti, dà i giudizi sulla rubrica (k1–k3, r, d1, d2), segnala ricadute anomale degli indirizzi |
| Auditor | Il processo è integro? Il profilo rispetta i limiti? | "Da verificare", registro, report di audit | Dà l'ok al profilo di pesi dell'organizzazione (o chiede chiarimenti); per il resto sola lettura |
| Amministratore tecnico | Il pilota procede? | Organizzazioni, pipeline, costi | Carica i mansionari, avvia scomposizione, abbinamento e calcolo, assegna i ruoli, attiva la vista del rappresentante, interviene sul processo |
| Rappresentante dei lavoratori (vista bonus) | Questa riduzione di D va riportata al comitato? | Variazioni di D dovute agli indirizzi | Accetta, oppure sospende e riporta al comitato |

**Il revisore valuta anche sulla rubrica:** non c'è un ruolo "esperto". Due modi di lavoro, la coda (dal più incerto) e la valutazione sulla rubrica; i giudizi si registrano come giudizi di persona (`rater_kind = 'expert'`) e prevalgono su quelli del modello.

**La vista del rappresentante** è invisibile finché l'amministratore tecnico non la attiva per l'organizzazione; allora il comitato nomina chi la usa, anche fra i propri membri. Tono di verifica, non di veto.

**Chi risponde ai questionari d3/d4** (lavoratori, beneficiari o chi li rappresenta) non ha account né ruolo: riceve un'email con un link monouso.

Più una **pagina pubblica** che presenta il metodo e raccoglie le candidature delle aziende pilota.

Regole valide ovunque:
- **Ogni dato dichiara da dove viene**: `giudicato da persone`, `stima del modello`, `derivato per somiglianza`, `nuovo`; sempre con testo, mai solo colore.
- **Nessun output riguarda una persona.** Le risposte ai questionari si leggono solo aggregate, con almeno N rispondenti per gruppo (parametro `minimo_rispondenti_gruppo`, il piano indica 5).
- **Ogni azione diventa un atto nel registro**, tramite le funzioni del motore; i permessi passano da `richiedi`; i testi dell'organizzazione restano in `org_<codice>`.

### Questionari d3/d4

1. La piattaforma propone il questionario dai task di una famiglia professionale (al massimo 12, con la domanda della rubrica per d3 o d4); il comitato lo approva.
2. Il comitato carica gli indirizzi email, tenuti nello spazio dell'organizzazione e separati dalle risposte.
3. Invio dell'email con link monouso senza identità; promemoria.
4. Risposte pseudonimizzate; visibili solo per gruppi sopra il minimo.
5. Alla chiusura (atto del comitato) il giudizio aggregato del gruppo si registra come giudizio di persona (`worker` per d3, `beneficiary` per d4) e si ricalcola. I risultati tornano a chi ha risposto.

## Canali

- **Primario:** desktop e laptop per comitato, revisore, auditor, amministratore (lavoro analitico, spesso in riunione: la panoramica del comitato regge la proiezione 16:9).
- **Email e smartphone verticale:** questionari d3/d4.
- **Stampa e PDF:** la restituzione approvata.

## Che cosa manca nel motore

| Pezzo | Da aggiungere |
|---|---|
| Task non abbinati (3b) | Classificazione per somiglianza: media pesata dei vicini nel dataset, con origine dichiarata nei giudizi |
| Indirizzi → pesi (5) | Questionario strutturato del comitato (domande versionate); funzione che propone il profilo di pesi dalle risposte; simulazione dell'effetto sui task; approvazione del comitato; **ok dell'auditor** (permesso nuovo all'auditor, migrazione); controllo automatico del pavimento legale e dei pesi a somma uno |
| Feedback dei revisori (8) | Rilevazione dello scostamento sistematico nel campione e proposta di ricalibrazione al comitato |
| Revisore: rubrica | Funzione `registra_giudizio_rubrica` con atto e nota nello spazio; distribuzione dei task fra i revisori; coda unica con abbinamenti e risultati instabili |
| Questionari d3/d4 | Campagne, destinatari, inviti, risposte (migrazione, tabelle nello spazio); invio email; aggregazione; permessi del comitato |
| Vista del rappresentante | Attivazione per organizzazione (amministratore); nomina (comitato); rilevazione delle riduzioni di D dovute agli indirizzi; sospensione con atto |
| Amministratore | Worker dei job; caricamento dei documenti dal browser; stima dei costi prima delle chiamate a pagamento |
| Comitato | Avanzamento della sperimentazione per voce; storico delle restituzioni |

## Costruzione, a fette consegnabili

Ogni fetta: API con test, schermate con test, revisione (Python, database, sicurezza, accessibilità), PR verso `main` con approvazione del responsabile.

0. **Fondamenta** (ADR 0007): FastAPI con SSO e sessione, connessione per richiesta e log di accesso dedicato; frontend con il sistema di design di `docs/identita/`; CI su GitHub; ambiente di prova su un ramo Neon. Pagina pubblica.
1. **Comitato: panoramica e restituzione**, con avanzamento della sperimentazione e approvazione con impronta.
2. **Indirizzi del comitato**: questionario, profilo di pesi, effetto sui task, approvazione del comitato, ok dell'auditor, ricalcolo.
3. **Revisore**: coda unica, campioni, lotti, valutazione sulla rubrica, proposta di ricalibrazione.
4. **Task non abbinati per somiglianza** e pipeline dei documenti con il worker (amministratore).
5. **Questionari d3/d4.**
6. **Auditor e vista bonus del rappresentante.**

## Test

- API: test con il database di prova come oggi (`tests/`), un test per ogni permesso negato.
- Frontend: test dei componenti; **end to end** con Playwright sui percorsi critici (indirizzi fino all'ok dell'auditor, approvare una restituzione, decidere un lotto, dare un giudizio sulla rubrica, rispondere al questionario).
- Accessibilità: WCAG 2.2 AA, controllo automatico nella CI e verifica da tastiera.

## Esercizio

- **Ospitalità in UE**, database Neon già in UE; ambiente di **prova** su un ramo Neon separato, con dati sintetici.
- **Email:** servizio di invio con server in UE, mittente verificato per dominio.
- **CI su GitHub** a ogni PR; **backup** con ripristino puntuale di Neon e prova di ripristino documentata.

## Decisioni del responsabile ancora aperte

1. Approvazione di questo piano, delle bozze e dell'ADR 0007.
2. Coppia di caratteri (Inter + JetBrains Mono oppure Geist + Geist Mono): oggi Inter, cambio di un solo token.
3. Fornitore di ospitalità in UE (proposta nell'ADR 0007).
4. Questionari d3/d4: aggregazione del gruppo (proposta: mediana sulla scala 0–4) e `minimo_rispondenti_gruppo` (il piano indica 5).
5. Le domande del questionario del comitato e la regola che traduce le risposte in pesi: da definire con il comitato del primo pilota.
