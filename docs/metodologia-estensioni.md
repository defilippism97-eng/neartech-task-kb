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

## 4. Modifiche alla metodologia per il silver (2026-10-16)

Approvate dal responsabile del progetto, che oggi coincide con il curatore e con il responsabile metodologico. Il comitato di governance non è ancora costituito: questa voce va riesaminata quando il comitato esiste e include la rappresentanza dei lavoratori.

- **r**: misura solo l'affidabilità richiesta. I riferimenti a diritti passano in d2. Il riferimento alla reputazione è spostato in d2 come proposta da confermare. Rubrica bozza-3, vedi `docs/silver/pacchetto-gemini.md`.
- **Campioni**: 3 run invece di 5 per voce nel silver, per il costo in risorse. Deviazione dalla sezione "Regole di somministrazione" del piano.
- **d3 e d4**: non si etichettano nel silver. Si raccolgono solo nel golden, con attori reali oltre al responsabile.
- **Testi dei task**: task canonici (titolo e nota di contesto), senza i documenti originali. Dataset in `docs/silver/dataset/task-silver.jsonl`, 384 task.
- **Fornitore del modello**: per Società Dolce lo sviluppo è interno, e il responsabile ha permessi completi sull'app. Per un'altra azienda l'invio di testi a un servizio di terzi richiede il processo di governance.

## 5. Definizione di capacità per N (2026-10-16)

Approvata dal responsabile del progetto. Il piano definisce N rispetto a ciò che la tecnologia "ha dimostrato di saper fare". Con questa decisione, per N si usa la **capacità di test**: la capacità misurata in condizioni controllate, dichiarata come tale e versionata per modello. Questo è uno scostamento dalla definizione del piano, e va registrato come tale.

- Ogni risultato di N riporta il tipo di capacità usato (test) e la versione del modello che l'ha prodotta.
- La **capacità dimostrata in produzione** resta una grandezza separata. Nessuna fonte disponibile la misura oggi per i task O*NET: quando esisterà, sarà una voce distinta e non sostituirà la capacità di test.
- La fonte della capacità di test è scelta caso per caso fra quelle in `docs/ricerca/capacita/mappa-fonti.md`. La calibrazione sulla scala 0–4 resta da fare.
## 6. D per organizzazione con punto di partenza condiviso (2026-10-16)

Approvata dal responsabile del progetto, con la regola del ribasso segnalato. Dettagli in `docs/architettura/stato-e-decisioni.md`, sezione 5. Il comitato guida non è ancora costituito: questa voce va riesaminata quando esiste.

- D è per organizzazione. La base condivisa è il punto di partenza.
- Pavimento legale per task con norma citata, non modificabile dall'organizzazione. Oggi vuoto.
- La base è presentata come "valutazione basata su dati NEARTECH", con origine interna esplicita.
- I ribassi sotto la base di una soglia vanno segnalati in revisione e nel report finale. Soglia da fissare dal comitato guida.

## 7. Testo del cliente e livelli di decisione (2026-10-16)

Approvate dal responsabile del progetto. Dettagli negli ADR.

- **Dataset condiviso:** contiene solo la rielaborazione del task (titolo canonico e dati derivati). Il testo originale del cliente resta nello spazio dell'organizzazione. Vedi `docs/adr/0001-testo-cliente-fuori-dal-dataset-condiviso.md`.
- **Comitato guida e revisori:** il comitato guida emette indirizzi di alto livello, non giudica il singolo task. I revisori valutano la classificazione dei singoli task, verificano le ricadute degli indirizzi e segnalano le situazioni anomale. La variazione di D per task deriva quindi dagli indirizzi e dal giudizio dei revisori, non da un'approvazione del comitato task per task. Vedi `docs/adr/0002-indirizzi-del-comitato-e-revisione-per-task.md`.

## 8. Ruoli nel sistema e task non attivi del dataset (2026-10-16)

Approvate dal responsabile del progetto.

