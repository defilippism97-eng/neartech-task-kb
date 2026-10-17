# La fase di ascolto del comitato guida: materiali, interviste, scenari

**Stato:** proposta di progetto, 2026-10-17, da approvare dal responsabile del progetto. Solo progetto: nessun codice, nessuna migrazione, nessun parametro approvato.
**Sostituisce**, una volta approvata e costruita, il questionario provvisorio `docs/governance/questionario-indirizzi-bozza-1.json` (registro di metodo, sezione 28, nota "Da rivedere").
**Riferimenti:** registro di metodo, sezioni 17, 22, 27 e 28; `docs/piani/fase-6-piattaforma.md` (passi 4–6 del flusso, fetta 3); `neartech.calcolo` (formule di N e D, quadranti); `neartech.indirizzi_pesi` (proposta, approvazione, verifica, effetto); migrazione 0037; ADR 0004 (spazio dell'organizzazione).

## Perché cambiare

Il questionario `bozza-1` chiede al comitato quanto contano relazione, responsabilità, senso del lavoro e valore per il beneficiario. Sono preferenze **dichiarate**: le risposte sono ovvie e quasi uguali per tutte le imprese ("la relazione conta molto"), e la regola le trasforma in pesi che si muovono poco e non distinguono un'impresa dall'altra. Il responsabile ha chiesto (sezione 28) che gli indirizzi emergano da preferenze **rivelate**: dalle scelte che il comitato fa davanti a scenari di automazione costruiti sui task reali dell'impresa.

Resta valido tutto ciò che la fetta 3 ha costruito dopo i pesi: la bozza di profilo con l'atto di proposta, la simulazione dell'effetto sui task, l'approvazione del comitato, la verifica dell'auditor, l'attivazione solo con entrambi gli atti (imposta dal database, migrazione 0037), i limiti dei pesi e il pavimento legale. Cambia **come si arriva alla proposta dei pesi**.

## Che cosa muovono i pesi di D, e che cosa no

Dal codice (`neartech.calcolo`):

- `D = Σ w_j · d_j / 4` sulle componenti disponibili, con i pesi riportati a somma uno; oggi le componenti disponibili sono d1 e d2 (D provvisorio).
- Il quadrante dipende da `N ≥ θ_N` e `D ≥ θ_D`. I pesi di D **non toccano N** né le soglie (la fetta 3 li lascia quelli del profilo di partenza, e così resta).

Due conseguenze guidano tutto il progetto:

1. **Un cambio di pesi sposta un task sulla mappa solo lungo l'asse di D**, cioè fra Q1 e Q2 (N alto) o fra Q3 e Q4 (N basso). Il passaggio che conta di più per gli indirizzi è **Q3 ↔ Q4**: N basso significa che la tecnologia copre il task, e la domanda "lo affidiamo all'IA o lo teniamo alle persone perché è desiderabile così?" è esattamente quella che il comitato deve orientare.
2. **Un cambio di pesi sposta D solo nei task con componenti diverse fra loro.** Un task con d1 = d2 ha lo stesso D con qualunque peso. Gli scenari utili sono quelli fra task che differiscono nelle componenti, perché solo lì la scelta del comitato dice qualcosa sul peso relativo.

## Che cosa vive il comitato: semplice per chi partecipa

Il metodo statistico serve al codice e all'auditor; **il comitato non lo vede**. Per il comitato la fase sono quattro momenti, con un linguaggio senza termini tecnici:

| Momento | Che cosa fa il comitato | Tempo |
|---|---|---|
| 1. Materiali | Carica i documenti che ha già (anche nessuno) | quando vuole |
| 2. Interviste | Una conversazione per membro con il facilitatore; poi legge una pagina di sintesi e risponde a quattro domande: *"questa componente per noi conta più, come o meno del profilo comune?"* | 1 ora a testa, più 15 minuti insieme |
| 3. Scenari | Ogni membro, da solo, risponde a 14 schede: *"di questi quattro compiti, quale terreste alle persone e quale cedereste all'IA?"* | 20–25 minuti |
| 4. Restituzione | Legge una pagina: i pesi proposti, quanti task cambiano quadrante e quali, dove le scelte confermano o smentiscono quanto detto nelle interviste; approva o modifica | 1 incontro |

Regole di semplicità:
- **Nessun numero da dare.** Il comitato non assegna punteggi né percentuali: risponde "più / come / meno" e sceglie fra compiti che conosce.
- **Nessun termine tecnico nelle schermate:** non compaiono "prior", "logit", "intervallo di credibilità". La precisione si dice a parole ("le vostre scelte sono nette", "le vostre scelte non bastano per dire nulla su questa componente").
- **Un documento di restituzione di una pagina**, con il dettaglio tecnico in un allegato per l'auditor.
- **Se le schede non bastano, i pesi restano dove sono** e la schermata lo dice: nessun secondo giro obbligatorio.

## 1. Le tre componenti dell'ascolto e che cosa danno al profilo di D

La fase ha tre componenti, in quest'ordine. Le interviste danno il **punto di partenza** dei pesi, gli scenari lo **confermano o lo correggono**. Né un riassunto del modello né una frase di un'intervista diventano un peso da soli: passano sempre da una risposta o da una scelta delle persone.

| Componente | Che cosa si raccoglie | Che cosa dà al profilo di D |
|---|---|---|
| A. Materiali documentali | Documenti già esistenti dell'impresa | Perimetro degli scenari; vincoli dichiarati dall'impresa; confronto con le scelte |
| B. Interviste aperte e di visione | Conversazioni con i membri del comitato | **Punto di partenza** dei pesi (quattro risposte del comitato dopo la sintesi); processi e temi per gli scenari |
| C. Scenari di automazione | Scelte del comitato fra task reali | **Stima finale** dei pesi, a partire dal punto di partenza |

### A. Materiali documentali

Il comitato, tramite l'amministratore tecnico, carica i documenti che già esistono. Nessun documento è obbligatorio; l'assenza si registra ("nessuna policy sull'IA") ed è essa stessa un'informazione per il comitato.

Esempi, in ordine di utilità:
- policy o linee guida sull'uso dell'IA, regolamenti interni sugli strumenti informatici;
- piano strategico o industriale, documenti di visione, presentazioni del vertice sulla trasformazione digitale;
- carta dei servizi, codice etico, bilancio di sostenibilità;
- accordi con le rappresentanze dei lavoratori sull'uso delle tecnologie e sul controllo a distanza;
- valutazioni d'impatto e registro dei trattamenti per i processi automatizzati, modello organizzativo 231 se presente.

Che cosa ne esce:
- **Perimetro degli scenari:** i processi che l'impresa indica come oggetto di trasformazione, o come esclusi, delimitano da quali ruoli e famiglie si pescano i task (sezione 2).
- **Vincoli dichiarati:** frasi come "nessuna decisione sul cliente senza una persona responsabile" non sono pesi, sono vincoli. Il modello li **segnala** con la citazione esatta; il comitato decide se e come registrarli. Un vincolo approvato può diventare (decisione aperta 6) un pavimento dell'organizzazione sopra quello legale, con lo stesso trattamento del pavimento legale nei controlli: gli indirizzi stimati non possono andare contro di esso.
- **Confronto:** dopo la stima, la restituzione mette accanto ciò che i documenti dichiarano e ciò che le scelte rivelano (le "dissonanze", sezione 3.6, passo 3).

### B. Interviste aperte e di visione

Interviste individuali di 45–60 minuti con ciascun membro del comitato (e, se il comitato lo chiede, con chi guida i processi principali), condotte da un facilitatore NEARTECH, prima della sessione sugli scenari. Domande aperte, non a scala. Traccia indicativa:

1. Fra tre anni, quali processi della vostra impresa immagina trasformati dall'IA, e come lavorerebbero le persone in quei processi?
2. C'è una parte del vostro servizio che un cliente o un utente non dovrebbe mai percepire come automatica? Perché proprio quella?
3. Quali decisioni non firmerebbe se a prenderle fosse un sistema, anche se fosse accurato?
4. Pensi a un lavoro della sua impresa che dà senso a chi lo fa. Che cosa succederebbe a quel senso se una parte passasse a una macchina?
5. Se l'IA liberasse il 20% del tempo di un ruolo, dove vorrebbe che andasse quel tempo?
6. Che cosa la preoccupa e che cosa spera, per la sua impresa, da questa trasformazione?
7. Chi, fuori dall'impresa, giudicherebbe le vostre scelte sull'automazione, e con quale metro?

Che cosa ne esce:
- **Il punto di partenza dei pesi.** Il modello riassume le interviste in una pagina, per componente di D, con le frasi citate alla lettera. Il comitato la legge e, per ogni componente, risponde a una sola domanda: *"Per noi questa componente conta più, come o meno del profilo comune?"*. Quattro risposte, un atto registrato. Il codice le traduce con una regola fissa del parametro di governance (più = +x%, meno = −x%, poi dentro i limiti e a somma uno, come `bozza-1`): è il **punto di partenza** da cui partono gli scenari. Il passaggio dalle parole al numero lo fa il comitato, non il modello. L'intensità x è più bassa dello spostamento massimo ammesso dagli scenari, perché le preferenze dichiarate sono il punto debole da cui partiamo.
- **Temi e processi** citati come centrali: alimentano la scelta del perimetro e il testo degli scenari.
- **Confronto:** se le scelte negli scenari smentiscono il punto di partenza, la restituzione lo dice in una frase.

Il contenuto delle interviste si legge **solo in forma aggregata**, senza attribuzione a chi ha parlato (sezione 4).

### C. Scenari di automazione simulati

È il cuore della fase. Ogni membro del comitato, da solo e senza vedere le scelte degli altri, risponde a una serie di **schede di scenario**. Ogni scheda presenta **quattro task reali** dell'impresa, dello stesso processo o di processi vicini, con la premessa:

> "Supponete che nei prossimi due anni l'IA possa svolgere ciascuno di questi compiti con la stessa qualità e lo stesso costo di oggi. Di questi quattro, quale vorreste di più che restasse affidato a persone? E quale cedereste più volentieri all'IA?"

La premessa neutralizza la fattibilità e l'economia (che N e il costo misurano già altrove): la scelta riguarda la **desiderabilità**, cioè D. È un formato di *best–worst scaling* (MaxDiff): ogni scheda dà due scelte e, implicitamente, cinque dei sei confronti a coppie fra i quattro task, quindi informa più di una domanda a coppie.

Ogni task compare con il nome, una descrizione breve tratta dal mansionario e il ruolo. **Non compaiono i valori di d1–d4**: se il comitato li vedesse sceglierebbe sui numeri, e torneremmo alle preferenze dichiarate. Il collegamento fra scelta e pesi lo fa il codice, usando i valori di d1–d4 registrati per quei task.

Le schede su cui il comitato si è diviso di più (misura aggregata, nessun nome) si discutono nell'incontro di restituzione, senza una sessione in più. La stima usa il giro individuale (decisione aperta 3).

## 2. Come si generano gli scenari dai task dell'impresa

Gli scenari si generano **dal codice, in modo deterministico**, dai task e dalle occorrenze dell'organizzazione. Il modello interviene solo per riscrivere la descrizione del task in modo leggibile (sezione 4); la composizione delle schede non la decide il modello. L'insieme delle schede è approvato prima della sessione (decisione aperta 4) e congelato con un'impronta.

### 2.1 Il perimetro

Si parte dai ruoli e dalle famiglie professionali dentro il perimetro organizzativo condiviso con NEARTECH, ristretti ai processi che i materiali e le interviste indicano come oggetto di trasformazione. Se il perimetro è più ampio del tempo di una sessione, il comitato sceglie i processi; la scelta è un atto registrato.

### 2.2 I task che decidono la mappa

Per ogni occorrenza `t` con D disponibile, il codice calcola:

- **Intervallo ammissibile di D.** Fra tutti i profili di pesi ammessi (ogni peso dentro i limiti del parametro, somma uno, e scostamento massimo dal profilo di partenza, come oggi l'intensità di `bozza-1`), il D minimo e il D massimo del task: `D_min(t)` e `D_max(t)`. Poiché D è lineare nei pesi e l'insieme ammesso è un poliedro, il minimo e il massimo stanno sui vertici: è un calcolo esatto, senza simulazione.
- **Task decisivo:** se `θ_D` sta fra `D_min(t)` e `D_max(t)`, esiste un profilo ammesso che lo porta da una parte e uno che lo porta dall'altra. Sono i task su cui l'orientamento del comitato cambia la mappa.
- **Priorità.** Fra i task decisivi si preferiscono:
  1. quelli con **N basso** con alta probabilità (passaggio Q3 ↔ Q4, dove la scelta di automazione è concreta);
  2. quelli più vicini al confine, misurato con la probabilità del quadrante calcolata con il profilo di partenza (la stessa simulazione di `effetto`);
  3. quelli con più occorrenze nell'impresa, perché pesano di più sulla mappa;
  4. a parità, quelli con giudizi di persona su d1–d4 rispetto alle stime del modello.

I numeri di questa priorità (quanti task, quale peso a ciascun criterio) sono un parametro di governance, non stanno nel codice.

### 2.3 Dalle liste alle schede

Ogni scheda ha quattro task dello stesso processo o di processi vicini (la scelta è realistica solo se i task sono confrontabili). Il codice compone le schede per **massimizzare l'informazione sui pesi**, con un criterio di disegno ottimo (D-efficienza della matrice di informazione del modello di scelta, calcolata al profilo di partenza):

- nella stessa scheda i task differiscono in **direzioni diverse** delle componenti (uno alto in relazione e basso in responsabilità, un altro il contrario), perché solo le differenze fra componenti identificano i pesi;
- ogni task compare in almeno tre schede per membro, in posizioni diverse (bilanciamento usuale del MaxDiff);
- si aggiungono **due schede di controllo** non usate per la stima: una ripetuta identica a distanza (coerenza nel tempo) e una con un task che domina gli altri su tutte le componenti (attenzione). Servono all'auditor, non ai pesi;
- una piccola quota di task **non decisivi ma chiari** (D molto alto o molto basso con qualunque profilo) fa da ancora: rende le schede credibili e aiuta a stimare la nettezza delle scelte.

Il disegno è deterministico: stesso stato dell'organizzazione, stesso parametro, stesso seme, stesse schede. Prima della sessione il codice esegue una **prova di recupero**: simula comitati sintetici con pesi noti, risponde alle schede con il modello di scelta, stima i pesi e verifica che l'intervallo stimato contenga quelli veri con la frequenza attesa. Se il disegno non permette di stimare un peso (per esempio perché nei task dell'impresa d1 e d2 vanno sempre insieme), il sistema lo dice prima, non dopo.

### 2.4 Componenti mancanti

Oggi i task hanno d1 e d2, non d3 e d4 (arrivano con i questionari d3/d4, fetta 6). Con soli d1 e d2 le scelte identificano **solo il rapporto fra w_d1 e w_d2**, ed è anche l'unica cosa che oggi cambia la mappa, perché D si calcola sulle sole componenti disponibili. Proposta: nella prima applicazione la stima riguarda la quota di w_d1 su w_d1 + w_d2, mentre w_d3 e w_d4 restano quelli del profilo di partenza; un secondo giro di scenari, dopo i questionari d3/d4, stima le quattro componenti. È la decisione aperta 2.

## 3. Dalla scelta ai pesi: il metodo di stima

### 3.1 Il modello

Lo stesso modello che calcola D spiega le scelte. Per il membro `m` e la scheda `S`, l'utilità di "tenere il task `t` alle persone" è

`U(t) = Σ_j β_j · d_j(t) + ε`,   con `β_j = α · w_j`, `w_j ≥ 0`, `Σ w_j = 1`,

dove `d_j(t)` sono i valori registrati del task (gli stessi che usa il calcolo, con la stessa precedenza: persone prima del modello, occorrenza prima del task; per una voce con più giudizi, la media), `α > 0` è la nettezza delle scelte e `ε` è un errore con distribuzione di Gumbel. Ne segue il **logit condizionale** per il best–worst sequenziale:

- probabilità di indicare `t` come "da tenere alle persone": `exp(α·w·d(t)) / Σ_{s∈S} exp(α·w·d(s))`;
- probabilità di indicare `u` come "da cedere", fra i tre restanti: `exp(−α·w·d(u)) / Σ_{s∈S∖{t}} exp(−α·w·d(s))`.

Le componenti mancanti si trattano come nel calcolo: entrano solo quelle disponibili, con i pesi riportati a somma uno.

### 3.2 La stima

**Stima bayesiana su una griglia, deterministica.** Il prior sui pesi è una Dirichlet **centrata sul punto di partenza** (il profilo comune spostato dalle quattro risposte del comitato dopo le interviste, sezione 1.B), con una concentrazione `c` che è un parametro di governance: con poche scelte o scelte contraddittorie il risultato resta vicino al profilo di partenza, con molte scelte coerenti se ne allontana quanto le scelte giustificano. Il prior su `α` è debolmente informativo (parametro).

Lo spazio dei pesi ha tre dimensioni libere (una sola nella prima applicazione con d1 e d2): la posteriore si calcola su una griglia fine del simplesso ammesso per una griglia di valori di `α`. Nessun campionatore, nessun seme: stesso input, stesso risultato, verificabile dall'auditor rifacendo il conto. Esce:

- la **media a posteriori** dei pesi, che diventa la proposta;
- per ogni peso un **intervallo di credibilità** (per esempio all'80%, livello come parametro);
- la probabilità a posteriori che ogni peso sia sopra o sotto quello di partenza ("le vostre scelte dicono, con probabilità 0,9, che la relazione pesa per voi più del profilo comune").

La griglia è **ristretta all'insieme ammesso**: limiti `min` e `max` del parametro e scostamento massimo dal profilo di partenza. Così la proposta rispetta per costruzione gli stessi limiti di oggi, senza troncare dopo. I pesi si arrotondano a tre decimali con la stessa regola di `pesi_dalle_risposte` (lo scarto va al peso maggiore).

Alternative considerate:
- **Confronti a coppie con Bradley–Terry:** stesso modello, meno informazione per scheda; resta come formato di riserva per comitati che trovano difficili le schede da quattro.
- **Massima verosimiglianza senza prior:** con poche decine di scelte e pesi vincolati le stime vanno facilmente sul bordo dei limiti; il prior centrato sul profilo comune è più prudente e più spiegabile ("ci si sposta dal default solo quanto le scelte giustificano").
- **AHP (confronti a coppie fra componenti):** chiede di confrontare direttamente "relazione contro responsabilità", cioè preferenze dichiarate: è il difetto da cui partiamo.

### 3.3 Le ipotesi, dichiarate

1. **Additività lineare:** la desiderabilità di tenere un task alle persone cresce linearmente con d1–d4, con gli stessi pesi per tutti i task. È l'ipotesi della formula di D: se non regge per le scelte, non regge neanche per il calcolo, e la fase lo fa vedere (bassa nettezza, molte incoerenze).
2. **I valori di d1–d4 dei task sono corretti.** La stima li prende come dati. Errori nei valori attenuano i pesi verso il profilo di partenza (non li inventano). I task con giudizi di persona hanno priorità nella composizione delle schede.
3. **La premessa regge:** il comitato sceglie sulla desiderabilità, non su fattibilità o costo. Le schede di controllo e la plenaria lo verificano in parte; l'ipotesi resta.
4. **Indipendenza dalle alternative irrilevanti** dentro la scheda (proprietà del logit). Le schede da quattro task dello stesso processo la rendono ragionevole.
5. **Un solo profilo per l'organizzazione:** le scelte dei membri si mettono insieme. L'eterogeneità fra membri si misura (sezione 3.5) ma non si modella con pesi per persona, che non si calcolano né si mostrano.
6. **Scelte indipendenti nel giro individuale**, prima della plenaria.
7. **Preferenze stabili durante la sessione**: verificata con la scheda ripetuta.

### 3.4 Quante schede servono

Il criterio vincolante è di **precisione, non di numero**: la stima vale come proposta se l'intervallo di credibilità di ogni peso stimato è più stretto di un'ampiezza massima fissata dal parametro; altrimenti il sistema dice che le scelte non bastano e il peso resta quello di partenza (o si fa un secondo giro). La prova di recupero (2.3) stima prima della sessione se il disegno può raggiungere quella precisione.

Come ordine di grandezza, da usare per il primo parametro e da rivedere dopo il primo pilota:
- **per membro:** 12 schede da quattro task più le 2 di controllo, circa 20–25 minuti; con un insieme di 16 task decisivi ognuno compare tre volte. Sotto 8 schede valide un membro non entra nella stima;
- **per il comitato:** almeno 3 membri con scelte valide, cioè almeno 36 schede e 72 scelte (circa 18 per peso con quattro componenti, 36 con due). Sotto questo minimo la fase non produce una proposta;
- nella prima applicazione, con il solo rapporto fra w_d1 e w_d2, lo stesso numero di schede dà una stima molto più stretta: è un motivo in più per partire da lì.

Questi numeri vanno nel parametro del metodo (per esempio `minimo_schede_membro`, `minimo_membri`, `ampiezza_massima_intervallo`), non nel codice.

### 3.5 Coerenza e accordo

Il codice calcola, solo in forma aggregata:
- **coerenza:** quota di risposte uguali nella scheda ripetuta, quota di risposte attese nella scheda di dominanza;
- **nettezza:** la stima di `α` (scelte nette o quasi casuali);
- **accordo:** quanto spesso la maggioranza dei membri indica lo stesso task in una scheda. Se il comitato è molto diviso, la proposta lo dice e la plenaria si concentra lì.

Nessuna misura per singolo membro compare in un output. Con meno membri del minimo di gruppo (`minimo_rispondenti_gruppo`) l'accordo si mostra solo come "alto" o "basso", per evitare che si risalga alla scelta di una persona.

### 3.6 Dalla stima al profilo vigente: il percorso della fetta 3 resta

1. **Proposta.** Il codice stima i pesi e crea la bozza di profilo (`weight_profiles`, `is_active = false`), con pesi di N, λ e soglie del profilo di partenza, come oggi. L'atto di proposta nel registro porta nei dettagli: parametro e versione del metodo, profilo di partenza, impronta dell'insieme di schede, numero di schede e membri validi, intervalli di credibilità, misure di coerenza e accordo. **Non porta le scelte, né i testi**: stanno nello spazio dell'organizzazione (sezione 4).
2. **Effetto.** La stessa simulazione di `indirizzi_pesi.effetto`: quanti task cambiano quadrante, quali, verso dove.
3. **Restituzione al comitato:** pesi proposti con intervalli; effetto sulla mappa; misure di coerenza e accordo; **dissonanze** fra materiali, interviste e scelte (per esempio: la policy dice che la relazione con il cliente resta umana, ma nelle schede i task di relazione sono stati ceduti spesso). Le dissonanze sono testo per la discussione, non correzioni dei pesi.
4. **Approvazione del comitato** (atto `approvazione`). Le persone decidono: il comitato può approvare la stima oppure un profilo diverso **dentro l'insieme ammesso**, con motivazione; lo scostamento dalla stima si registra e l'auditor lo vede (decisione aperta 5).
5. **Verifica dell'auditor** (atto `verifica`) con i controlli automatici di oggi più quelli nuovi:
   - somma uno, dentro i limiti, pavimento legale (come oggi);
   - dentro lo scostamento massimo dal profilo di partenza;
   - numero minimo di schede e membri validi raggiunto;
   - ampiezza degli intervalli entro il massimo del parametro;
   - schede di controllo sopra il minimo di coerenza del parametro;
   - stima riproducibile: rifatta dal codice con lo stesso input, stesso risultato;
   - insieme di schede uguale a quello approvato (impronta);
   - nessun vincolo approvato dell'organizzazione violato (se la decisione aperta 6 li introduce).
6. **Attivazione** solo con entrambi gli atti: il trigger della migrazione 0037 non cambia.
7. **Ricalcolo** di tutti i task con il profilo nuovo; ogni risultato porta il profilo, quindi la chiave che risale alla stima.

La vista del rappresentante dei lavoratori, se attiva, vede le riduzioni di D dovute al profilo nuovo, come previsto dalla sezione 27.

## 4. Dove stanno i contenuti e che cosa fa il modello

### 4.1 Dove stanno

Tutto ciò che è testo dell'impresa o scelta di una persona sta nello **spazio dell'organizzazione** (`org_<codice>`, ADR 0004), con tabelle append-only come quelle della migrazione 0006 dello spazio, e se ne va con lo spazio all'uscita del cliente. **Nulla di questo entra nel dataset condiviso NEARTECH.**

Contenuti proposti (le tabelle si definiranno con una migrazione versionata dello spazio organizzazione quando si costruirà):
- **materiali:** documento caricato, tipo, impronta del contenuto, chi l'ha caricato e quando, livello di riservatezza indicato dal comitato;
- **interviste:** trascrizione o appunti del facilitatore, data, consenso registrato; l'intervistato si identifica come membro del comitato solo per il controllo degli accessi, mai negli output;
- **sintesi del modello:** ogni sintesi con modello e versione, versione del prompt, passaggi citati (riferimenti esatti nel documento o nella trascrizione) e stato: `stima del modello`, poi accettata o corretta dal comitato; una correzione è un record nuovo, non sovrascrive;
- **schede:** composizione congelata (task, ordine, testi mostrati), impronta, parametro usato, atto di approvazione;
- **scelte:** per ogni membro uno pseudonimo dentro l'organizzazione, scheda, task indicato come da tenere, task indicato come da cedere, momento; append-only, una scelta modificata è un record nuovo;
- **vincoli dichiarati** dai documenti, con la citazione e l'atto del comitato che li accetta o li scarta.

Nel database condiviso restano solo: gli atti del registro con l'**impronta** dei testi calcolata con la chiave dello spazio (come per gli indirizzi testuali di oggi), il profilo di pesi e le misure aggregate della stima. Gli identificativi dei task del database NEARTECH compaiono nelle schede, ma la composizione delle schede e le scelte restano nello spazio. L'uso aggregato e anonimo delle scelte per la ricerca fra organizzazioni è escluso per ora (decisione aperta 7).

Chi legge che cosa: i membri del comitato vedono le sintesi aggregate, le misure aggregate e la stima; il facilitatore vede le trascrizioni per la sintesi; l'auditor vede gli atti, le impronte, le misure e i controlli, e può chiedere di rifare la stima; l'amministratore tecnico non legge i testi.

### 4.2 Che cosa fa il modello, e che cosa no

Il modello (con versione bloccata, come ogni uso del modello nel progetto) **propone testi, non decide numeri**:

| Il modello può | Il modello non può |
|---|---|
| riassumere documenti e interviste in temi per componente di D, citando i passaggi | dare pesi, punteggi o direzioni numeriche |
| segnalare frasi che sembrano vincoli ("nessuna decisione senza una persona"), con la citazione esatta | trasformare un vincolo in parametro: lo fa un atto del comitato |
| riscrivere la descrizione breve di un task per la scheda, a partire dal mansionario | scegliere quali task entrano nelle schede o come si combinano |
| proporre il testo delle dissonanze fra dichiarato e rivelato, partendo dai numeri calcolati dal codice | interpretare le scelte o correggerle |

Regole operative:
- **Il testo dei documenti è dato, mai istruzione.** Documenti, trascrizioni e mansionari entrano nel prompt delimitati e marcati come materiale da analizzare; il prompt dice che le istruzioni contenute nel materiale non si eseguono; il modello non ha strumenti né accesso ad altro.
- **Uscita strutturata e verificata dal codice:** ogni tema o vincolo deve citare un passaggio che il codice ritrova **alla lettera** nella fonte; una citazione che non si ritrova scarta la voce.
- **Ogni sintesi dichiara da dove viene:** `stima del modello` finché il comitato non la accetta o la corregge (stessa regola della piattaforma).
- **Nessuna attribuzione:** le sintesi delle interviste riuniscono i temi di tutti gli intervistati, senza dire chi ha detto cosa; i temi citati da un solo intervistato si mostrano solo se il comitato lo decide, sapendo che in un gruppo piccolo si riconoscono.
- **Le descrizioni dei task nelle schede** si controllano contro il mansionario (il facilitatore le rivede prima dell'approvazione delle schede) e non devono contenere valutazioni ("compito di grande valore umano") che orientino la scelta.
- Il cambio di modello richiede il set di controllo e la ritaratura del prompt prima di nuove sintesi, come da standard di progetto.

## 5. Decisioni metodologiche aperte per il responsabile del progetto

1. **Formato delle schede:** best–worst da quattro task (proposta) oppure confronti a coppie, più semplici ma con circa il doppio delle schede per la stessa precisione.
2. **Componenti mancanti:** nella prima applicazione stimare solo il rapporto fra w_d1 e w_d2 e lasciare w_d3 e w_d4 al profilo di partenza (proposta), oppure usare stime del modello di d3 e d4 marcate provvisorie, oppure aspettare i questionari d3/d4.
3. **Giro individuale o di consenso:** la stima usa le scelte individuali messe insieme, e la plenaria serve a discutere (proposta), oppure la stima usa una scelta di consenso per scheda (meno dati, meno indipendenza, ma "una voce del comitato").
4. **Chi approva le schede prima della sessione:** il comitato con un atto (proposta), oppure il facilitatore con il comitato informato. Se le approva il comitato, conosce in anticipo i task: va deciso se questo indebolisce le preferenze rivelate.
5. **Margine del comitato sulla stima:** il comitato può approvare un profilo diverso dalla stima dentro l'insieme ammesso, con motivazione registrata e controllo dell'auditor (proposta); oppure solo approvare o respingere la stima e ripetere la fase.
6. **Vincoli dichiarati dai documenti:** restano testo per la discussione, oppure possono diventare, con un atto del comitato, un pavimento dell'organizzazione sopra il pavimento legale (oggi non registrato), con un controllo automatico nella verifica.
7. **Uso per la ricerca:** escludere ogni uso fuori dall'organizzazione (proposta), oppure ammettere nel database NEARTECH misure aggregate e anonime (pesi stimati, coerenza) per confrontare organizzazioni, con il consenso dell'impresa.
8. **Valori del primo parametro del metodo:** concentrazione del prior, scostamento massimo dal profilo di partenza (oggi ±50%), limiti dei pesi (oggi 0,10–0,45), numero di schede e di membri minimi, ampiezza massima degli intervalli, livello di credibilità, minimo di coerenza. Proposta: tenere limiti e scostamento di `bozza-1` e fissare gli altri dopo una prova di recupero sui dati di prova di ACME S.p.A.
9. **Enfasi per classi di task** (passo 5 del flusso della fase 6): rinviare (proposta), oppure stimare pesi diversi per processo, che richiede molte più schede.
10. **Sorte del questionario `bozza-1`:** ritirarlo quando il nuovo metodo è approvato, lasciando i profili già calcolati con le loro chiavi (proposta), oppure tenerlo come via rapida per organizzazioni che non fanno la fase di ascolto.
11. **Ripetizione:** quando si ripete la fase (cambio del perimetro, nuovi giudizi d3/d4, cambio di vertice, a scadenza fissa).
12. **Quanto pesano le interviste rispetto agli scenari:** l'intensità x della regola "più / come / meno" (proposta: metà dello scostamento massimo ammesso, così gli scenari possono sempre correggere il punto di partenza) e la forza del punto di partenza nella stima (concentrazione del prior, decisione 8).

## Che cosa servirà per costruirla (non in questa proposta)

Solo per orientare la stima del lavoro, dopo l'approvazione:
- un parametro di governance del metodo (sostituisce `questionario_indirizzi`) con i valori della decisione 8;
- una migrazione versionata dello spazio organizzazione per materiali, interviste, sintesi, schede, scelte e vincoli; nel registro, i tipi di oggetto per l'insieme di schede e per i vincoli, se servono;
- un modulo del motore per perimetro, task decisivi, disegno delle schede, prova di recupero, stima su griglia e controlli; la proposta del profilo riusa `indirizzi_pesi` dall'atto di proposta in poi;
- le schermate: caricamento dei materiali, sintesi da accettare, schede per il membro, restituzione con effetto e dissonanze, verifica dell'auditor con i controlli nuovi;
- test: la stima ritrova pesi noti su comitati sintetici; il disegno è deterministico; nessuna scelta o testo finisce in tabelle condivise; una citazione inventata dal modello viene scartata.
