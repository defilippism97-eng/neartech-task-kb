# Neartech — Piano di sviluppo V2 della knowledge base dei task

Oct 8, 2026 · @Marco De Filippis

**Come leggere questo documento.** Le prime quattro sezioni bastano per capire il progetto: cosa costruiamo, le parole chiave, la matrice e un esempio svolto. Le sezioni successive spiegano come funziona la misura, da dove vengono i dati e come lavora il sistema. Chiudono validazione, regole, tempi, rischi e decisioni da prendere. Lo schema tecnico del database è in appendice.

## Il progetto in breve

**Il problema.** Le organizzazioni vogliono adottare l'intelligenza artificiale, ma non sanno quali attività del lavoro affidarle, quali affiancare con l'AI e quali proteggere. Le risposte oggi disponibili sono generiche ("l'AI farà questo mestiere") oppure basate su opinioni, e ignorano una domanda decisiva: *le persone e gli utenti vogliono davvero che quel compito resti umano?*

**La soluzione.** Neartech costruisce una knowledge base (KB) che descrive il lavoro attività per attività (i "task") e per ciascuna misura due cose:

- **N, necessità dell'apporto umano**: quanto serve ancora una persona, per limiti tecnici, oggi.

- **D, desiderabilità dell'apporto umano**: quanto vale che a farlo sia una persona, per ragioni etiche, relazionali, di fiducia e di senso del lavoro.

Incrociando N e D, ogni task cade in uno di quattro quadranti, e ogni quadrante suggerisce un'azione diversa (sezione successiva).

**Cosa produce per un'organizzazione cliente.**

- Una mappa dei task di ogni ruolo, con il quadrante e il grado di certezza della stima.

- Per ogni ruolo, un punto medio sulla matrice e un indice di eterogeneità: i ruoli con task molto dispersi tra quadranti diversi sono i candidati naturali a una riprogettazione.

- Per ogni numero, la fonte, la data e la versione del metodo che lo ha prodotto, così da poter spiegare il risultato a dirigenti, sindacati e lavoratori.

**Tre principi che guidano tutto il piano.**

1.  **Nessun numero senza prova.** Ogni valore dichiara da quale evidenza viene, quando è stato osservato e con quale incertezza.

2.  **N si basa sui dati, D sulle persone.** N deriva da cosa la tecnologia ha dimostrato di saper fare; D dalle preferenze raccolte da chi lavora e da chi riceve il servizio. L'intelligenza artificiale aiuta a collegare e a estrarre informazioni, ma non inventa i punteggi.

3.  **Gli agenti propongono, il codice calcola, le persone decidono.** La KB si aggiorna da sola nel tempo, ma tutto ciò che cambia un risultato passa da un'approvazione umana.

**Come si parte.** Un'azienda pilota nei servizi alla persona fornisce i primi documenti di lavoro. In circa 16 settimane la KB deve poter essere usata in produzione su quel dominio; entro la settimana 24 deve mantenersi aggiornata in modo autonomo, sotto supervisione.

## Glossario per chi inizia

| Termine                      | Significato                                                                                                                                                        |
|------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Task**                     | Una singola attività di lavoro, scritta con un verbo e un oggetto. Esempio: "Comporre il piano turni settimanale del servizio"                                     |
| **Task canonico**            | Il task riscritto in forma standard e indipendente dall'azienda, in modo che lo stesso compito descritto in modi diversi da aziende diverse diventi un solo record |
| **Occorrenza**               | Un task canonico dentro un ruolo preciso di un'azienda, con il tempo che occupa e il contesto in cui si svolge. D si misura qui, perché dipende dal contesto       |
| **N e D**                    | Necessità e desiderabilità dell'apporto umano, entrambe su scala da 0 a 1                                                                                          |
| **Quadrante**                | Una delle quattro zone della matrice N/D, ciascuna con una raccomandazione d'azione                                                                                |
| **Tassonomia**               | Un catalogo ufficiale di professioni e attività. Usiamo O\*NET (Stati Uniti), ESCO (Europa) e l'Atlante del Lavoro INAPP (Italia)                                  |
| **Collegamento (crosswalk)** | La corrispondenza tra un nostro task canonico e una voce di una tassonomia. Serve per usare i dati internazionali sui task italiani                                |
| **Evidenza**                 | Un dato osservabile sulla capacità dell'AI: uso reale, tasso di successo, risultato di un benchmark, giudizio di un esperto, esito di un pilota interno            |
| **Domanda del task**         | Quanto un task richiede su una dimensione (per esempio giudizio). È una caratteristica stabile del task                                                            |
| **Copertura tecnologica**    | Quanto la tecnologia disponibile a una certa data copre in modo affidabile quel livello di domanda. Cambia nel tempo                                               |
| **Snapshot**                 | La fotografia della copertura tecnologica a una data, approvata da un curatore. Ogni ricalcolo usa uno snapshot preciso                                            |
| **Rubrica**                  | La scala 0–4 con descrizioni ed esempi concreti per ogni livello, usata per valutare i task                                                                        |
| **Panel**                    | Il gruppo di 3–5 persone (HR, linea, rappresentanza dei lavoratori, voce dei beneficiari) che valuta i task con la rubrica                                         |
| **Gold standard**            | Un insieme di 200 task valutati dal panel, usato per tarare e verificare il sistema                                                                                |
| **HITL (human in the loop)** | La coda dei casi incerti che una persona deve rivedere, e la regola secondo cui le decisioni di policy sono umane                                                  |
| **Azienda pilota**           | La prima organizzazione che fornisce documenti e partecipanti alle survey per mettere alla prova il metodo                                                         |
| **Comitato di governance**   | Per ogni cliente, il gruppo che decide pesi, soglie e rubrica: direzione HR, responsabili di linea, rappresentanza dei lavoratori, DPO se presente                 |

## La matrice N/D

Ogni task occupa un punto sulla matrice, e la zona in cui cade suggerisce cosa farne.

<img src="media/image1.png" style="width:6in;height:4.44643in" alt="matrice N/D · 4 quadranti" />

matrice N/D · 4 quadranti

| Quadrante                             | Che cosa significa                                                      | Azione tipica                                                   |
|---------------------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------|
| **Q1 Baluardo umano**                 | La tecnologia non basta e la presenza umana è voluta                    | Proteggere, valorizzare, investire nella formazione             |
| **Q2 Collo di bottiglia transitorio** | Serve una persona solo perché la tecnologia non è ancora affidabile     | Monitorare: può passare a Q4 o Q3 quando migliora la tecnologia |
| **Q3 Scelta di valore**               | La macchina potrebbe farlo, ma l'organizzazione sceglie che resti umano | Decisione consapevole: mantenere, rendere esplicita la scelta   |
| **Q4 Automazione pura**               | Nessun vincolo tecnico e nessun valore nella presenza umana             | Automatizzare, liberando tempo per gli altri quadranti          |

La soglia tra "bassa" e "alta" è fissata di default a 0,50 sia per N sia per D, ma è un parametro che ogni cliente può modificare tramite il proprio comitato di governance.

### Dal task al ruolo

Il valore per il cliente sta soprattutto nella lettura per ruolo. Per ogni ruolo calcoliamo:

- **il baricentro**: il punto medio dei suoi task sulla matrice, pesato per il tempo che ciascun task occupa;

- **la dispersione**: quanto i task del ruolo sono lontani dal baricentro. Un ruolo con task sparsi su quadranti diversi è il candidato naturale a una riprogettazione;

- **la stabilità**: quanta parte del tempo del ruolo è composta da task il cui quadrante è stimato con buona certezza.

## Un esempio svolto

Due task di un servizio socio-assistenziale mostrano come si arriva al quadrante. **I valori sono illustrativi, scelti per spiegare il metodo, e non sono misure reali.** Pesi usati nell'esempio: variabilità dell'input 0,4; giudizio 0,4; componente fisica 0,2; criticità dell'errore con λ = 0,5; le quattro componenti di D con peso 0,25 ciascuna.