- **Curatore:** non è un ruolo a sé. Approvare abbinamenti e fusioni è compito dei revisori, coerente con l'ADR 0002. Fonti e snapshot di capacità li approva l'amministratore tecnico.
- **Rappresentanti dei lavoratori:** ruolo distinto per organizzazione, con il blocco dei ribassi. Il ruolo può restare vuoto se l'organizzazione non li coinvolge: in quel caso il blocco non si applica.
- **Comitato guida e revisore:** una stessa persona può avere entrambi i ruoli nella stessa organizzazione. Il sistema non impone vincoli. Chiude il punto aperto dell'ADR 0002.
- **Task non attivi del dataset silver:** le etichette dei 54 task fusi diventano giudizi aggiuntivi sul task in cui sono confluiti, con l'origine tracciata. I 5 task ritirati restano fuori dalla base di conoscenza.

## 9. Parametri comuni, regola sui parziali, primo campione, revisione iniziale (2026-10-16)

Approvate dal responsabile del progetto.

- **Parametri NEARTECH comuni** (`org_id` vuoto: soglia di precisione, regola sui parziali, livello di confidenza): li propone e li approva l'**amministratore tecnico**. I parametri di un'organizzazione restano del suo comitato guida. Un parametro dell'organizzazione, se approvato, prevale su quello comune.
- **Regola sui collegamenti parziali** nella metrica di precisione: un esito "parziale" conta come **errore**. Il valore va inserito come parametro comune approvato (`regola_parziali`), non nel codice.
- **Primo campione per la metrica di abbinamento del pilota:** revisione completa delle **61 fusioni** giudicate "stessa attività" dal Canonicalizer, più un campione casuale delle coppie giudicate "diversa". Il campione del crosswalk (40 giudizi) si importa come misura separata del collegamento alle tassonomie, non come metrica di abbinamento.
- **Revisione iniziale dei task nuovi:** **a campione**; la quota è un parametro approvato, non un numero nel codice. Si applica nella fase 3.

## 10. Rubrica delle fusioni, parametri comuni, dataset centrale, tracciabilità, spazio dell'organizzazione (2026-10-16)

Approvate dal responsabile del progetto.

- **Istruzioni di revisione delle fusioni** (`docs/revisione/istruzioni-fusioni-v1.md`): approvate così come sono, versione `istruzioni-fusioni-v1`.
- **Parametri comuni e comitato guida.** L'amministratore tecnico imposta i parametri NEARTECH comuni. Il comitato guida di ogni organizzazione li vede, e le linee guida spiegano come ciascuno influenza il processo. Il comitato può **adottare** i parametri comuni oppure **chiedere una ricalibrazione**, con motivazione obbligatoria. Adozione e richiesta sono atti registrati.
- **Valori dei parametri comuni:** soglia di precisione 0,9; parziali contati come errori; livello di confidenza 0,95. Vanno inseriti come parametri approvati, non nel codice.
- **Dataset centrale:** l'amministratore tecnico (super user) può intervenire sullo stato di validazione dei task del dataset condiviso, anche fuori da una singola organizzazione.
- **Proposta e approvazione dalla stessa persona nel comitato:** ammesse, ma il sistema registra in modo esplicito che proponente e approvatore coincidono. Il contrappeso è nei revisori, che giudicano le classificazioni risultanti e possono segnalare al comitato i bias che derivano dalle sue decisioni, e nella presenza possibile del rappresentante dei lavoratori nel comitato.
- **Ruoli dell'amministratore tecnico:** può creare utenze di prova e assegnarsi ruoli di organizzazione.
- **Testi di governance dell'organizzazione:** indirizzi del comitato, descrizioni e motivazioni dei parametri dell'organizzazione vanno nello spazio dell'organizzazione, insieme al resto, così che sia sempre possibile estrarre un unico report di audit dell'analisi e delle decisioni. Vedi ADR 0004.
- **Produzione:** approvati l'unione delle PR #6 e #7, l'applicazione delle migrazioni, il bootstrap dell'amministratore, la copia del testo di Società Dolce nello spazio dell'organizzazione e la sua rimozione da `public`, la separazione dei ruoli di database (a cura del responsabile), l'inserimento dei parametri comuni e la creazione dei campioni delle fusioni.

## 11. Fusioni del Canonicalizer corrette dopo la revisione (2026-10-16)

