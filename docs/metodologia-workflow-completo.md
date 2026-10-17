# Neartech: metodologia e workflow completo

**Versione consolidata 2, 2026-10-17.** La versione 2 allinea percorso, ruoli e dati al workflow della fase 6 (piattaforma per le aziende pilota). Documento di riferimento per chi usa, governa o verifica le analisi di Neartech. Ricostruisce il metodo a partire dalle decisioni più recenti del responsabile del progetto. Dove una decisione successiva supera una precedente, vale la successiva; le incoerenze residue sono elencate nella sezione 10.

---

## 0. Come leggere questo documento

Il riferimento unico è la combinazione di queste fonti, consolidate nell'ordine indicato:

| Fonte | Data | Ruolo nel consolidamento |
|---|---|---|
| `workflow e metodologia rivisti.docx` | 2026-10-16, 18:43 | Percorso del ruolo di staff con tre task di esempio e commenti del responsabile. Superato su canonicalizzazione, ruoli, approvazioni e comitato. Le sue indicazioni confermate sono riprese. |
| `docs/piano-sviluppo-v2.md` | 2026-10-16 | Piano di base: N e D, rubrica, fonti, validazione, governance, ciclo di aggiornamento. Vale dove non è superato dalle decisioni successive. |
| `docs/metodologia-estensioni.md`, sezioni 1–13 | 2026-10-12 / 2026-10-17 | Registro delle decisioni operative approvate dal responsabile. Fonte primaria per le scelte di metodo. |
| `docs/HANDOVER.md`, sezione 3 "Decisioni vigenti" | 2026-10-17 | Stato vigente delle decisioni, sintesi aggiornata del registro. |
| `docs/adr/0001`–`0005` | 2026-10-16 / 10-17 | Decisioni di architettura: testo del cliente, indirizzi del comitato, schema per organizzazione, testi nello spazio, scheletro in `public`. |
| `docs/adr/0006` (non ancora committato) | 2026-10-17 | Abbinamento al dataset: candidati, proposte, decisione in blocco. Riprende la canonicalizzazione rivista dell'handover. |
| `docs/metodologia-estensioni.md`, sezione 14 (branch `stato-produzione`) | 2026-10-17 | Set di controllo del prompt v2 del Canonicalizer: non supera il controllo. |
| `docs/metodologia-estensioni.md`, sezione 15 (branch `governance-e-pulizia`) | 2026-10-17 | Seguiti tecnici delle revisioni. Decisioni tecniche da confermare dal responsabile. |
| `docs/governance/linee-guida-parametri-comuni.md` | 2026-10-17 | Guida per il comitato guida sui parametri comuni. |
| Workflow della fase 6, comunicato dalla sessione «Fase 6», e `docs/piani/fase-6-piattaforma.md` (branch `worktree-fase-6-piattaforma`, PR #28) | 2026-10-17 | Percorso per azienda in nove passi, indirizzi e profilo dei pesi di D, revisione a campione, ruoli, questionari e collocazione dei dati. Prevale sulle fonti precedenti dove le contraddice. |

**Stato di approvazione.** Le sezioni 1–13 del registro e gli ADR 0001–0005 sono approvati dal responsabile. La sezione 14 è approvata, con esito negativo. La sezione 15 e l'ADR 0006 sono in attesa di conferma. Le istruzioni di revisione dell'abbinamento sono una bozza da approvare. Il workflow della fase 6 è riportato come approvato dal responsabile dalla sessione della fase 6; il piano della fase 6 resta in bozza.

---

## 1. Principi

1. **Gli agenti propongono, il calcolo è deterministico, le persone decidono.** Ogni modifica che cambia un risultato di policy passa da un'approvazione umana.
2. **Nessuna soglia e nessun peso nel codice o nello schema.** Stanno in tabelle di parametri versionate e approvate.
3. **Un record per ogni giudizio.** Le valutazioni di modello e di persona non si sovrascrivono: ogni campione conserva il proprio valore e la versione della rubrica.
4. **I risultati portano le proprie chiavi.** Ogni risultato riporta il profilo di pesi, lo snapshot di copertura, la versione della rubrica e il modello che l'ha prodotto.
5. **Il testo dei documenti è dato, mai istruzione.** Nessun prompt esegue comandi contenuti in mansionari o job description.
6. **Modelli con versione bloccata.** Ogni cambio di modello richiede il set di controllo e la ritaratura del prompt prima di nuove valutazioni.
7. **Nessun output riguarda una persona.** Il sistema classifica task, mai lavoratori. Nessun dato individuale nel database.
8. **Il testo del cliente resta nel suo spazio.** Il dataset condiviso (`public`) contiene solo il task rielaborato e legami con nomi neutri. Il testo originale sta in `org_<codice>` (ADR 0001, 0005). Nella base NEARTECH entrano solo dati anonimizzati; log e azioni dell'organizzazione restano consultabili per l'audit nella sua sezione (sezione 3).
9. **Le modifiche allo schema avvengono con migrazioni nuove**, mai modificando una migrazione già applicata in produzione.
10. **Lingua: documentazione, commenti e nomi di dominio in italiano.**

---

## 2. Ruoli

| Ruolo | Ambito | Cosa fa | Cosa non fa |
|---|---|---|---|
| **Amministratore tecnico** | Globale | Super user e fornitore del servizio. Governa i parametri del frontend, il budget dell'IA (come nella console di Anthropic), le fonti e gli snapshot di capacità. Propone e approva i parametri comuni. Crea le organizzazioni, gestisce gli utenti, avvia scomposizione, abbinamento e calcolo. Segue ogni fase e può intervenire. Attiva la vista facoltativa del rappresentante dei lavoratori. Può intervenire sullo stato di validazione del dataset condiviso. | Non decide i parametri dell'organizzazione. Non giudica i singoli task. |
| **Comitato guida** | Organizzazione | Unisce il metodologo e il comitato di governance. Vede tutti i task, per funzione e ruolo, fino al singolo task. La sua leva principale sono gli **indirizzi**: con interviste strutturate e questionari sulla visione dell'innovazione tecnologica produce il profilo dei pesi di D (fase E6). Regola i parametri di livello superiore partendo dai valori predefiniti; adotta o chiede la ricalibrazione dei parametri comuni. Decide sulle proposte di ricalibrazione dei pesi. Approva la restituzione finale. | Non giudica il singolo task (ADR 0002). |
| **Revisori** | Organizzazione | Approvano o rifiutano gli abbinamenti e le fusioni. Controllano le classificazioni su un campione e le correggono: la correzione vale per quel task in tutte le sue occorrenze. Danno i giudizi sulla rubrica (k1–k3, r, d1, d2): non esiste un ruolo di valutatore separato. Segnalano al comitato le deviazioni sistematiche e i bias. | Non cambiano parametri. Non correggono da sé gli altri task. Non vedono più di quanto il loro ruolo consente. |
| **Rappresentante dei lavoratori** | Organizzazione | Vista facoltativa, attivata dall'amministratore tecnico; altrimenti non compare. Verifica i cali di D causati dagli indirizzi del comitato e può rinviarli al comitato. | Non ha un veto: la decisione resta al comitato. |
| **Auditor** | Globale | Segue ogni fase e vede tutto come l'amministratore tecnico, in lettura. Legge log e aggregati. Dà il via libera al profilo dei pesi di D dopo l'approvazione del comitato. | Non cambia parametri e non giudica task. |
| **Chi risponde ai questionari** | Organizzazione | Lavoratori (d3) e beneficiari o chi li rappresenta (d4). Ricevono un'email con un link monouso; le risposte si leggono solo aggregate, con almeno 5 rispondenti per gruppo. | Non ha un account né un ruolo nella piattaforma. |

**Note.**
- Il "curatore" non è un ruolo. Le sue funzioni sono ripartite: fonti e snapshot all'amministratore tecnico, abbinamenti e fusioni ai revisori.
- Una stessa persona può avere comitato guida e revisore nella stessa organizzazione. Il sistema non lo vieta. Le approvazioni di proposte fatte e approvate dalla stessa persona sono registrate con `stesso_proponente`.
- La visibilità è configurabile: dallo schema con un solo revisore che vede tutto, fino a schemi in cui ciascuno vede solo il proprio ruolo.
- **Differenza da confermare.** Il piano della fase 6 dice che il rappresentante dei lavoratori lo nomina il comitato guida; il workflow comunicato dalla sessione della fase 6 dice che la vista la attiva l'amministratore tecnico. Qui si segue il workflow, più recente (sezione 10, punto 17).

---

## 3. Dove stanno i dati

| Oggetto | Dove | Motivo |
|---|---|---|
| Task canonici rielaborati, stati, legami con nomi neutri | `public` (dataset condiviso) | Sono il patrimonio della base di conoscenza. |
| Testo dei documenti, motivazioni, note dei revisori, candidati | `org_<codice>` (spazio dell'organizzazione) | Sono testo del cliente (ADR 0001, 0004, 0005). |
| Impronte dei testi (`hash_testo`, `hash_nota`) | `public`, calcolate con la chiave dello spazio | Chi legge solo `public` non può verificare un testo indovinato. |
| Registro delle decisioni | `public` (catena di hash) | Ogni atto è registrato; le righe non si modificano. |
| Giudizi, campioni, misure | `public` con gli identificativi dello spazio | Append-only: un ripensamento è un record nuovo. |
| Log di accesso | `public` | Ogni verifica di permesso lascia una riga. |

Tutte le tabelle che registrano decisioni o giudizi sono append-only. Il ruolo applicativo non è proprietario delle tabelle e non può disattivare i controlli. Il confine di fiducia è la credenziale applicativa: chi la possiede può scrivere un atto falso, che però resta visibile nel registro (migrazione 0026).

**Indirizzo della fase 6.** Nella base NEARTECH (`public`) entrano solo dati anonimizzati; log e azioni dell'organizzazione restano consultabili per l'audit nella sua sezione. Oggi registro e log di accesso stanno in `public` con gli identificativi dello spazio: l'allineamento è un punto aperto (sezione 10, punto 18).

---

## 4. Parametri e chi li governa

I parametri sono di tipo comune (valgono per tutte le organizzazioni) o di organizzazione (decisi dal suo comitato). Ogni valore è versionato e ha un approvatore.

| Parametro | Tipo | Chi propone | Chi approva | Note |
|---|---|---|---|---|
| Soglia di precisione dell'abbinamento | Comune | Amministratore tecnico | Amministratore tecnico | Valore 0,90. Il comitato lo adotta o chiede ricalibrazione. |
| Regola sui parziali | Comune | Amministratore tecnico | Amministratore tecnico | Parziale conta come errore. |
| Livello di confidenza | Comune | Amministratore tecnico | Amministratore tecnico | Valore 0,95. |
| Profilo di pesi di N (`w_k`, `λ`) | Organizzazione | Comitato guida | Comitato guida | Scelta del cliente, versionata. |
| Soglie che separano i quadranti | Organizzazione | Comitato guida | Comitato guida | Default 0,50 per N e per D, da approvare. |
| Profilo dei pesi di D (`w_d1`–`w_d4`, enfasi per classi di task) | Organizzazione | Comitato guida, dagli indirizzi | Comitato guida, con via libera dell'auditor | Nasce da interviste strutturate e questionari (fase E6). Aggiunge enfasi sopra il pavimento legale, mai lo tocca. |
| Pavimento legale di D | Organizzazione | Comitato guida | Comitato guida | Per task con norma citata. Gli indirizzi non lo toccano. Oggi vuoto. |
| Quota di revisione a campione | Comune | Amministratore tecnico | Amministratore tecnico | Parametro approvato, non numero nel codice. |
| Rubrica e ancore | Comune | Responsabile metodologico | Comitato guida, con riapprovazione delle restituzioni | Ogni versione è marcata. |
| Budget dell'IA | Tecnico | Amministratore tecnico | Amministratore tecnico | Come nella console del fornitore del modello. |

**Regola.** Un parametro dell'organizzazione, se approvato, prevale su quello comune. Il comitato di un'organizzazione adotta i parametri comuni vigenti oppure chiede una ricalibrazione motivata: sono atti registrati nello spazio dell'organizzazione (linee guida in `docs/governance/linee-guida-parametri-comuni.md`).

**Decisione aperta.** Se l'adozione di un parametro comune debba diventare obbligatoria prima di ogni calcolo (sezione 13 del registro, decisione b).

---

## 5. Workflow di analisi: dall'onboarding alla restituzione

Il percorso è composto da fasi in sequenza. Ogni fase indica che cosa esiste già nel software, che cosa è in costruzione e che cosa è una decisione aperta. Lo stato è aggiornato al 2026-10-17.

**Sequenza per azienda (workflow della fase 6).**

1. Le job description si scompongono in task (fase A).
2. Ogni task si abbina, dove possibile, alla base NEARTECH (fase B).
3. Task abbinato: eredita il punteggio del task della base (B4). Task non abbinato: riceve la media dei task più simili della base, pesata per somiglianza, ed è mostrato come «derivato per somiglianza»; poi entra nella base come task nuovo (fase C).
4. Il comitato guida vede i task e può scendere al singolo task; la sua leva principale sono gli indirizzi. Regola anche i parametri di livello superiore, partendo dai valori predefiniti (A3).
5. Gli indirizzi, raccolti con interviste strutturate e questionari sulla visione dell'innovazione tecnologica, producono il profilo dei pesi di D; il profilo vale dopo l'approvazione del comitato e il via libera dell'auditor (E6).
6. Con D calibrato, il sistema aggiorna la classificazione di tutti i task (fase F).
7. I revisori controllano le classificazioni su un campione (fase F bis).
8. La correzione di un revisore vale per quel task in tutte le sue occorrenze; una deviazione sistematica nel campione diventa una proposta di ricalibrazione dei pesi al comitato. Il sistema non corregge da sé gli altri task (fase F bis).
9. Il comitato vede il risultato finale e approva la restituzione (fase G).

L'auditor segue ogni fase; l'amministratore tecnico segue e può intervenire.

### Fase A: onboarding dell'organizzazione

**A1. Creazione dell'organizzazione e del suo spazio.** L'amministratore tecnico crea l'organizzazione. Il sistema assegna il codice breve, crea lo schema `org_<codice>` e registra l'atto. *Stato: costruito.*

**A2. Nomina dei ruoli.** L'amministratore assegna il comitato guida e i revisori e, se previsto, attiva la vista del rappresentante dei lavoratori. Ogni assegnazione è un atto nel registro, firmato da chi aveva `gestire_utenti`. Il bootstrap è ammesso solo per il primo amministratore tecnico. *Stato: costruito (migrazione 0026, in attesa di applicazione in produzione).*

**A3. Parametri e indirizzi del comitato.** Il comitato guida:
- vede i parametri comuni vigenti, con valore, versione e descrizione, e li adotta o chiede una ricalibrazione motivata;
- regola i parametri di livello superiore (soglie dei quadranti, pavimento legale, profilo di pesi di N), partendo dai valori predefiniti;
- dà gli indirizzi, da cui nasce il profilo dei pesi di D (fase E6). Gli indirizzi non toccano soglie, pavimento legale o passaggi di approvazione. *La versione 1 diceva che gli indirizzi non cambiano mai i pesi: il workflow della fase 6 la supera (sezione 10, punto 16).*

Il comitato riceve le linee guida per capire che effetto ha ogni sua azione sul sistema. *Stato: costruito; linee guida per il comitato, versione 1.*

**A4. Caricamento dei documenti.** Il responsabile carica le job description o i mansionari dell'organizzazione.
- Per i documenti interni la licenza coincide con il contratto del pilota: non serve una verifica di licenza documento per documento.
- Il caricamento richiede il permesso `gestire_dataset_centrale`, verificato prima della chiamata al modello. Ogni documento caricato lascia un atto nel registro.
- Il caricamento richiede la connessione diretta al database, non il canale HTTPS.
- Il testo del documento è dato da analizzare. Il modello legge le frasi del documento come contenuto, non come istruzioni.

*Stato: costruito (`scripts/scomponi_job.py`). Ingestione automatica da fonti esterne: non costruita.*

**A5. Candidati.** La scomposizione produce **candidati**: attività nello spazio dell'organizzazione, con titolo, estratto e nota di contesto. Un candidato non entra nel dataset finché una decisione umana non lo porta lì (ADR 0006, punto 1). *Stato: costruito.*

### Fase B: abbinamento al dataset consolidato

Il principio: il task dell'organizzazione si abbina al task più vicino del dataset consolidato. Solo i task senza corrispondenza entrano nel dataset. Così due organizzazioni con lo stesso task ottengono lo stesso punteggio.

**B1. Proposte.** Per ogni candidato il sistema calcola il task attivo più vicino per embedding, con la distanza e il margine sul secondo, e salva i vicini. Nessuna soglia di distanza decide: la vicinanza ordina la coda di revisione, non la decide. L'embedding si calcola in locale (bge-m3). *Stato: in costruzione (`scripts/abbina.py proponi`, non ancora committato).*

**B2. Lotto e livello di revisione.** Le proposte formano un **lotto**, che dichiara il livello di revisione:
- `campione`: si rivede una quota dichiarata, e su quel campione si misura la precisione;
- `completa`: si rivedono tutte le proposte;
- `nulla`: il lotto non si rivede, e la scelta si dichiara nel sistema.

Il livello incide sullo stato dei risultati che ne derivano. *Stato: in costruzione.*

**B3. Revisione in blocco.** Il revisore approva il lotto tranne le proposte che rifiuta. Ogni proposta ha il suo record, legato all'atto nel registro. La revisione è cieca rispetto al calcolo: il revisore vede il candidato e il task proposto, non la distanza. Le istruzioni (`istruzioni-abbinamento-v1`) sono ancora una bozza da approvare. *Stato: bozza.*

**B4. Applicazione deterministica.**
- Proposta approvata: l'organizzazione eredita la classificazione del task esistente, con N e D trasferiti. Nessun modello riclassifica il task.
- Proposta rifiutata o senza vicini: il candidato diventa un task nuovo nel dataset, con il titolo rielaborato in `public`, fonte "Neartech" e la colonna riservata al cliente con il testo originale nello spazio. Il suo punteggio di partenza è derivato per somiglianza (C1).

*Stato: in costruzione.*

**B5. Misura della precisione.** La precisione dell'abbinamento si misura prima di ogni altra metrica, su un campione rivisto: 90% è la soglia comune (parametro approvato). Il campione si estrae con criterio registrato, la revisione è cieca, e la misura porta le versioni di rubrica, parametri e origine delle proposte. Un campione incompleto o con disaccordi tra revisori non produce misura. *Stato: costruito (fase 2, `scripts/metrica.py`). Mancano ancora i giudizi delle persone sul lotto reale.*

### Fase C: task non abbinati e loro classificazione

**C1. Punteggio derivato per somiglianza.** Un task senza corrispondenza riceve, come punteggio di partenza, la media dei task più simili della base NEARTECH, pesata per somiglianza. È mostrato come «derivato per somiglianza» ed entra nella base come task nuovo, in forma standard e anonimizzata. La regola è deterministica: i task simili e i pesi di somiglianza si registrano con il risultato. Le etichette del modello già prodotte restano stime preliminari, marcate come tali (etichette v2 di Haiku 5.5 per 354 task del silver). *Regola del workflow della fase 6; non ancora costruita. Numero dei vicini e forma del peso di somiglianza sono parametri da approvare, non numeri nel codice.*

**C2. Stato del task.** Ogni task ha uno stato:
- `validato`: rivisto da persone;
- `derivato per somiglianza`: punteggio di partenza ottenuto dai task simili, provvisorio finché il campione non lo conferma;
- `stima del modello`: provvisorio;
- `da integrare`: non ancora rivisto.

Un task non validato non può fondare un'analisi definitiva. L'output mostra lo stato.

**C3. Priorità di revisione.** I task classificati per la prima volta hanno priorità nella revisione. Il revisore può dare un feedback su qualunque task, ma il processo va avanti anche a campione. Il sistema segnala che una revisione umana accurata su una quota di task è necessaria perché il risultato finale sia affidabile. La quota è un parametro approvato. *Stato: regole di priorità da approvare; la coda non è ancora costruita.*

Le regole che attivano la revisione, tratte dal piano e da approvare, sono:
- la probabilità del quadrante principale è sotto l'80%;
- le cinque valutazioni del modello divergono di oltre un punto su una voce;
- esiste una coppia quasi identica nel testo con coordinate molto diverse. Se il revisore conferma la differenza e ne annota il motivo, la coppia diventa un esempio di calibrazione;
- il task appartiene a una famiglia ad alto rischio normativo;
- D è ancora basata solo su stime preliminari.

Nessuna di queste soglie sta nel codice.

**C4. Decisione umana.** Ogni revisione produce un record separato: chi decide, quando e perché. L'etichetta del modello non viene sovrascritta. Se la decisione riguarda una regola della rubrica e non un singolo task, la decisione è sulla rubrica (esempio: una distinzione che il modello non coglie perché r misura solo le conseguenze tecniche e non il costo economico di un errore strategico). *Stato: il record esiste; la coda con le regole di priorità no.*

**C5. Compiti che nessun altro possiede.** Ricevono il punteggio derivato per somiglianza (C1) e hanno priorità nel campione dei revisori (F bis). *Il workflow della fase 6 supera la decisione di posizionamento del 2026-10-17 sui compiti nuovi (stima da evidenze esterne e revisione con il cliente sotto un livello di certezza, con l'intervento dei consulenti). Le evidenze restano la base di N (D2). Se l'intervento dei consulenti resti come servizio fuori dal metodo è da confermare (sezione 10, punto 15).*

### Fase D: valutazione di N (domanda tecnologica)

**D1. Domanda del task.** Per ogni task si valutano k1 (variabilità dell'input), k2 (giudizio) e k3 (componente fisico-percettiva) su scala 0–4. La criticità dell'errore r è un moltiplicatore, non una quarta dimensione. r misura solo l'affidabilità richiesta: i danni a diritti e reputazione stanno in D.

**D2. Copertura tecnologica.** La base di conoscenza segue di continuo lo stato dell'arte dell'avanzamento tecnologico e lo mappa sulle librerie di compiti standard (basate su standard globali, europei e italiani): per questo è predittiva e indica che cosa verrà automatizzato, non solo che cosa lo è già. La copertura non si decide a tavolino. Si calcola dalle evidenze, pesate per qualità, forza del collegamento al task e decadimento nel tempo (dimezzamento ogni 6 mesi, da tarare con la verifica a posteriori). Le evidenze si collegano ai nodi delle tassonomie e si trasferiscono sui task solo attraverso relazioni esatte o più strette. Per N si usa la **capacità di test**: misurata in condizioni controllate, dichiarata come tale e versionata per modello. La capacità dimostrata in produzione resta una grandezza separata.

**D3. Snapshot approvato.** La copertura viene pubblicata come snapshot proposto con una nota su cosa è cambiato. L'amministratore tecnico approva lo snapshot. Dopo l'approvazione, N si ricalcola per tutti i task. Una variazione tecnologica non richiede di toccare pesi o rubrica.

**Stato di N.** La capacità non è ancora collegata ai task di Società Dolce, e la scala 0–4 non è calibrata. Per questo N non è completo. La calibrazione richiede un campione etichettato da persone.

### Fase E: valutazione di D (desiderabilità)

D riflette cosa vogliono le persone coinvolte e quali valori l'organizzazione decide di proteggere. Non si deduce da un modello.

**E1. Quattro componenti.**

| Componente | Domanda | Chi risponde |
|---|---|---|
| d1 Relazione e fiducia | Quanto conta la presenza umana nel rapporto con l'altra persona? | Revisori, con i giudizi sulla rubrica |
| d2 Responsabilità | Il task incide su diritti, carriere, risorse individuali o è un atto riservato per legge? | Revisori, con i giudizi sulla rubrica |
| d3 Senso del lavoro | Se il task sparisse, il lavoro sarebbe migliore o snaturato? | Chi svolge il task, con il questionario |
| d4 Valore per il beneficiario | Se lo svolgesse un sistema con la stessa qualità tecnica, sarebbe accettabile? | Beneficiari o chi li rappresenta, con il questionario |

Il dato primario conservato sono sempre i quattro punteggi separati. D è una vista calcolata a valle con il profilo dei pesi di D nato dagli indirizzi del comitato (E6).

**E2. Base NEARTECH e profilo dei pesi.** D è per organizzazione:

`D_finale = max( pavimento legale ; D pesata con il profilo dell'organizzazione )`, limitato a 0–4.

- La **base NEARTECH** sono i punteggi d1–d4 ereditati dalla base o derivati per somiglianza. È presentata al cliente come "valutazione basata su dati NEARTECH". Nel record interno l'origine resta esplicita.
- Il **profilo dei pesi di D** (`w_d1`–`w_d4`, ed enfasi per classi di task dove serve) nasce dagli indirizzi del comitato (E6). Vale dopo l'approvazione del comitato e il via libera dell'auditor.
- Il **pavimento legale** è il livello minimo che una norma impone per un task. Gli indirizzi aggiungono enfasi sopra il pavimento, mai lo toccano. Oggi è vuoto, perché la verifica delle norme è sospesa.
- I **cali di D** causati dagli indirizzi sono segnalati in revisione e nel report finale. Se la vista del rappresentante dei lavoratori è attiva, il rappresentante può rinviarli al comitato, che decide. *Che cosa resti vigente finché il comitato decide (il piano della fase 6 propone il D precedente) è una decisione aperta.*
- Lo scostamento del profilo dai valori predefiniti viene registrato nell'audit finale.

**E3. Stime preliminari.** Finché non esiste un dato raccolto, un modello propone stime preliminari di ciascuna componente. Sono sempre etichettate come preliminari e conservate a parte. Vengono sostituite dai giudizi dei revisori o dai risultati dei questionari appena disponibili. Se rappresentano oltre il 30% delle ore di un ruolo, rendono provvisori tutti i risultati di quel ruolo.

**E4. Questionari per d3 e d4.** Non si etichettano con il modello. La piattaforma genera i questionari a partire dai task di una famiglia professionale (al massimo 12 task) e li invia per email a lavoratori (d3) e beneficiari o chi li rappresenta (d4), con un link monouso che non contiene l'identità. Gli indirizzi email restano nello spazio dell'organizzazione, separati dalle risposte. Le risposte sono pseudonimizzate alla raccolta e si leggono solo aggregate, con almeno 5 rispondenti per gruppo (parametro `minimo_rispondenti_gruppo`). Alla chiusura della campagna, il risultato del gruppo ricalibra d3 o d4 e il sistema ricalcola. *Come si aggrega il gruppo (proposta: mediana sulla scala 0–4) è una decisione aperta del piano della fase 6. Stato: non costruito (fase 6, fetta 3).*

**E5. Dato di riferimento esterno.** Dove esiste una corrispondenza con il dataset WORKBank, il livello di coinvolgimento umano preferito dai lavoratori (H1–H5) entra come ulteriore indicazione sul senso del lavoro, con peso ridotto.

**E6. Indirizzi del comitato e profilo dei pesi di D.** Il comitato guida dà gli indirizzi con interviste strutturate e questionari sulla visione dell'innovazione tecnologica dell'impresa. Gli indirizzi producono il profilo dei pesi di D: `w_d1`–`w_d4` e, dove serve, un'enfasi per classi di task. Regole:

- gli indirizzi aggiungono solo enfasi sopra il pavimento legale, mai lo toccano;
- il profilo è un parametro versionato (`weight_profiles`), mai un numero nel codice;
- vale dopo l'approvazione del comitato e il via libera dell'auditor; poi il sistema aggiorna la classificazione di tutti i task (fase F).

*Stato: la vista «Indirizzi del comitato» è in bozza nella piattaforma della fase 6; il calcolo del profilo dagli indirizzi non è costruito.*

### Fase F: calcolo deterministico

Il programma calcola N e D. Il modello linguistico non somma mai i punteggi.

**F1. Formule.**

- Divario per dimensione: `g_k(t) = max(0, d_k − c_k(t)) / 4`, dove `c_k(t)` è la copertura alla data `t`.
- N: `N(t) = min(1, Σ_k w_k · g_k(t) · (1 + λ · r/4))`, con pesi `w_k` che sommano a 1 e `λ` approvati dal comitato.
- D: media pesata delle quattro componenti, riportata su scala 0–1, con il profilo dei pesi di D (E6).

**F2. Simulazione e quadranti.** Il sistema esegue 2.000 simulazioni Monte Carlo a partire dai campioni e dagli intervalli di incertezza. Conta in quale quadrante cade ciascuna simulazione. Scrive media e deviazione di N e D, la probabilità di ciascun quadrante e la composizione delle fonti di D.

**F3. Stabilità.** Un task è stabile se il quadrante più probabile supera l'80%. Altrimenti va in revisione umana. Il criterio di stabilità si verifica sulle ore lavorate: almeno il 75% deve essere stabile.

**F4. Assenza di profilo.** Senza profilo di pesi approvato il sistema non assegna il quadrante e marca il risultato come provvisorio.

**F5. Chiavi del risultato.** Ogni risultato riporta: profilo di pesi, snapshot di copertura, versione della rubrica, modello e versione del prompt, esito e stato di validazione dei task.

*Stato: calcolo previsto; non ancora costruito per N e D completi. Dipende dalle fasi C, D ed E.*

### Fase F bis: revisione a campione e correzioni

**F bis 1. Campione.** I revisori controllano le classificazioni su un campione, con priorità ai task incerti e a quelli derivati per somiglianza (C3). La quota è un parametro approvato.

**F bis 2. Correzione.** La correzione di un revisore è un giudizio di persona con il suo record e vale per quel task in tutte le sue occorrenze. La stima del modello resta visibile.

**F bis 3. Deviazione sistematica.** Se il campione mostra una deviazione sistematica, il sistema la segnala al comitato come proposta di ricalibrare i pesi. Non corregge da sé gli altri task: gli agenti propongono, le persone decidono.

*Stato: campioni, giudizi e misure esistono per l'abbinamento (fase B5); propagazione delle correzioni e segnalazione delle deviazioni non costruite.*

### Fase G: restituzione

**G1. Chi vede cosa.**
- Il comitato guida vede i task, fino al singolo task, e i risultati per ruolo o funzione solo sopra una soglia minima di gruppo. Nessun output riguarda una persona.
- Il revisore vede le classificazioni dei singoli task su cui deve decidere.
- L'auditor segue ogni fase e legge log e aggregati; la sua sola azione è il via libera al profilo dei pesi di D.

**G2. Restituzione finale.** La restituzione è approvata dal comitato guida. Se una decisione del comitato cambia una regola della rubrica o un altro parametro:
1. il revisore analizza la classificazione aggiornata;
2. il comitato riapprova la restituzione finale, con una nuova versione.

Le restituzioni precedenti restano legate alla versione con cui sono state date.

**G3. Report di audit.** Ogni organizzazione ha un report di audit unico che raccoglie analisi e decisioni: atti del registro, parametri, testi di governance, giudizi, misure. Si produce con `scripts/report_audit.py` e richiede il ruolo auditor. *Stato: costruito.*

**G4. Limiti d'uso.** La base di conoscenza non produce valutazioni di singoli lavoratori né graduatorie di persone. I risultati di un ruolo con D prevalentemente da stime preliminari sono provvisori e non possono motivare una riorganizzazione. Ogni risultato esportato riporta il profilo di pesi, lo snapshot di copertura e la versione della rubrica.

---

## 6. Manutenzione e attualizzazione

La base di conoscenza non si costruisce una volta sola. Un sistema di componenti la alimenta e la aggiorna nel tempo. Il principio resta lo stesso: gli agenti propongono, il codice calcola, le persone approvano tutto ciò che cambia un risultato di policy.

### 6.1 Cadenze

| Quando | Cosa succede | Chi approva |
|---|---|---|
| Settimanale | Il Source Watcher controlla i nuovi rilasci (O\*NET, ESCO, Anthropic Economic Index, GDPval, METR, ILO, preprint, novità normative) e registra le nuove fonti dopo i controlli di integrità. | Registrazione automatica dopo controlli; fonti nuove approvate dall'amministratore tecnico. |
| A ogni nuovo documento | Scomposizione, abbinamento e classificazione dei task nuovi. Il calcolo aggiorna solo le occorrenze toccate. | Revisori, sul lotto. |
| Mensile | Il Capability Estimator propone uno snapshot di copertura con una nota su cosa è cambiato. Il Sintetizzatore produce un report con novità delle fonti, spostamenti di quadrante per famiglia, stato della coda, proposte su rubrica e fonti. | Amministratore tecnico per lo snapshot. Il report è solo proposta. |
| Mensile | Precisione dei collegamenti misurata sul campione rivisto. | Metrica automatica; esito letto dal responsabile. |
| Trimestrale | Il responsabile metodologico rivede set di controllo, rubrica e regole di approvazione automatica alla luce delle metriche. | Comitato guida per rubrica e ancore. |
| Semestrale | Verifica a posteriori: la copertura stimata anticipa l'uso osservato, a sei mesi. | Responsabile metodologico. |
| A ogni cambio di modello | Rerun del set di controllo di 50 task fissi; se fallisce, ritaratura del prompt prima di ogni nuova valutazione. | Responsabile del progetto. |
| A ogni nuova versione della rubrica | Calcolo dell'alfa di Krippendorff per voce (almeno 0,67 per l'uso; obiettivo 0,80). | Comitato guida. |

### 6.2 Quando un cambiamento richiede una nuova analisi

- **Snapshot di copertura nuovo.** Si ricalcola N per tutti i task. Se un nuovo rilascio sposta la copertura media di una famiglia di oltre 0,5 punti, la nota esplicativa è obbligatoria prima della pubblicazione.
- **Cambio di parametro del comitato.** Il revisore analizza la classificazione aggiornata. Il comitato riapprova la restituzione. Le restituzioni precedenti restano legate alla versione di partenza.
- **Cambio di parametro comune.** Il comitato di ogni organizzazione lo vede e può adottarlo o chiedere una ricalibrazione. L'adozione vale per una versione: una versione nuova va adottata di nuovo. Una richiesta è superata quando la versione comune a cui si riferisce non è più vigente.
- **Cambio di modello.** Set di controllo, ritaratura del prompt, nuove valutazioni solo dopo. Il Canonicalizer non si riesegue finché la sua versione non supera il controllo.
- **Nuova evidenza.** Una nuova evidenza entra nel calcolo con il proprio peso, e il suo peso decade nel tempo. Non serve toccare pesi o rubrica.
- **Indirizzi del comitato.** Producono un nuovo profilo dei pesi di D, che vale dopo l'approvazione del comitato e il via libera dell'auditor. Il sistema riclassifica tutti i task, i revisori controllano il campione e il comitato riapprova la restituzione.

### 6.3 Data flywheel

Ogni task nuovo classificato diventa parte del dataset NEARTECH. Le aziende successive trovano più task già classificati. Con più clienti cresce anche la validità statistica del campione da cui nasce ogni classificazione. Due aziende con lo stesso task ottengono lo stesso punteggio, perché il dato è consolidato nella base.

### 6.4 Segnali di drift

- Il fornitore del modello aggiorna il modello: si riesegue il set di controllo; se fallisce, si ritara il prompt.
- La quota di D da stime preliminari supera il 30% delle ore di un ruolo: le metriche di quel ruolo sono mostrate come provvisorie.
- Una metrica di qualità scende sotto soglia: il lotto o la coda si fermano, e il blocco è registrato come atto. Le soglie sono parametri approvati.

### 6.5 Metriche di controllo

| Metrica | Cosa verifica | Soglia | Quando |
|---|---|---|---|
| Alfa di Krippendorff per voce | Coerenza della rubrica | Almeno 0,67; obiettivo 0,80 | A ogni nuova versione |
| Non-inferiorità rispetto al panel | Accordo sistema–consenso non peggiore dell'accordo medio di un valutatore | Differenza non peggiore di −0,05 sull'alfa, per asse | Prima del rilascio e a ogni cambio di modello |
| Precisione dei collegamenti | Corrispondenze esatte davvero esatte | Almeno 90% sul campione rivisto | Mensile |
| Precisione e richiamo dei duplicati | Deduplicazione che non fonde task diversi | Precisione 95%, richiamo 85% | Trimestrale |
| Correlazione N–D | Assi distinti | Spearman sotto 0,5 | A ogni ricalcolo |
| Set di controllo | Stabilità su 50 task fissi | Spostamento medio sotto 0,25 punti | Settimanale e a ogni cambio di modello |
| Stabilità dei quadranti | Quota stabile | Almeno 75% delle ore lavorate | A ogni ricalcolo |
| Coda di revisione | Sostenibilità della revisione | Tempo mediano di risoluzione fino a 10 giorni lavorativi | Settimanale |

**Nota.** Le soglie di questa tabella provengono dal piano V2 e non sono ancora tutte approvate dal comitato. Devono diventare parametri versionati prima di essere usate come regole automatiche.

---

## 7. Gold standard e validazione

La base entra in produzione quando il sistema giudica almeno quanto un valutatore umano medio, misurato su task che non ha mai visto. Il gold standard prevede:
- 200 task stratificati per famiglia professionale, sovracampionati fuori diagonale e vicino alle soglie;
- almeno 20 coppie minime: task quasi identici nel testo con requisiti diversi;
- divisione fissa: 60 task per tarare rubrica ed esempi, 140 task di hold-out mai mostrati al sistema;
- panel di 3–5 valutatori, con almeno un rappresentante dei lavoratori e una voce vicina ai beneficiari. Il panel serve solo alla validazione: non è un ruolo della piattaforma, dove i giudizi sulla rubrica li danno i revisori.

Se i valutatori non concordano tra loro, nessun modello può essere validato e il problema da risolvere è la rubrica. *Stato: non costruito.*

---

## 8. Governance

### 8.1 Chi decide cosa

| Oggetto | Chi propone | Chi approva | Applicazione automatica |
|---|---|---|---|
| Caricamento di documenti e fonti | Source Watcher o responsabile | Amministratore tecnico | Sì, dopo controlli di integrità |
| Candidati e nuovi task | Scomposizione e canonicalizzazione | Revisori, sul lotto | No: un lotto richiede una decisione |
| Abbinamenti al dataset | Sistema, per vicinanza | Revisori, in blocco | Sì, dopo la decisione del lotto |
| Collegamenti alle tassonomie | Crosswalk Mapper | Revisori, a campione | Da decidere (sezione 10) |
| Evidenze normalizzate | Evidence Extractor | Amministratore tecnico per le fonti nuove | Sì per fonti approvate |
| Snapshot di copertura | Capability Estimator | Amministratore tecnico, con nota | No |
| Rubrica e ancore | Responsabile metodologico | Comitato guida | No |
| Pesi, λ, soglie di quadrante | Comitato guida | Comitato guida | No: gli agenti possono solo segnalare una proposta di ricalibrazione |
| Parametri comuni (soglia, regola, livello) | Amministratore tecnico | Amministratore tecnico; il comitato adotta o chiede ricalibrazione | No |
| Profilo dei pesi di D (dagli indirizzi) | Comitato guida, con interviste e questionari | Comitato guida, con via libera dell'auditor | No |
| Correzione di una classificazione | Revisore, sul campione | Revisore | Sì, per quel task in tutte le occorrenze |
| Ricalibrazione dei pesi per deviazione sistematica | Sistema, come segnalazione | Comitato guida | No |
| Calo di D causato dagli indirizzi | Sistema, come segnalazione | Comitato guida; il rappresentante, se la vista è attiva, può rinviarlo al comitato | No |
| Restituzione finale | Sistema | Comitato guida | No |

### 8.2 Registro delle decisioni

Ogni atto è registrato con autore, oggetto, motivazione e, per le organizzazioni, testo nel suo spazio con impronta in `public`. Gli atti sono: proposta, approvazione, rifiuto, ritiro, segnalazione, blocco, correzione, adozione, richiesta di ricalibrazione, assegnazione di ruolo, caricamento di documento, creazione di organizzazione. Ogni approvazione, rifiuto o ritiro registra `stesso_proponente` nei dettagli. Le righe non si modificano: una correzione è un atto nuovo.

### 8.3 Comitato guida: composizione

Il comitato guida di ogni organizzazione comprende la direzione, i responsabili di linea e, dove presente, il responsabile della protezione dei dati; può includere la rappresentanza dei lavoratori. La vista del rappresentante dei lavoratori è facoltativa: verifica i cali di D causati dagli indirizzi e può rinviarli al comitato, senza veto. Il comitato è il contrappeso alle decisioni del fornitore del servizio sui parametri del cliente.

### 8.4 Contrappesi

Chi propone un parametro dell'organizzazione può anche approvarlo; l'atto lo segna. I revisori, che giudicano le classificazioni risultanti, possono segnalare al comitato i bias che derivano dalle sue decisioni, e il sistema segnala le deviazioni sistematiche come proposte di ricalibrazione. L'auditor dà il via libera al profilo dei pesi di D prima che valga. Il rappresentante dei lavoratori, se la vista è attiva, può rinviare al comitato i cali di D causati dagli indirizzi.

### 8.5 Quadro normativo

- **AI Act europeo.** Il Digital Omnibus ha spostato al 2 dicembre 2027 gli obblighi per i sistemi ad alto rischio dell'Allegato III, che include occupazione e gestione del personale. Se Neartech viene usato per assegnare compiti o prendere decisioni che toccano i lavoratori, va progettato con registrazione degli eventi, supervisione umana e documentazione tecnica. Il rischio di un task si classifica per coppia task × uso ipotizzato dell'IA, con quattro categorie: vietato, alto rischio, esente, non regolato (`docs/legale/ai-act-schema.md`).
- **Legge 132/2025, articolo 11.** Il datore di lavoro deve informare i lavoratori dell'uso di sistemi di AI. Un'organizzazione che usa la base per riprogettare mansioni deve valutare se rientra in questi casi. Neartech può fornire il materiale per l'informativa.
- **GDPR.** Le risposte ai questionari sono pseudonimizzate alla raccolta, con link monouso senza identità; gli indirizzi email sono conservati separatamente dalle risposte, e i risultati si mostrano solo in forma aggregata con gruppi di almeno 5 rispondenti.

Il quadro va verificato con un consulente legale prima del primo uso commerciale.

---

## 9. Stato di implementazione

| Parte | Stato |
|---|---|
| Schema multi-organizzazione, ruoli, permessi, registro, log, migrazioni | Costruito. In produzione fino alla migrazione 0025 e alla 0006 degli spazi. |
| Testo del cliente fuori da `public` | Costruito; eseguito su Società Dolce il 2026-10-17. |
| Parametri comuni, adozione e ricalibrazione | Costruito; in vigore in produzione. |
| Metrica di precisione (campioni, giudizi, misure) | Costruita. Mancano i giudizi delle persone sul lotto reale. |
| Scomposizione dei documenti e candidati | Costruita. |
| Abbinamento al dataset (proposte, lotti, applicazione) | In costruzione; non ancora committato. |
| Canonicalizer, prompt v2 | Il set di controllo non ha superato la soglia; il prompt v2 non si usa. Serve una versione 3 e un nuovo controllo. |
| Crosswalk alle tassonomie | Costruito per i task di Società Dolce; crosswalk delle 11 task separate da eseguire. |
| Etichette del modello (silver) | 354 task etichettati; 3 run per voce; d3 e d4 non etichettati dal modello. |
| Capacità di test collegata ai task | Non costruita. |
| Calcolo deterministico di N e D | Non costruito per N e D completi. |
| Coda di revisione con regole di priorità | Non costruita. |
| Questionari per d3 e d4 | Non costruiti (fase 6, fetta 3). |
| Indirizzi del comitato e profilo dei pesi di D | Non costruito; vista in bozza nella piattaforma della fase 6. |
| Punteggio derivato per somiglianza | Non costruito. |
| Revisione a campione con propagazione delle correzioni | Non costruita. |
| Restituzione per il comitato | Non costruita. |
| Report di audit per organizzazione | Costruito. |
| Gold standard e validazione | Non costruito. |
| Ingestione automatica da fonti (Source Watcher) | Non costruita. |

---

## 10. Decisioni aperte e incoerenze residue

1. **ADR 0006 non committato.** L'abbinamento segue l'ADR 0006, accettato ma presente solo nell'albero di lavoro. Va committato e confermato dal responsabile.
2. **Istruzioni di revisione dell'abbinamento.** Bozza, da approvare, con versione `istruzioni-abbinamento-v1`.
3. **Collegamento alle tassonomie.** Il commento del responsabile nel docx (passo 3, "superfluo") non è stato registrato come decisione. Il collegamento resta necessario per le evidenze di N, ma non decide nell'abbinamento. Da confermare.
4. **Regole di priorità e coda.** Il docx parla di priorità di revisione. Il piano parla di coda con regole. Il documento usa priorità di revisione con regole da approvare. Da confermare.
5. **Chi approva i pesi.** Il piano dice che pesi e soglie sono del comitato di governance. La decisione 10 del registro dice che i parametri comuni della metrica (soglia, regola, livello) li approva l'amministratore tecnico. Le due cose sono compatibili: i pesi di N e D sono del comitato; i parametri della metrica sono comuni. Per il profilo dei pesi di D serve anche il via libera dell'auditor (workflow della fase 6). Il confine va scritto nelle linee guida. Da confermare.
6. **Applicazione automatica dei collegamenti alle tassonomie.** Il piano prevede che siano automatici finché la precisione resta sopra il 90%. Il lotto di abbinamento richiede invece una decisione. Non è chiaro se la regola automatica valga anche per i collegamenti alle tassonomie, che non passano da un lotto. Da fissare.
7. **Adozione obbligatoria dei parametri comuni.** Se debba diventare obbligatoria prima dei calcoli è una decisione aperta (sezione 13 del registro, decisione b).
8. **Sezione 15 del registro.** I seguiti tecnici delle revisioni (migrazioni 0026–0030 e 0007 degli spazi) sono in attesa di conferma del responsabile. Due di essi sono decisioni di metodo: un atto per documento caricato, e l'uso del permesso `gestire_dataset_centrale` per il caricamento.
9. **Sezione numerata due volte.** Il registro di metodo ha due sezioni "4" (revisione del crosswalk e modifiche per il silver). Va scelto un numero per una delle due.
10. **Set di controllo.** Il piano parla di 5 valutazioni per voce; il silver ha adottato 3 run per il costo (sezione 4 del registro). Il set di controllo di 50 task va riallineato alla scelta fatta.
11. **Soglie del piano non ancora approvate.** Le soglie della sezione 6.5 vengono dal piano V2. Prima di usarle come regole automatiche vanno approvate come parametri.
12. **Capacità non calibrata.** La scala 0–4 della capacità di test non è calibrata. N non è completo finché non lo è.
13. **Questionari per d3 e d4.** Il modulo non esiste. Finché non c'è, D resta da stime preliminari, e i risultati sono provvisori.
14. **Verifica normativa.** Il quadro AI Act, L. 132/2025 e GDPR va verificato con un consulente legale.
15. **Consulenti e certezza (C5).** Il workflow della fase 6 sostituisce, per i compiti nuovi, la stima con revisione del cliente e intervento dei consulenti (decisione di posizionamento del 2026-10-17) con il punteggio derivato per somiglianza e il controllo a campione. Va confermato se l'intervento dei consulenti resti come servizio fuori dal metodo.
16. **ADR 0002 e indirizzi.** L'ADR 0002 lega gli indirizzi ai valori dell'organizzazione e alle classi di task, ma non descrive il profilo dei pesi di D e mantiene il blocco dei ribassi da parte dei rappresentanti dei lavoratori. Il workflow della fase 6 fa nascere dagli indirizzi il profilo dei pesi e sostituisce il blocco con il rinvio al comitato. L'ADR va aggiornato o superato.
17. **Chi attiva il rappresentante dei lavoratori.** Il piano della fase 6 dice che lo nomina il comitato guida; il workflow comunicato dalla sessione della fase 6 dice che la vista la attiva l'amministratore tecnico. Questo documento segue il secondo. Da confermare.
18. **Dove stanno log e azioni.** Il workflow vuole nella base NEARTECH solo dati anonimizzati, con log e azioni nella sezione dell'organizzazione; oggi registro e log di accesso stanno in `public` con gli identificativi dello spazio. Se confermato, serve una migrazione.
19. **Calo di D rinviato al comitato.** Che cosa vale finché il comitato decide (il piano della fase 6 propone il D precedente).

---

## 11. Glossario essenziale

- **Candidato.** Attività estratta da un documento dell'organizzazione, nello spazio. Non è ancora un task del dataset.
- **Task canonico.** Task del dataset condiviso, rielaborato in forma standard.
- **Lotto.** Insieme di proposte di abbinamento con il proprio livello di revisione.
- **N.** Quanto serve ancora l'intervento umano per limiti tecnici. Nei materiali per i clienti l'asse si chiama «Necessità della presenza umana: vincoli tecnici».
- **D.** Quanto vale che sia una persona a svolgere il task, per relazione, responsabilità e valore. Nei materiali per i clienti l'asse si chiama «Desiderabilità della presenza umana: scelte di valore».
- **Capacità di test.** Capacità misurata in condizioni controllate, dichiarata come tale, versionata per modello.
- **Pavimento legale.** Livello minimo di D imposto da una norma per un task. Non modificabile dall'organizzazione.
- **Base NEARTECH.** Punto di partenza di D, ereditato dalla base o derivato per somiglianza, presentato come "valutazione basata su dati NEARTECH".
- **Derivato per somiglianza.** Punteggio di partenza di un task senza corrispondenza: media dei task più simili della base, pesata per somiglianza.
- **Indirizzi.** La visione dell'innovazione tecnologica che il comitato guida esprime con interviste strutturate e questionari; producono il profilo dei pesi di D.
- **Profilo dei pesi di D.** Pesi `w_d1`–`w_d4` delle quattro componenti di D, con eventuale enfasi per classi di task. Vale dopo l'approvazione del comitato e il via libera dell'auditor.
- **Stima preliminare.** Valore di componente di D prodotto dal modello, in attesa di un giudizio dei revisori o del risultato di un questionario.
- **Snapshot di copertura.** Fotografia approvata della copertura tecnologica, usata per il calcolo di N.
- **Impronta.** Valore calcolato con la chiave dello spazio che lega un testo a `public` senza rivelarlo.
- **Set di controllo.** Insieme fisso di 50 task usato per verificare la stabilità del sistema a ogni cambio di modello.