|                                                                                | Task A: comporre il piano turni settimanale    | Task B: condurre il colloquio con la famiglia dopo un peggioramento                  |
|--------------------------------------------------------------------------------|------------------------------------------------|--------------------------------------------------------------------------------------|
| **Domanda del task** (variabilità input, giudizio, fisica)                     | 2, 2, 0                                        | 3, 3, 1                                                                              |
| **Copertura tecnologica oggi** (stessa scala, dalle evidenze)                  | 3, 2, 4                                        | 1, 1, 2                                                                              |
| **Gap** = domanda meno copertura, solo se positivo                             | 0, 0, 0                                        | 2, 2, 0 (su scala 0–4)                                                               |
| **Criticità dell'errore** (0–4)                                                | 2                                              | 3                                                                                    |
| **N**                                                                          | 0,00                                           | 0,55                                                                                 |
| **D**: relazione, responsabilità, senso del lavoro, valore per il beneficiario | 1, 2, 1, 0                                     | 4, 3, 4, 4                                                                           |
| **D (valore finale)**                                                          | 0,25                                           | 0,94                                                                                 |
| **Quadrante**                                                                  | **Q4 Automazione pura**                        | **Q1 Baluardo umano**                                                                |
| **Che cosa si dice al cliente**                                                | Automatizzare: i coordinatori recuperano tempo | Proteggere: il compito richiede competenza umana oggi e le persone lo vogliono umano |

Dove arrivano i numeri nel caso reale: la copertura viene da evidenze con fonte e data (per esempio uso e successo osservati su compiti equivalenti), D da panel e survey. Se tra sei mesi uno snapshot aggiornato alzasse la copertura del task B, N scenderebbe da solo e il task si sposterebbe verso sinistra. Il suo D alto lo terrebbe comunque nella parte alta: sarebbe un candidato alla zona Q3, cioè a una scelta di valore dell'organizzazione.

## Come si misura N

N è la distanza tra ciò che il task richiede e ciò che la tecnologia ha dimostrato di saper fare a una certa data. Se la tecnologia copre già la richiesta, N è zero. Se la richiesta supera la copertura, N cresce.

### Le tre dimensioni della domanda

Per ogni task si valutano tre dimensioni, ciascuna su scala 0–4 con la rubrica:

- **k1, variabilità dell'input**: quanto il materiale di partenza è strutturato, completo e prevedibile.

- **k2, giudizio**: quanto serve valutare e bilanciare vincoli in condizioni di incertezza.

- **k3, componente fisico-percettiva**: quanta manipolazione o percezione in ambiente reale richiede.

A queste si aggiunge la **criticità dell'errore r** (0–4). Non è una quarta dimensione da sommare: è un moltiplicatore. Un errore grave alza la soglia di affidabilità richiesta e quindi amplifica il divario che resta, ma non crea necessità umana dove il divario è nullo.

### La formula

Per ciascuna dimensione k, alla data t, il divario è la parte della domanda dₖ non coperta dalla tecnologia cₖ(t), riportata su scala 0–1:

g_k(t) = \frac{\max(0,\\ d_k - c_k(t))}{4}

N è la somma pesata dei divari, amplificata dalla criticità dell'errore e limitata a 1:

N(t) = \min\Big(1,\\ \sum\_{k=1}^{3} w_k \\ g_k(t) \cdot \big(1 + \lambda \\ \tfrac{r}{4}\big)\Big)

I pesi wₖ (somma 1) e il parametro λ sono scelte di governance del cliente, versionate e approvate dal suo comitato.

### Come si stima la copertura tecnologica

La copertura non si decide a tavolino: si calcola dalle evidenze raccolte. Ogni evidenza e, riferita a un task, porta un valore normalizzato su 0–4 e viene pesata:

c_k(t) = \frac{\sum_e q_e \\ m_e \\ 2^{-(t - t_e)/h} \\ s_e}{\sum_e q_e \\ m_e \\ 2^{-(t - t_e)/h}}

- **qₑ, qualità dell'evidenza.** Gerarchia: benchmark misurato su un task equivalente, poi uso osservato con successo, poi pilota interno, poi giudizio di esperti, infine stima preliminare dell'LLM.

- **mₑ, forza del collegamento.** 1 se l'evidenza si riferisce esattamente al nostro task; meno se la corrispondenza è più ampia o solo affine.

- **Decadimento nel tempo.** Il peso di un'evidenza si dimezza ogni h giorni. La capacità degli agenti AI cresce molto in fretta (le misure pubbliche di METR indicano un raddoppio della durata dei compiti completati in circa 4 mesi), quindi un dato vecchio vale meno. Punto di partenza: h pari a 6 mesi, da tarare con la verifica a posteriori.

- **Incertezza.** Il disaccordo tra le fonti allarga l'intervallo attorno a cₖ(t). Fonti in conflitto producono una stima incerta, non una media rassicurante.

### Perché N si aggiorna da solo

La domanda del task non cambia. Cambia la copertura, quando arrivano nuove evidenze. Ogni mese il sistema propone uno snapshot aggiornato; dopo l'approvazione del curatore N viene ricalcolato per tutti i task. Una variazione tecnologica non richiede quindi di toccare pesi o rubrica: si pubblica un nuovo snapshot.

## Come si misura D

D non è una proprietà tecnica del task: riflette cosa vogliono le persone coinvolte e quali valori l'organizzazione decide di proteggere. Per questo non si deduce da un modello, ma si raccoglie da chi ha titolo per rispondere, e dipende dal contesto di ruolo in cui il task si svolge.

### Quattro componenti, ciascuna con la sua fonte

| Componente                        | Domanda di fondo                                                                          | Chi risponde                                                                               |
|-----------------------------------|-------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| **d1 Relazione e fiducia**        | Quanto conta la presenza umana nel rapporto con l'altra persona?                          | Panel di esperti                                                                           |
| **d2 Responsabilità**             | Il task incide su diritti, carriere, risorse individuali o è un atto riservato per legge? | Panel di esperti                                                                           |
| **d3 Senso del lavoro**           | Se il task sparisse dal lavoro, il lavoro sarebbe migliore o snaturato?                   | Chi svolge il task, tramite survey                                                         |
| **d4 Valore per il beneficiario** | Se lo svolgesse un sistema automatico con la stessa qualità tecnica, sarebbe accettabile? | Utenti, clienti o chi li rappresenta (familiari, coordinatori di servizio), tramite survey |

Ogni componente ha una scala 0–4 (la rubrica è nella sezione dedicata). D è la media pesata delle quattro componenti, riportata su scala 0–1. I pesi sono una scelta del comitato di governance del cliente.

Le quattro componenti possono entrare in conflitto: il lavoratore può vivere come un peso un compito che il beneficiario vuole umano. Per questo il dato primario conservato sono sempre i quattro punteggi separati, e D è una vista calcolata a valle con un profilo di pesi approvato.

### Il punto di partenza: la stima preliminare

Quando non esiste ancora un dato raccolto, un modello linguistico produce una stima preliminare di ciascuna componente. Questa stima:

- è sempre etichettata come "preliminare" e conservata a parte;

- viene sostituita dal dato di panel o di survey non appena disponibile;

- se rappresenta oltre il 30% del tempo di un ruolo, rende provvisori tutti i risultati di quel ruolo, che non possono motivare una riorganizzazione.

Dove esiste una corrispondenza con il dataset WORKBank di Stanford, il livello di coinvolgimento umano preferito dai lavoratori statunitensi (scala H1–H5) entra come ulteriore indicazione sul senso del lavoro, con peso ridotto.

### Regole per le survey

- Al massimo 12 task per questionario, per contenere la stanchezza.

- Risposte pseudonimizzate alla raccolta, conservate separatamente dalle anagrafiche.

- Risultati mostrati solo in forma aggregata, con almeno 5 rispondenti per gruppo.

- Ai partecipanti si restituiscono i risultati della propria campagna.

### Le soglie e l'incertezza

Le soglie che separano i quadranti (di default 0,50 per N e per D) sono parametri del cliente, versionati e approvati dal comitato di governance. Il quadrante non è un'etichetta secca. Il sistema simula più volte N e D a partire dalla loro incertezza e calcola la probabilità che il task cada in ciascun quadrante. Un task è considerato **stabile** se il quadrante più probabile supera l'80%, altrimenti va in revisione umana.

## La rubrica di valutazione