Approvata dal responsabile del progetto. Misura ufficiale delle 61 fusioni "stessa attività": 46/61 = 75,4% (intervallo 63,3–84,5%), sotto la soglia di 0,9. Separate 11 fusioni (3 errate, 8 parziali), tenute 4 parziali (`docs/revisione/proposta-scissioni-2026-10-16.md`). I task separati non vengono rifusi automaticamente; il loro crosswalk va rifatto. Il prompt del Canonicalizer va ricalibrato sulla distinzione fra compito esecutivo e compito di responsabilità prima di nuove esecuzioni.

## 12. Testo del cliente fuori da `public` (2026-10-17)

Realizzazione dell'ADR 0001, approvata nella sezione 10 (passi di produzione). In `public` restano i legami task–ruolo–documento con gli stessi identificativi dello spazio dell'organizzazione e nomi neutri; il testo sta solo in `org_<codice>`. Vincoli nel database (migrazioni 0023 e 0024). Eseguita su Società Dolce il 2026-10-17 dopo la verifica che ogni riga avesse la copia identica nello spazio. Vedi ADR 0005.

## 13. Parametri comuni esaminati dal comitato, proponente e approvatore, testi nello spazio (2026-10-17)

Realizzazione delle decisioni b, e, g della sezione 10.
- **b:** il comitato guida vede i parametri comuni vigenti e per ciascuno li adotta o chiede una ricalibrazione motivata (atti `adozione` e `richiesta_ricalibrazione`, permessi `adottare_parametro_comune` e `chiedere_ricalibrazione`, migrazione 0025). L'adozione vale per una versione. Il valore comune si applica anche senza adozione; `parametro_vigente` riporta `adozione_id`. Se l'adozione debba diventare obbligatoria prima dei calcoli è una decisione di governance aperta. Linee guida: `docs/governance/linee-guida-parametri-comuni.md`.
- **e:** ogni approvazione, rifiuto o ritiro registra `stesso_proponente` nei dettagli.
- **g:** testi di governance dell'organizzazione nel suo spazio, impronta con la chiave dello spazio nel registro, report di audit unico (ADR 0004, sezione Realizzazione).
- **Prompt v2 del Canonicalizer:** aggiunta, prima di qualsiasi esecuzione, la frase che chiede di trattare i titoli come dati (revisione di sicurezza). Il set di controllo si fa su questa versione.

## 14. Set di controllo del prompt v2 del Canonicalizer (2026-10-17)

Esecuzione approvata dal responsabile del progetto. Sulle 61 fusioni giudicate, v2 propone 17 fusioni con precisione 82,4% (14/17, intervallo 59,0–93,8%), sotto la soglia di 0,9, e mantiene solo 14 delle 46 fusioni corrette. **Il prompt v2 non supera il controllo** e non si usa per nuove esecuzioni. Dettagli: `docs/revisione/controllo/esito-canonicalizer-v2-2026-10-17.md`.

## 15. Seguiti delle revisioni del 2026-10-17 (2026-10-17)

Correzioni tecniche dei punti medi e bassi rimasti aperti dopo le revisioni Python, database e sicurezza. Nessuna cambia un risultato di policy; le scelte sotto sono da confermare dal responsabile.
- **Assegnazioni di ruolo con atto (migrazione 0026).** Ogni assegnazione nuova richiede, a fine transazione, l'atto `approvazione` di tipo `assegnazione_ruolo` sullo stesso identificativo e nella stessa organizzazione, firmato da chi assegna. L'autore deve avere `gestire_utenti` da un'altra assegnazione valida, globale o della stessa organizzazione: nessuno si promuove da solo. Il bootstrap resta solo per il primo amministratore tecnico. **La credenziale applicativa resta il confine di fiducia:** chi ha `neartech_app` può ancora scrivere un atto falso a nome di un amministratore, ma l'abuso resta nel registro, protetto dalla catena di hash.
- **Caricamento dei documenti (`scripts/scomponi_job.py`).** L'organizzazione si indica con `--org`, chi carica con `--utente-sso`. Serve `gestire_dataset_centrale` (i task nuovi entrano nel dataset condiviso), verificato prima di chiamare il modello. Ogni documento caricato lascia un atto `approvazione` di tipo `caricamento_documento` con oggetto il documento; nome del file e ruolo stanno nello spazio con la motivazione. Scelta: un atto per documento, non per esecuzione, perché ogni documento ha le sue occorrenze; un rilancio lascia un altro atto con zero occorrenze nuove. Il caricamento richiede la connessione diretta: via HTTPS l'atto non troverebbe il suo testo nello spazio.
- **Giudizi del crosswalk conservati (migrazione 0027).** La fusione non cancella più i giudizi del crosswalk del task fuso; la tabella è append-only e il ruolo applicativo non ha più il permesso di cancellarli. La vista `v_crosswalk_giudizi` li marca (`task_fuso`, `fuso_in`) ricavando lo stato da `canonical_tasks`, senza modificare il giudizio: dopo una scissione tornano validi così come sono. Le relazioni del task fuso (`task_mappings`) si spostano ancora sul superstite e si cancellano dal fuso: restano un seguito.
- **Note dei revisori nello spazio (migrazione 0028, migrazione 0007 degli spazi).** `giudizi_revisione.nota` è testo libero: sta in `org_<codice>.note_giudizi`, e in `public` resta `hash_nota`, l'impronta con la chiave dello spazio. Il database controlla che la nota corrisponda all'impronta e appartenga a un giudizio della stessa organizzazione. Le note già presenti si spostano all'applicazione della migrazione degli spazi; il vincolo `giudizi_nota_nello_spazio` è `NOT VALID` e va convalidato con una migrazione successiva, dopo l'applicazione in produzione.
- **Elementi dei campioni (migrazione 0029).** Ogni elemento nuovo richiede che il campione, a fine transazione, abbia esattamente la sua dimensione: un elemento aggiunto dopo la creazione è rifiutato anche prima del primo giudizio.
- **Misure coerenti con i parametri (migrazione 0030).** Soglia, livello di confidenza e regola sui parziali di una misura devono coincidere con il valore dei parametri che cita.
- **Richieste di ricalibrazione.** La lettura lascia una voce nel log di accesso per ogni organizzazione letta, e ogni richiesta dice se è superata, cioè se la versione comune a cui si riferisce non è più vigente.

## 16. Fase 3: abbinamento al dataset consolidato (2026-10-17)

Realizzazione tecnica della canonicalizzazione rivista (handover, sezione 3), ADR 0006. Scelte tecniche, che non cambiano risultati di policy:
- la proposta è il task attivo più vicino per embedding; si registrano i 5 vicini, la distanza e il margine sul secondo; nessuna soglia di distanza;
- la coda di revisione è ordinata per ambiguità (margine crescente, poi distanza decrescente): un ordinamento, non un filtro;
- la dimensione del campione è la quota del lotto per il numero di proposte, arrotondata per eccesso; la quota usata è quella vigente quando il lotto nasce;
- con revisione a campione o completa la decisione in blocco richiede una misura sul campione del lotto, il cui esito entra nell'atto; con revisione nulla la decisione si registra come tale;
- una proposta senza task vicino (dataset vuoto) è rifiutata d'ufficio e diventa task nuovo; un task proposto fuso nel frattempo si segue fino al superstite.

Dopo le revisioni Python e database della fase 3:
- un solo campione per lotto (indice nel database): la misura non si sceglie fra più estrazioni; la decisione verifica che la misura copra esattamente la dimensione prevista dalla quota (aritmetica decimale) o tutte le proposte con revisione completa;
- un lotto senza proposte con un task (dataset vuoto) si decide senza misura, e l'atto lo dice (`proposte_con_task` = 0);
- le proposte giudicate errate o parziali nel campione e non rifiutate si contano nell'atto (`campione_non_corrette_approvate`);
- un task proposto ritirato prima dell'applicazione ferma l'applicazione del lotto; un task fuso si segue fino al superstite;
- il database controlla che lotti, decisioni e applicazioni citino l'atto giusto della stessa organizzazione, che le decisioni e le applicazioni coprano il lotto intero con un solo atto, e che un'applicazione segua la decisione.