La rubrica traduce giudizi soggettivi in scale a 5 livelli (0–4) con un esempio concreto per ogni livello. Due regole la rendono affidabile: le descrizioni dell'asse N non contengono mai riferimenti etici o relazionali (che appartengono a D), e viceversa. Così i due assi restano distinti. Gli esempi qui sotto vanno sostituiti con task reali dell'azienda pilota prima della taratura del panel.

### Domanda del task (asse N)

| Livello | k1 Variabilità dell'input                                                                                    | k2 Giudizio                                                                                           | k3 Componente fisico-percettiva                                                         |
|---------|--------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| 0       | Input strutturato e completo. Es.: registrare presenze da badge                                              | Regole esaustive. Es.: calcolare maggiorazioni da contratto collettivo                                | Nessuna. Es.: redigere un verbale                                                       |
| 1       | Semi-strutturato con varianti note. Es.: registrare fatture fornitori                                        | Scelta tra opzioni documentate. Es.: assegnare una sostituzione da graduatoria                        | Dispositivi standard. Es.: stampare e archiviare                                        |
| 2       | Non strutturato in un dominio delimitato. Es.: sintetizzare una relazione di servizio                        | Bilanciare 2–3 vincoli noti. Es.: comporre turni con vincoli orari e di competenza                    | Manipolazione ordinaria in ambiente stabile. Es.: riordinare il magazzino presidi       |
| 3       | Incompleto o contraddittorio, va ricostruito. Es.: ricostruire il bisogno di un utente da famiglia e servizi | Dati incompleti, senza precedenti standard. Es.: rivedere un progetto educativo dopo un peggioramento | Manipolazione o percezione in ambiente variabile. Es.: igiene della persona a domicilio |
| 4       | Contesto aperto che cambia durante l'esecuzione. Es.: gestire un'uscita educativa con imprevisti             | Sintesi inedita in scenari mai visti. Es.: riorganizzare un servizio in emergenza                     | Intervento fine e non pianificabile su persone. Es.: soccorrere un utente caduto        |

**Criticità dell'errore r** (moltiplicatore): 0 reversibile senza effetti; 1 intercettato dai controlli ordinari; 2 richiede rilavorazione o chiarimento con terzi; 3 danno economico, legale o reputazionale rilevante; 4 danno irreversibile a salute, sicurezza o diritti fondamentali.

**Copertura tecnologica di riserva**, usata solo per dimensioni senza evidenze esterne e sempre con qualità minima: 0 nessuna soluzione dimostrata; 1 dimostrata in ricerca o demo; 2 strumenti commerciali con supervisione costante; 3 uso diffuso con revisione a campione; 4 esecuzione autonoma affidabile documentata.

### Desiderabilità (asse D)

Per d3 e d4 la scala deriva dalla risposta a una domanda diretta; più il livello è alto, più pesa la presenza umana.

| Livello | d1 Relazione e fiducia (panel)                                                | d2 Responsabilità (panel)                                                          | d3 Senso del lavoro (lavoratori): "Se questo compito sparisse dal tuo lavoro, il tuo lavoro sarebbe…" | d4 Valore per il beneficiario (utenti): "Se lo svolgesse un sistema automatico con la stessa qualità tecnica, per te sarebbe…" |
|---------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| 0       | Transazione funzionale. Es.: comunicare un orario                             | Nessun effetto su diritti o doveri                                                 | Molto migliore: è un peso che sottrae tempo                                                           | Preferibile                                                                                                                    |
| 1       | Cortesia procedurale. Es.: fissare un appuntamento                            | Applicazione di regola senza discrezionalità. Es.: calcolo delle ferie             | Un po' migliore                                                                                       | Indifferente                                                                                                                   |
| 2       | Supporto che aumenta la chiarezza. Es.: spiegare una pratica                  | Verifica di conformità interna. Es.: controllare la completezza di una cartella    | Uguale                                                                                                | Leggermente peggiore                                                                                                           |
| 3       | Relazione d'aiuto o mediazione. Es.: colloquio con una famiglia in disaccordo | Incide su diritti, carriera o risorse individuali. Es.: contestazione disciplinare | Più povero                                                                                            | Chiaramente peggiore                                                                                                           |
| 4       | Vulnerabilità acuta, lutto, crisi. Es.: accompagnare un utente nel fine vita  | Atto riservato per legge a una figura abilitata                                    | Snaturato                                                                                             | Inaccettabile                                                                                                                  |

### Regole di somministrazione

- N e D si valutano in chiamate o sessioni separate, per evitare che il giudizio su uno influenzi l'altro (effetto alone).

- Un modello linguistico valuta ogni voce con 5 campioni indipendenti; si conservano tutti i campioni, non solo il valore centrale.

- Ogni modifica a un'ancora crea una nuova versione della rubrica; le valutazioni restano legate alla versione con cui sono state prodotte.

- Le scale sono ordinali e ancorate a priori, non derivate da incidenti critici raccolti con gli esperti. Sarà la misura di accordo tra valutatori a dire se reggono.

## Fonti dei dati

Non partiamo da zero. Esiste già un framework molto vicino alla nostra matrice e diversi dataset pubblici che misurano capacità e uso dell'AI task per task. Quasi tutti sono ancorati a O\*NET, il catalogo statunitense dei task di lavoro, quindi collegare i task italiani a O\*NET è il passaggio che sblocca il riuso di tutto il resto.

### Evidenze sulla capacità della tecnologia