**Da decidere (metodologia):** chi sceglie il livello di revisione del lotto (oggi chi propone il lotto, con `gestire_dataset_centrale`); valore di `quota_revisione_abbinamenti`; approvazione di `istruzioni-abbinamento-v1`; se una decisione in blocco con misura sotto soglia vada impedita (oggi si registra); come il livello di revisione del lotto incide sullo stato dei risultati (oggi si registra con i risultati); se aggiungere un giudizio del modello sulle proposte.

## 17. Calcolo di N e D, quota dei lotti di abbinamento (2026-10-17)

Approvate dal responsabile del progetto.
- **D senza survey.** Finché d3 e d4 non sono raccolti (solo con survey, mai con il modello), D si calcola come provvisorio su d1 e d2, con i loro pesi del profilo riportati a somma 1. Ogni risultato lo dichiara ("provvisorio: mancano d3 e d4") e non può motivare una riorganizzazione.
- **Incertezza nella simulazione.** Nelle 2.000 estrazioni Monte Carlo ogni voce si estrae dai giudizi registrati per quella voce; se esistono giudizi di persone, sostituiscono quelli del modello. La copertura tecnologica si estrae uniformemente fra `c_low` e `c_high`. Il seme è fisso e registrato: stesso input, stesso risultato.
- **Capacità per N.** Finché la capacità di test non è calibrata sulla scala 0–4, N usa la **copertura di riserva** della rubrica (0 nessuna soluzione dimostrata … 4 esecuzione autonoma affidabile documentata), con qualità minima, dichiarata nei risultati come capacità di riserva.
- **Abbinamento.** Quota comune di revisione a campione `quota_revisione_abbinamenti` = 0,20. Il livello di revisione di un lotto (`campione`, `completa`, `nulla`) lo sceglie il revisore con un atto, non chi propone il lotto.

## 18. Fase 4: calcolo di N e D, scelte tecniche e punti aperti (2026-10-17)

Realizzazione delle decisioni della sezione 17 (piano `docs/piani/fase-4-calcolo-n-d.md`). Scelte tecniche:
- quadrante: N alto se N ≥ θ_N e D alto se D ≥ θ_D (confronto a 9 decimali);
- giudizi: di persona sull'occorrenza, poi di persona sul task, poi del modello sull'occorrenza, poi del modello sul task; di ogni persona conta l'ultimo giudizio sulla voce; i giudizi su task poi fusi valgono per il superstite (sezione 8);
- ogni risultato porta profilo, snapshot, rubrica, versione del calcolo, seme, estrazioni, tipo di capacità, componenti di D, numero di giudizi per voce, task e ruolo dell'occorrenza e un'impronta di tutti gli input (anche dei valori del profilo); i risultati non si modificano;
- un profilo di pesi o una rubrica approvati non cambiano valori: un cambio è un profilo o una rubrica nuovi; l'applicazione li registra solo come bozze;
- lo snapshot di capacità nasce proposto, si pubblica solo con l'atto di approvazione, e la sua copertura non cambia dopo; nello snapshot di riserva tutte le evidenze hanno la stessa classe di qualità (con qualità diverse servono pesi di qualità approvati); l'intervallo è dato dalle evidenze che pesano;
- le etichette silver v2 si importano come giudizi di modello sotto la rubrica `bozza-3`, registrata come bozza.

**Punti aperti (metodologia):**
- con la copertura estratta uniformemente fra c_low e c_high (sezione 17), la media pesata con il decadimento (c_mean) non entra in N: l'emivita cambia solo un valore informativo; un'alternativa è una distribuzione centrata su c_mean;
- con una sola evidenza di riserva per dimensione l'intervallo è nullo, e N risulta senza incertezza dalla copertura;
- ogni voce si estrae a sé anche quando i giudizi vengono dalla stessa esecuzione del modello;
- la copertura di riserva proposta dal modello non ha ancora un set di controllo umano;
- in produzione mancano: rubrica corrente approvata (oggi solo `bozza-3`), profilo di pesi approvato, snapshot pubblicato, quote di tempo delle occorrenze (servono alla lettura per ruolo).