| Fonte                                                                                                                                  | Cosa misura                                                                                                                             | Come la usiamo                                                                                                                                                           | Asse     |
|----------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| [WORKBank, Stanford](https://arxiv.org/abs/2506.06576v2) (2025)                                                                        | Desiderio di automazione dei lavoratori e capacità stimata da esperti AI, task per task, in quattro zone                                | Validazione esterna della nostra matrice; scala [H1–H5](https://futureofwork.saltlab.stanford.edu) di coinvolgimento umano come riferimento per le domande ai lavoratori | N e D    |
| [Anthropic Economic Index](https://www.anthropic.com/economic-index)                                                                   | Uso reale dell'AI mappato su task O\*NET, con distinzione tra automazione e affiancamento e, nei rilasci più recenti, successo per task | Evidenza di uso e di successo con serie storica tra rilasci                                                                                                              | N        |
| [Microsoft, Working with AI](https://arxiv.org/html/2507.07935v5) (2025)                                                               | 200.000 conversazioni di un assistente AI classificate su attività O\*NET, con punteggio di applicabilità                               | Seconda misura indipendente dell'uso, per confrontare le fonti                                                                                                           | N        |
| [GDPval, OpenAI](https://arxiv.org/pdf/2510.04374) (2026)                                                                              | Qualità dei risultati dei modelli su 1.320 compiti reali di 44 occupazioni, giudicata da professionisti                                 | Evidenza di qualità sulle attività della conoscenza; metodo di valutazione a confronto cieco riusabile nel pilota                                                        | N        |
| [METR](https://en.wikipedia.org/wiki/METR)                                                                                             | Durata dei compiti che gli agenti AI completano con una data affidabilità                                                               | Indicatore di frontiera per il decadimento delle evidenze e per i task lunghi                                                                                            | N        |
| [ILO, Working Paper 140](https://www.ilo.org/node/706766) (2025)                                                                       | Esposizione all'AI generativa di circa 30.000 task, con validazione umana                                                               | Stima di partenza per professioni europee                                                                                                                                | N        |
| [INAPP, WP 125](https://oa.inapp.gov.it/server/api/core/bitstreams/3fa70c6b-dbdf-4232-95ef-08590a16a5a0/content) (2024)                | Esposizione all'AI applicata alle attività dell'Atlante del Lavoro                                                                      | Ponte verso le classificazioni italiane                                                                                                                                  | N        |
| [McKinsey Global Institute](https://www.mckinsey.com/mgi/our-research/agents-robots-and-us-skill-partnerships-in-the-age-of-ai) (2025) | Potenziale tecnico di automazione e collaborazione persone–agenti–robot                                                                 | Solo inquadramento e linguaggio per i clienti                                                                                                                            | Contesto |

### Tassonomie a cui agganciamo i task

| Tassonomia                                                                                                        | Versione di riferimento | Uso                                                | Aggiornamento |
|-------------------------------------------------------------------------------------------------------------------|-------------------------|----------------------------------------------------|---------------|
| [O\*NET](https://www.onetcenter.org/dictionary/31.0/jsonld/hasTask.html): task, attività dettagliate e intermedie | 31.0                    | Ancoraggio principale                              | Trimestrale   |
| [ESCO](https://esco.ec.europa.eu/et/node/563): professioni e competenze                                           | 1.2.1 (dicembre 2025)   | Ponte europeo e multilingue, etichette in italiano | Annuale       |
| Atlante del Lavoro INAPP                                                                                          | Corrente                | Lessico e repertori italiani                       | Irregolare    |

### Tre avvertenze sull'uso delle fonti

- **Uso osservato non è capacità.** Molti dati registrano chi usa un certo prodotto, soprattutto negli Stati Uniti. Un task poco presente può essere automatizzabile ma non ancora adottato. Per questo l'uso pesa meno del successo misurato e dei benchmark.

- **Esposizione non è impatto.** Le stime di ILO, INAPP e McKinsey misurano un potenziale tecnico, non ciò che le organizzazioni scelgono di fare. È lo spazio che D deve occupare.

- **Il vuoto da colmare è D in contesto italiano.** Nessuna fonte misura la desiderabilità dell'apporto umano dal punto di vista dei beneficiari, né copre bene i servizi alla persona e il terzo settore. È qui che Neartech produce dati originali.

### I quattro strati di dati

| Strato               | Contenuto                                         | Esempi                                                                 |
|----------------------|---------------------------------------------------|------------------------------------------------------------------------|
| L0 Tassonomie        | Cataloghi ufficiali                               | O\*NET, ESCO, Atlante del Lavoro                                       |
| L1 Evidenze esterne  | Dati pubblici sulla tecnologia e sulle preferenze | Le fonti della prima tabella                                           |
| L2 Dati dell'azienda | Documenti e dati organizzativi                    | Mansionari e job description, interviste, ore per ruolo dal sistema HR |
| L3 Misure proprie    | Dati raccolti da Neartech                         | Valutazioni del panel, survey, piloti interni                          |

Le licenze di ogni fonte vengono registrate prima del primo caricamento. L'Anthropic Economic Index è pubblicato con licenza CC-BY; per le altre fonti la verifica va fatta caso per caso.

## Dal documento dell'azienda al task standard

I documenti delle aziende (mansionari, job description, interviste) descrivono lo stesso lavoro in modi molto diversi. Prima di misurare qualsiasi cosa, il sistema li trasforma in task standard e li collega alle tassonomie, in cinque passaggi.

1.  **Scomposizione.** Un modello linguistico divide le descrizioni composite in attività singole. "Accogliere l'utente e raccogliere la documentazione" diventa due task.

2.  **Forma canonica.** Ogni task viene riscritto nella grammatica fissa: *verbo all'infinito + oggetto + strumento o vincolo + finalità*. Esempio: "Comporre il piano turni settimanale del servizio rispettando orari e competenze, per garantire la copertura dei turni". Ogni task canonico ha un livello di granularità esplicito, fissato con esempi, perché la scomposizione tende a frammentare troppo.

3.  **Deduplicazione.** Gli embedding (rappresentazioni numeriche del significato di un testo) trovano i task molto simili. Una persona approva le fusioni. Le soglie di somiglianza si fissano per percentile sulla distribuzione reale dei dati, non con numeri assoluti, perché cambiano da modello a modello.

4.  **Collegamento alle tassonomie.** Per ogni task canonico si cercano, con gli embedding, i 20 nodi più vicini in ciascuna tassonomia. Un modello linguistico giudica ogni candidato con una relazione standard: esatta, più ampia, più stretta, affine, nessuna. Si salvano solo le relazioni diverse da "nessuna", ciascuna con una breve motivazione.

5.  **Controllo.** Un campione casuale del 10% delle corrispondenze esatte viene rivisto da una persona. Se la precisione misurata scende sotto il 90%, il collegamento automatico si ferma.

### Perché gli embedding servono qui e non per calcolare N e D

Gli embedding misurano quanto due testi si assomigliano per significato, non quanto richiedono giudizio o quanto sono desiderabili da svolgere per una persona. Due task quasi identici nel testo, come "redigere un verbale di riunione" e "redigere un verbale di contestazione disciplinare", hanno N e D molto diversi. Per questo gli embedding si usano solo per trovare duplicati, collegare le tassonomie, riconoscere se un nuovo task esiste già e suggerire percorsi di riqualificazione. N e D si ricavano da evidenze e valutazioni.

### Come entrano le evidenze esterne

Le evidenze sono agganciate ai nodi delle tassonomie, non ai nostri task. L'agganciamento avviene tramite i collegamenti del passaggio 4. La forza del collegamento (mₑ nella formula) dipende dalla relazione: massima se esatta, ridotta se più ampia o affine. Le evidenze si trasferiscono sui nostri task solo attraverso relazioni esatte o più strette, mai attraverso relazioni vaghe.

### Primo dominio da caricare

Il pilota parte dalle job description dell'azienda pilota, già organizzate in un formato che esplicita aree di responsabilità, output, risultati attesi e indicatori misurabili. Sono un materiale ideale per tre ragioni: i task sono già quasi pronti per la scomposizione, riguardano i servizi alla persona dove le fonti internazionali sono più deboli, e il contenuto è già stato validato in riunioni di revisione.

## Il modello dati in parole semplici

La KB vive in un unico database PostgreSQL con l'estensione pgvector, che gestisce sia i dati tabellari sia gli embedding. Per qualche migliaio di task è la scelta più semplice e controllabile: niente database vettoriale separato. Lo schema tecnico completo è in appendice.

### Le regole di progetto

- **I dati grezzi, i dati normalizzati, le evidenze, le valutazioni e i parametri di governance stanno in tabelle separate.** Si può sempre risalire dal numero finale al documento da cui è partito.

- **Nessuna soglia e nessun peso sono scritti nel codice o nello schema.** Stanno in tabelle di parametri versionate e approvate.

- **Ogni valutazione è un record a sé**, non un valore sovrascritto: si conservano tutti i campioni dei modelli e tutti i giudizi delle persone, con la versione della rubrica con cui sono stati prodotti.

- **I risultati calcolati si salvano con le chiavi di ciò che li ha prodotti**: profilo di pesi, snapshot di copertura, versione della rubrica. Un cambio di parametri non lascia mai numeri vecchi mescolati ai nuovi.

### Le tabelle principali

| Gruppo               | Tabelle                                               | A cosa servono                                                                                            |
|----------------------|-------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| Fonti                | sources, taxonomy_nodes                               | Registro delle fonti con versione, licenza e impronta; nodi delle tassonomie                              |
| Task                 | canonical_tasks, task_mappings, task_embeddings       | Task standard, collegamenti alle tassonomie, vettori per modello di embedding                             |
| Aziende e ruoli      | organizations, roles, task_occurrences                | Dove e come ciascun task compare in un ruolo, con tempo occupato e frammento originale                    |
| Capacità tecnologica | evidence_items, capability_snapshots, task_capability | Evidenze normalizzate, fotografie datate della copertura, copertura per task con intervallo di incertezza |
| Valutazioni          | rubric_versions, assessment_runs                      | Versioni della rubrica; ogni singolo giudizio, di modello o di persona                                    |
| Governance           | weight_profiles, steering_directives                  | Pesi, soglie e approvazioni; indirizzi forniti dagli utenti agli agenti                                   |
| Risultati            | policy_estimates                                      | N, D, probabilità di ogni quadrante e quota di D proveniente da stime preliminari                         |
| Esecuzione           | jobs, agent_runs                                      | Coda di lavoro; registro di ogni esecuzione degli agenti con modello, costo e durata                      |

### Come si calcolano i risultati

Un programma Python, avviato da un evento (nuove valutazioni, nuovo snapshot pubblicato, nuovo profilo di pesi attivo), ricalcola i risultati solo per le occorrenze toccate:

1.  Legge tutti i campioni di valutazione per la versione corrente della rubrica, dando precedenza ai giudizi umani su quelli dei modelli per ciascuna voce.

2.  Legge la copertura tecnologica dallo snapshot pubblicato, con il suo intervallo di incertezza.

3.  Esegue 2.000 simulazioni (Monte Carlo) a partire dai campioni e dagli intervalli, applica le formule di N e D e conta in quale quadrante cade ciascuna simulazione.

4.  Scrive media e deviazione di N e D, probabilità di ciascun quadrante e composizione delle fonti di D.

L'aritmetica la fa sempre il codice: il modello linguistico non somma mai i punteggi.

## Il sistema che costruisce e mantiene la KB

La KB non si costruisce una volta sola: un sistema di agenti la alimenta, la aggiorna e la arricchisce nel tempo. Il principio è uno: gli agenti propongono, il codice calcola, le persone approvano tutto ciò che cambia un risultato di policy. Servono sei componenti basati su modelli linguistici e tre deterministici, che lavorano su una coda nel database.

<img src="media/image2.png" style="width:6in;height:6.46428in" alt="sistema di costruzione e aggiornamento · 9 componenti, 3 ruoli umani" />

sistema di costruzione e aggiornamento · 9 componenti, 3 ruoli umani

I dati scendono dalle fonti al calcolo; due anelli risalgono. Gli indirizzi degli utenti orientano il lavoro degli agenti. Giudizi e approvazioni tornano nel database come dati versionati e migliorano le stime successive.

### Ruoli e autonomia di ciascun componente

| Componente           | Tipo                                            | Quando parte                                | Cosa produce                                                 | Autonomia                                                    |
|----------------------|-------------------------------------------------|---------------------------------------------|--------------------------------------------------------------|--------------------------------------------------------------|
| Source Watcher       | Script, con LLM per i riassunti                 | Settimanale                                 | Nuove voci nel registro delle fonti, bollettino delle novità | Registra in automatico dopo controlli di integrità e licenza |
| Canonicalizer        | LLM                                             | Nuovo documento                             | Task canonici, occorrenze, proposte di fusione               | Automatico se la novità è chiara, altrimenti in coda         |
| Crosswalk Mapper     | LLM e embedding                                 | Nuovo task o nuova versione di tassonomia   | Collegamenti con relazione e motivazione                     | Automatico finché la precisione misurata resta almeno al 90% |
| Evidence Extractor   | Script per i dataset, LLM per articoli e report | Nuova fonte di evidenza                     | Evidenze normalizzate su scala 0–4                           | Automatico per fonti già approvate                           |
| Scorer               | LLM                                             | Nuovo task, nuova occorrenza, nuova rubrica | 5 campioni per voce, sempre marcati come di modello          | Automatico                                                   |
| Capability Estimator | Deterministico                                  | Mensile o nuova evidenza rilevante          | Snapshot proposto con nota su cosa è cambiato                | Richiede approvazione del curatore                           |
| Job di calcolo       | Deterministico                                  | A evento                                    | N, D e probabilità di quadrante                              | Automatico                                                   |
| Auditor              | Deterministico                                  | Dopo ogni calcolo                           | Casi per la coda di revisione, avvisi di drift               | Automatico                                                   |
| Sintetizzatore       | LLM                                             | Mensile e su richiesta                      | Report di sintesi con proposte                               | Solo proposte                                                |

### Il ciclo di aggiornamento

1.  **Ogni settimana** il Source Watcher controlla i nuovi rilasci (O\*NET, ESCO, Anthropic Economic Index, GDPval, METR, ILO, preprint selezionati, novità normative) e apre i job di estrazione.

2.  **A ogni nuovo documento** di un cliente, Canonicalizer, Mapper e Scorer lavorano in sequenza; il calcolo aggiorna solo le occorrenze toccate.

3.  **Ogni mese** il Capability Estimator propone un nuovo snapshot con una nota su cosa è cambiato e perché. Dopo l'approvazione del curatore, tutto viene ricalcolato.

4.  **Ogni mese** il Sintetizzatore produce un report: novità nelle fonti, spostamenti di quadrante per famiglia professionale, stato della coda di revisione, proposte su rubrica e fonti.

5.  **Ogni trimestre** il responsabile metodologico rivede set di controllo, rubrica e soglie di approvazione automatica alla luce delle metriche.

### Gli indirizzi degli utenti

I soci e i clienti orientano gli agenti con indirizzi espliciti, per esempio "dai priorità ai servizi educativi" o "escludi fonti di marketing". Ogni indirizzo viene salvato con ambito, priorità e scadenza, e gli agenti lo leggono come configurazione. Un indirizzo può cambiare priorità e perimetro del lavoro, mai pesi, soglie o passaggi di approvazione. Il testo dei documenti caricati è sempre trattato come dato, mai come istruzione: un mansionario che contenesse frasi del tipo "ignora le regole precedenti" non avrebbe alcun effetto.

### Scelte di implementazione

- **Linguaggio e orchestrazione**: Python 3.12, output dei modelli in formati tipizzati (Pydantic), esecuzione asincrona con gestione dei limiti di richiesta e nuovi tentativi progressivi. La coda di lavoro è una tabella jobs letta con FOR UPDATE SKIP LOCKED; lo scheduling è quello del provider cloud.

- **Modelli**: un modello linguistico di frontiera con versione bloccata per Canonicalizer, Mapper, Scorer e Sintetizzatore; bge-m3, un modello di embedding multilingue buono sull'italiano, ospitato da noi.

- **Contratti**: ogni componente è una funzione idempotente con input e output tipizzati. Ogni esecuzione viene registrata con modello, impronta del prompt, durata e costo.

- **Framework a grafo**: lo introdurremo solo se emergono cicli con ramificazioni che una coda e una macchina a stati in tabella non gestiscono in modo leggibile.

## Validazione e monitoraggio

La KB entra in produzione quando il sistema giudica almeno quanto un esperto umano medio, misurato su task che non ha mai visto. Dopo il rilascio, controlli periodici verificano che resti affidabile.

### Il criterio di ingresso in produzione

Su un insieme di task tenuti da parte (l'"hold-out"), si misura quanto il sistema concorda con il giudizio collettivo del panel. Poi si misura quanto concorda, in media, ogni singolo esperto con il giudizio collettivo degli altri. La KB è pronta quando il sistema non fa peggio di un esperto umano sull'asse D, che è il più difficile da misurare. Il criterio si confronta con il limite reale della misura: se gli esperti non concordano tra loro, nessun modello può essere validato e il problema da risolvere diventa la rubrica.

### Il gold standard

- **200 task** stratificati per famiglia professionale e sovracampionati fuori diagonale (Q2 e Q3) e vicino alle soglie, usando una pre-valutazione del modello per scegliere i candidati.

- **Almeno 20 coppie minime**: task quasi identici nel testo ma con requisiti diversi, come i due verbali dell'esempio sopra.

- **Divisione fissa**: 60 task per tarare rubrica ed esempi, 140 task di hold-out mai mostrati al sistema.

- **Panel di 3–5 valutatori**, con almeno un rappresentante dei lavoratori e una voce vicina ai beneficiari. Sessione congiunta di taratura sui primi 20 task, poi valutazione indipendente in cieco, distribuita su più sessioni per evitare la stanchezza.

### Le metriche

| Metrica                                                          | Cosa verifica                                                                | Soglia                                                               | Quando                                        |
|------------------------------------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------------------------|-----------------------------------------------|
| Alfa di Krippendorff per voce (indice di accordo tra valutatori) | Che la rubrica sia applicabile in modo coerente                              | Almeno 0,67 per l'uso; obiettivo 0,80                                | A ogni nuova versione della rubrica           |
| Non-inferiorità del sistema rispetto al panel                    | Accordo sistema–consenso non inferiore all'accordo medio valutatore–consenso | Differenza non peggiore di −0,05 sull'alfa, per asse                 | Prima del rilascio e a ogni cambio di modello |
| Precisione dei collegamenti                                      | Che le corrispondenze esatte siano davvero esatte                            | Almeno 90% sul campione rivisto                                      | Mensile                                       |
| Precisione e richiamo dei duplicati                              | Che la deduplicazione non fonda task diversi                                 | Precisione almeno 95%, richiamo almeno 85%                           | Trimestrale                                   |
| Correlazione tra N e D                                           | Che i due assi restino distinti                                              | Correlazione di Spearman sotto 0,5                                   | A ogni ricalcolo                              |
| Set di controllo                                                 | Stabilità del sistema su 50 task fissi                                       | Spostamento medio sotto 0,25 punti su scala 0–4                      | Settimanale e a ogni cambio di modello        |
| Verifica a posteriori della copertura                            | Che la copertura stimata anticipi l'uso osservato                            | Correlazione positiva tra copertura a t e aumento d'uso a t + 6 mesi | Semestrale                                    |
| Stabilità dei quadranti                                          | Quota di occorrenze con quadrante più probabile oltre l'80%                  | Almeno il 75% delle ore lavorate                                     | A ogni ricalcolo                              |
| Coda di revisione                                                | Che la revisione umana resti sostenibile                                     | Tempo mediano di risoluzione fino a 10 giorni lavorativi             | Settimanale                                   |

### Segnali di drift da sorvegliare

- Un nuovo rilascio di un dataset sposta la copertura media di una famiglia professionale di oltre 0,5 punti: prima di pubblicare lo snapshot serve una nota esplicativa.

- Il fornitore del modello linguistico lo aggiorna: si riesegue il set di controllo e, se fallisce, si ritara il prompt prima di ogni nuova valutazione.

- La quota di D proveniente da stime preliminari supera il 30% delle ore di un ruolo: le metriche di quel ruolo vengono mostrate come provvisorie.

## Governance, revisione umana e conformità

La regola di fondo: gli agenti propongono e le persone decidono tutto ciò che cambia un risultato di policy. La KB classifica task, mai persone, e non alimenta decisioni automatiche su singoli lavoratori.

### Chi decide cosa

| Oggetto                           | Chi propone               | Chi approva                    | Applicazione automatica                                |
|-----------------------------------|---------------------------|--------------------------------|--------------------------------------------------------|
| Caricamento di fonti e tassonomie | Source Watcher            | Curatore                       | Sì, dopo controllo di integrità e licenza              |
| Nuovi task canonici e fusioni     | Canonicalizer             | Curatore, a campione           | Sì se la novità semantica è chiara; altrimenti in coda |
| Collegamenti alle tassonomie      | Crosswalk Mapper          | Revisori, a campione del 10%   | Sì, finché la precisione misurata resta almeno al 90%  |
| Evidenze normalizzate             | Evidence Extractor        | Curatore per le fonti nuove    | Sì per fonti già approvate                             |
| Snapshot di copertura             | Capability Estimator      | Curatore, con nota esplicativa | No                                                     |
| Rubrica e ancore                  | Responsabile metodologico | Comitato di governance         | No                                                     |
| Pesi, λ e soglie                  | Comitato di governance    | Comitato di governance         | No: nessun agente può proporli                         |

Il comitato di governance di ogni organizzazione cliente comprende direzione HR, responsabili di linea, rappresentanza dei lavoratori e, dove presente, il responsabile della protezione dei dati.

### La coda di revisione umana

Un'occorrenza va in revisione quando si verifica almeno una di queste condizioni:

- la probabilità del quadrante principale è sotto l'80%;

- i 5 campioni del modello divergono di oltre un punto su una voce;

- esiste una coppia quasi identica nel testo con coordinate molto diverse. Non è automaticamente un errore: se il revisore conferma che la differenza è legittima e annota il tratto che la determina, la coppia diventa un esempio di calibrazione, tra i più preziosi del sistema;

- appartiene a una famiglia professionale ad alto rischio normativo;

- D è ancora basata solo su stime preliminari in un ruolo sotto analisi.

Ogni decisione del revisore viene salvata come giudizio esperto, quindi alimenta direttamente il ricalcolo e le future calibrazioni.

### Quadro normativo

- **AI Act europeo.** Il Digital Omnibus ha spostato al [2 dicembre 2027](https://www.burges-salmon.com/?p=17536) gli obblighi per i sistemi ad alto rischio dell'Allegato III, categoria che include occupazione e gestione del personale. Se Neartech viene usato per assegnare compiti o prendere decisioni che toccano i lavoratori, va progettato fin d'ora con registrazione degli eventi, supervisione umana e documentazione tecnica.

- **Legge 132/2025, articolo 11.** Il datore di lavoro deve [informare i lavoratori](https://www.ecnews.it/lavoro/blog/intelligenza-artificiale-diventa-legge/) dell'uso di sistemi di AI secondo l'art. 1-bis del D.Lgs. 152/1997. Un'organizzazione che usa la KB per riprogettare mansioni deve valutare se rientra in questi casi e predisporre l'informativa. Neartech può fornire ai clienti il materiale per prepararla.

- **GDPR.** Le risposte alle survey sono pseudonimizzate alla raccolta, conservate separatamente dalle anagrafiche e mostrate solo in forma aggregata, con gruppi di almeno 5 rispondenti.

Il quadro va verificato con un consulente legale prima del primo uso commerciale.

### Limiti d'uso dichiarati

- La KB non produce valutazioni di singoli lavoratori né graduatorie di persone.

- I risultati di un ruolo con D prevalentemente da stime preliminari sono provvisori e non possono motivare una riorganizzazione.

- Ogni risultato esportato riporta il profilo di pesi, lo snapshot di copertura e la versione della rubrica che lo hanno generato.

## Roadmap

Il percorso porta la KB in produzione su un primo dominio in circa 16 settimane e rende autonoma la manutenzione entro la settimana 24. Le durate sono stime da rivedere dopo la prima fase, e nessuna fase parte se il gate precedente non è superato.

<img src="media/image3.png" style="width:6in;height:5.92857in" alt="roadmap · 5 fasi, 5 gate" />

roadmap · 5 fasi, 5 gate

Il gate evidenziato decide l'ingresso in produzione: prima di superarlo, ogni risultato è sperimentale e non può motivare decisioni organizzative.

### Che cosa si consegna in ogni fase

- [ ] **F0, Fondazioni**: schema del database applicato; tassonomie caricate con licenze registrate; caricamento automatico delle fonti di evidenza; collegamenti sul primo lotto di task con campione rivisto da persone.

- [ ] **F1, Rubrica e gold standard**: rubrica con esempi reali dell'azienda pilota; protocollo e calendario del panel; 200 task con divisione fissa tra taratura e hold-out; rapporto di affidabilità per ogni voce.

- [ ] **F2, Pilota sui servizi alla persona**: task canonici e occorrenze dell'azienda pilota; campagne di survey a lavoratori e beneficiari; primo snapshot di copertura; rapporto di non-inferiorità; mappa dei ruoli con baricentro e dispersione.

- [ ] **F3, Manutenzione autonoma**: agenti di sorveglianza, estrazione e sintesi in esercizio; set di controllo; console di revisione; primo report mensile.

- [ ] **F4, Estensione**: profili di peso per organizzazione; una seconda famiglia professionale; prima verifica a posteriori a 6 mesi.

### Il ruolo dell'azienda pilota

L'azienda pilota mette a disposizione i documenti di lavoro, fa partecipare alcuni suoi operatori e coordinatori al panel e alle survey, e riceve in cambio la prima mappa dei propri ruoli. Serve un accordo che definisca l'uso dei documenti, le garanzie di riservatezza per i partecipanti e la restituzione dei risultati. Nessun dato individuale esce dall'azienda in forma identificabile.

## Rischi e mitigazioni

Il rischio principale non è tecnico: è che una KB credibile venga usata per giustificare tagli decisi altrove. Le mitigazioni tecniche servono, ma la difesa vera sono i limiti d'uso dichiarati e la presenza dei lavoratori nella governance.

| Rischio                                                         | Segnale                                                                            | Mitigazione                                                                                                              |
|-----------------------------------------------------------------|------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| Uso strumentale della KB per legittimare riduzioni di personale | Richieste di classifiche per ruolo senza un progetto di riprogettazione del lavoro | Limiti d'uso dichiarati; provenienza di ogni output; rappresentanza dei lavoratori nel comitato                          |
| Evidenze sbilanciate sugli Stati Uniti e su prodotti specifici  | Copertura alta su task poco digitalizzati in Italia                                | Peso ridotto per collegamenti indiretti; piloti interni come evidenza locale; stime ILO e INAPP come riferimento         |
| Uso osservato scambiato per capacità                            | Copertura che segue la popolarità di un task più che il suo successo               | Gerarchia di qualità delle evidenze; successo e benchmark pesano più della frequenza d'uso                               |
| Granularità diversa tra tassonomie e mansionari                 | Molte relazioni "più ampia" e poche "esatta"                                       | Livello di granularità esplicito sui task canonici; trasferimento delle evidenze solo via relazioni esatte o più strette |
| Cambio di comportamento del modello linguistico                 | Il set di controllo fallisce                                                       | Versione del modello bloccata; ritaratura obbligatoria prima di nuove valutazioni                                        |
| Bassa partecipazione alle survey                                | Gruppi sotto i 5 rispondenti                                                       | Questionari brevi; campagne per famiglia professionale; restituzione dei risultati ai partecipanti                       |
| Istruzioni nascoste nei documenti caricati                      | Testo nei mansionari che contiene comandi                                          | I documenti sono dati, mai istruzioni; gli agenti leggono solo gli indirizzi registrati                                  |
| Costo di manutenzione superiore al valore                       | Coda di revisione in crescita costante                                             | Soglie di approvazione automatica tarate sulla precisione misurata; revisione a campione                                 |
| Licenze dei dataset incompatibili con l'uso commerciale         | Fonte senza licenza registrata                                                     | Nessun caricamento senza licenza compilata; verifica legale per l'uso in Neartech                                        |
| Disaccordo tra esperti sull'asse D                              | Alfa di Krippendorff sotto 0,67 dopo le revisioni della rubrica                    | Fondere o eliminare le voci che non convergono; trattare il problema come problema di rubrica, non di modello            |

## Decisioni da prendere e prossimi passi

Per avviare la fase F0 servono sei decisioni; le prime tre bloccano l'avvio.

- [ ] **Accordo per il pilota**: formalizzare con l'azienda pilota l'uso delle job description e il coinvolgimento di operatori e coordinatori nelle survey.

- [ ] **Ruoli interni**: chi fa da curatore della KB (approva fonti e aggiornamenti) e chi da responsabile metodologico (rubrica, panel, validazione).

- [ ] **Budget operativo**: chiamate ai modelli linguistici, hosting del database e del modello di embedding, tempo del panel.

- [ ] **Licenze dei dataset**: verifica legale dell'uso commerciale delle fonti pubbliche dentro Neartech.

- [ ] **Seconda organizzazione**: individuare una PMI di un altro settore per la fase F4, così il metodo non resta tarato solo sui servizi alla persona.

- [ ] **Metodo aperto o proprietario**: decidere se pubblicare la metodologia (credibilità scientifica, rapporti con le università) tenendo proprietari i dati raccolti e il software.

### Primi deliverable operativi

1.  Applicare lo schema del database e caricare le tassonomie.

2.  Scrivere i caricatori delle fonti di evidenza pubbliche.

3.  Campionare i 200 task del gold standard e convocare il panel.

4.  Rifinire la rubrica con esempi reali dell'azienda pilota.

## Fonti consultate

Consultate il Oct 8, 2026.

- [Shao et al., Future of Work with AI Agents (WORKBank), arXiv 2506.06576](https://arxiv.org/abs/2506.06576v2) e [sito del progetto](https://futureofwork.saltlab.stanford.edu)

- [Anthropic Economic Index](https://www.anthropic.com/economic-index) e [report "Economic primitives"](https://www.anthropic.com/research/economic-index-primitives?stream=top)

- [Tomlinson et al., Working with AI, arXiv 2507.07935](https://arxiv.org/html/2507.07935v5)

- [Patwardhan et al., GDPval, arXiv 2510.04374](https://arxiv.org/pdf/2510.04374)

- [METR, voce Time Horizon 1.1](https://en.wikipedia.org/wiki/METR)

- [ILO Working Paper 140, Generative AI and Jobs: A Refined Global Index](https://www.ilo.org/node/706766)

- [INAPP, applicazione all'Atlante del Lavoro (WP 125)](https://oa.inapp.gov.it/server/api/core/bitstreams/3fa70c6b-dbdf-4232-95ef-08590a16a5a0/content)

- [McKinsey Global Institute, Agents, robots, and us](https://www.mckinsey.com/mgi/our-research/agents-robots-and-us-skill-partnerships-in-the-age-of-ai)

- [O\*NET 31.0 Data Dictionary](https://www.onetcenter.org/dictionary/31.0/jsonld/hasTask.html)

- [ESCO v1.2.1](https://esco.ec.europa.eu/et/node/563)

- [Digital Omnibus e scadenze AI Act](https://www.burges-salmon.com/?p=17536)

- [Legge 132/2025, art. 11](https://www.ecnews.it/lavoro/blog/intelligenza-artificiale-diventa-legge/)

## Appendice: schema SQL e vista per le metriche di ruolo

Schema per PostgreSQL 16 con l'estensione pgvector. È il punto di partenza per la fase F0; i nomi e i tipi possono essere rifiniti in implementazione, ma le regole di progetto (tabelle separate, nessuna soglia nel codice, un record per ogni giudizio) restano.

### Tabelle

CREATE EXTENSION IF NOT EXISTS vector;  
  
-- Fonti e tassonomie  
CREATE TABLE sources (  
source_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
kind text NOT NULL, -- taxonomy \| evidence \| org_document \| survey \| panel  
name text NOT NULL,  
version text NOT NULL,  
uri text,  
license text,  
content_hash text NOT NULL,  
retrieved_at timestamptz NOT NULL DEFAULT now(),  
UNIQUE (name, version)  
);  
  
CREATE TABLE taxonomy_nodes (  
node_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
scheme text NOT NULL CHECK (scheme IN ('ONET_TASK','ONET_DWA','ONET_IWA','ESCO_OCC','ESCO_SKILL','ATLANTE_ADA','ISCO08','CP2021')),  
code text NOT NULL,  
label text NOT NULL,  
lang text NOT NULL,  
parent_id uuid REFERENCES taxonomy_nodes,  
source_id uuid NOT NULL REFERENCES sources,  
UNIQUE (scheme, code, lang, source_id)  
);  
  
-- Task canonici, organizzazioni, occorrenze  
CREATE TABLE canonical_tasks (  
task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
title_it text NOT NULL UNIQUE,  
granularity smallint NOT NULL CHECK (granularity BETWEEN 1 AND 3),  
status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','merged','retired')),  
merged_into uuid REFERENCES canonical_tasks,  
created_at timestamptz NOT NULL DEFAULT now()  
);  
  
CREATE TABLE task_mappings (  
task_id uuid REFERENCES canonical_tasks,  
node_id uuid REFERENCES taxonomy_nodes,  
relation text NOT NULL CHECK (relation IN ('exact','broad','narrow','related')),  
confidence numeric(3,2) NOT NULL,  
rationale text NOT NULL,  
validated boolean NOT NULL DEFAULT false,  
PRIMARY KEY (task_id, node_id)  
);  
  
CREATE TABLE organizations (  
org_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
name text NOT NULL,  
sector text  
);  
  
CREATE TABLE roles (  
role_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
org_id uuid NOT NULL REFERENCES organizations,  
name text NOT NULL,  
family text,  
UNIQUE (org_id, name)  
);  
  
CREATE TABLE task_occurrences (  
occurrence_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
task_id uuid NOT NULL REFERENCES canonical_tasks,  
role_id uuid NOT NULL REFERENCES roles,  
context_note text,  
raw_snippet text NOT NULL,  
time_share numeric(5,4) CHECK (time_share BETWEEN 0 AND 1),  
source_id uuid NOT NULL REFERENCES sources,  
UNIQUE (task_id, role_id)  
);  
  
-- Embedding per modello, con indice parziale a dimensione fissa  
CREATE TABLE task_embeddings (  
task_id uuid REFERENCES canonical_tasks,  
model_name text,  
vec vector NOT NULL,  
PRIMARY KEY (task_id, model_name)  
);  
  
CREATE INDEX task_emb_bge_m3 ON task_embeddings  
USING hnsw ((vec::vector(1024)) vector_cosine_ops)  
WHERE model_name = 'BAAI/bge-m3';  
  
-- Evidenze e snapshot di copertura  
CREATE TABLE evidence_items (  
evidence_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
source_id uuid NOT NULL REFERENCES sources,  
evidence_type text NOT NULL CHECK (evidence_type IN ('benchmark','usage_success','usage','internal_pilot','expert','llm_prior')),  
node_id uuid REFERENCES taxonomy_nodes,  
task_id uuid REFERENCES canonical_tasks,  
dimension text NOT NULL CHECK (dimension IN ('k1','k2','k3','any')),  
raw_value numeric NOT NULL,  
score_0_4 numeric(3,2) NOT NULL CHECK (score_0_4 BETWEEN 0 AND 4),  
quality numeric(3,2) NOT NULL,  
observed_at date NOT NULL,  
CHECK (node_id IS NOT NULL OR task_id IS NOT NULL)  
);  
  
CREATE TABLE capability_snapshots (  
snapshot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
as_of date NOT NULL,  
method_version text NOT NULL,  
half_life_days int NOT NULL,  
status text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed','published','retired')),  
approved_by text,  
approved_at timestamptz  
);  
CREATE UNIQUE INDEX one_published_snapshot ON capability_snapshots (status) WHERE status = 'published';  
  
CREATE TABLE task_capability (  
snapshot_id uuid REFERENCES capability_snapshots,  
task_id uuid REFERENCES canonical_tasks,  
dimension text CHECK (dimension IN ('k1','k2','k3')),  
c_mean numeric(3,2) NOT NULL,  
c_low numeric(3,2) NOT NULL,  
c_high numeric(3,2) NOT NULL,  
n_evidence int NOT NULL,  
PRIMARY KEY (snapshot_id, task_id, dimension)  
);  
  
-- Versioni della rubrica (una sola corrente)  
CREATE TABLE rubric_versions (  
version text PRIMARY KEY,  
is_current boolean NOT NULL DEFAULT false,  
approved_by text,  
approved_at timestamptz  
);  
CREATE UNIQUE INDEX one_current_rubric ON rubric_versions (is_current) WHERE is_current;  
  
-- Valutazioni: un record per ogni singolo giudizio (campione di modello o persona)  
CREATE TABLE assessment_runs (  
run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
target_kind text NOT NULL CHECK (target_kind IN ('task','occurrence')),  
target_id uuid NOT NULL,  
item text NOT NULL CHECK (item IN ('k1','k2','k3','r','d1','d2','d3','d4')),  
value smallint NOT NULL CHECK (value BETWEEN 0 AND 4),  
rater_kind text NOT NULL CHECK (rater_kind IN ('llm','expert','worker','beneficiary')),  
rater_ref text NOT NULL, -- id pseudonimo o identificativo del modello  
rubric_version text NOT NULL REFERENCES rubric_versions,  
prompt_hash text,  
rationale text,  
campaign_id text,  
created_at timestamptz NOT NULL DEFAULT now()  
);  
CREATE INDEX ar_target ON assessment_runs (target_kind, target_id, item, rubric_version);  
  
-- Governance: profili di peso per organizzazione (org_id NULL = profilo di default)  
CREATE TABLE weight_profiles (  
profile_id text PRIMARY KEY,  
org_id uuid REFERENCES organizations,  
w_k1 numeric(4,3) NOT NULL, w_k2 numeric(4,3) NOT NULL, w_k3 numeric(4,3) NOT NULL,  
lambda_r numeric(4,3) NOT NULL DEFAULT 0.5,  
w_d1 numeric(4,3) NOT NULL, w_d2 numeric(4,3) NOT NULL, w_d3 numeric(4,3) NOT NULL, w_d4 numeric(4,3) NOT NULL,  
theta_n numeric(3,2) NOT NULL DEFAULT 0.50,  
theta_d numeric(3,2) NOT NULL DEFAULT 0.50,  
is_active boolean NOT NULL DEFAULT false,  
approved_by text,  
approved_at timestamptz,  
CHECK (abs(w_k1 + w_k2 + w_k3 - 1) \< 0.001),  
CHECK (abs(w_d1 + w_d2 + w_d3 + w_d4 - 1) \< 0.001)  
);  
CREATE UNIQUE INDEX one_active_profile_per_org  
ON weight_profiles (COALESCE(org_id, '00000000-0000-0000-0000-000000000000'::uuid)) WHERE is_active;  
  
-- Risultati materializzati dal job di calcolo (simulazione Monte Carlo)  
CREATE TABLE policy_estimates (  
occurrence_id uuid REFERENCES task_occurrences,  
profile_id text REFERENCES weight_profiles,  
snapshot_id uuid REFERENCES capability_snapshots,  
rubric_version text REFERENCES rubric_versions,  
n_mean numeric(4,3), n_sd numeric(4,3),  
d_mean numeric(4,3), d_sd numeric(4,3),  
p_q1 numeric(4,3), p_q2 numeric(4,3), p_q3 numeric(4,3), p_q4 numeric(4,3),  
d_source_mix jsonb NOT NULL, -- quota di D da panel, survey, stima preliminare  
computed_at timestamptz NOT NULL DEFAULT now(),  
PRIMARY KEY (occurrence_id, profile_id, snapshot_id, rubric_version)  
);  
  
-- Indirizzi forniti dagli utenti agli agenti  
CREATE TABLE steering_directives (  
directive_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
scope text NOT NULL, -- es. family:servizi_persona, source:AEI  
instruction text NOT NULL,  
priority smallint NOT NULL DEFAULT 2,  
expires_at date,  
created_by text NOT NULL  
);  
  
-- Esecuzione: coda di lavoro e registro degli agenti  
CREATE TABLE jobs (  
job_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
kind text NOT NULL,  
payload jsonb NOT NULL,  
status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','done','failed')),  
attempts int NOT NULL DEFAULT 0,  
run_after timestamptz NOT NULL DEFAULT now(),  
created_at timestamptz NOT NULL DEFAULT now()  
);  
  
CREATE TABLE agent_runs (  
agent_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),  
job_id uuid REFERENCES jobs,  
component text NOT NULL,  
model_id text,  
prompt_hash text,  
duration_ms int,  
cost_usd numeric(10,4),  
started_at timestamptz NOT NULL DEFAULT now()  
);

### Vista per le metriche di ruolo

La vista legge solo la configurazione attiva (profilo di pesi, snapshot pubblicato, rubrica corrente), quindi un cambio di configurazione non produce mai conteggi doppi.

CREATE VIEW v_role_metrics AS  
WITH cur AS (  
SELECT pe.\*, o.role_id, o.time_share AS p  
FROM policy_estimates pe  
JOIN task_occurrences o USING (occurrence_id)  
JOIN roles r ON r.role_id = o.role_id  
JOIN weight_profiles w ON w.profile_id = pe.profile_id AND w.is_active  
AND (w.org_id = r.org_id OR (w.org_id IS NULL AND NOT EXISTS (  
SELECT 1 FROM weight_profiles w2 WHERE w2.org_id = r.org_id AND w2.is_active)))  
JOIN capability_snapshots s ON s.snapshot_id = pe.snapshot_id AND s.status = 'published'  
JOIN rubric_versions rv ON rv.version = pe.rubric_version AND rv.is_current  
),  
bary AS (  
SELECT role_id, SUM(p \* n_mean) / SUM(p) AS bn, SUM(p \* d_mean) / SUM(p) AS bd, SUM(p) AS tw  
FROM cur GROUP BY role_id  
)  
SELECT b.role_id,  
round(b.bn, 3) AS barycenter_n,  
round(b.bd, 3) AS barycenter_d,  
round(sqrt(SUM(c.p \* ((c.n_mean - b.bn)^2 + (c.d_mean - b.bd)^2)) / b.tw), 3) AS dispersion,  
round(SUM(c.p \* GREATEST(c.p_q1, c.p_q2, c.p_q3, c.p_q4)) / b.tw, 3) AS stability,  
count(\*) AS n_tasks  
FROM bary b JOIN cur c USING (role_id)  
GROUP BY b.role_id, b.bn, b.bd, b.tw;

### Test minimo da eseguire in F0

Un test con dati sintetici deve verificare tre cose: una configurazione con due profili di pesi attivi nello stesso ambito viene rifiutata dall'indice univoco; un task con più valutazioni (di modello e umana) produce una sola riga in policy_estimates per configurazione; dopo la pubblicazione di un nuovo snapshot la vista restituisce una sola riga per ruolo.
