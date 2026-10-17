# Video Neartech · storyboard per l'approvazione

Bozza del 2026-10-17. Formato: solo testo e motion, in italiano, 16:9 a 1920×1080. Nessun progetto è stato ancora creato su HyperFrames e nessun render è partito.

Fonti dei contenuti: `elevator-pitch.html`, `metodo-neartech-per-clienti.html` e `../metodologia-workflow-completo.md`. Identità: guida v3.1 «Luce» (`guida-identita.html`, `neartech-identita.css`).

---

## 1. Limiti del connettore e cosa comportano

| Tema | Cosa dice HyperFrames | Conseguenza per noi |
|---|---|---|
| Costo | Import e ritocchi gratuiti. Il render è l'unico passo a pagamento: 3 render al mese sui piani gratuiti, 20 crediti per minuto sui piani a pagamento. | Ogni correzione a un video lungo costa un render intero. Un video unico di 5 minuti costa circa 100 crediti per ogni render. |
| Durata | Nessun tetto dichiarato. Le tipologie di riferimento arrivano a 60 secondi (explainer) e a 90 secondi (titolo cinematografico). | Il pitch da 50 secondi è nella norma. Un video di 4 minuti è fuori dalle tipologie previste. |
| Scene | Al massimo 5 secondi per scena. Il testo deve essere tutto entrato entro metà scena. 4–10 parole richiedono 3–4 secondi, 11–20 parole 4–6 secondi; oltre 35 parole la scena va divisa. | Senza voce, tutto passa dal testo a schermo: il tempo di lettura detta la durata. |
| Transizioni | Il 95% sono tagli netti, e l'ingresso della scena nuova fa il lavoro. In una prima bozza si usa al massimo una catena di transizioni shader. | Coincide con la nostra guida: «il movimento accompagna, non attira l'attenzione». Una sola transizione speciale per video. |
| Font | Va incorporato nel file, altrimenti l'aspetto ricade su un font di sistema. La guida HyperFrames sconsiglia i font più generici (tra cui Inter) e impone di rispettare il font del marchio. | Deciso: Inter e JetBrains Mono, i font del marchio, incorporati nel file. |
| Audio | Il video che si importa è muto. Musica ed effetti sonori li aggiunge dopo l'agente di HyperFrames (passo gratuito); in locale si aggiungono con un elemento `<audio>`. | Nessuna voce. Effetti sonori sintetizzati da noi, sincronizzati con le animazioni (`suoni_pitch.py`), e musica di sottofondo a livello costante sotto gli effetti (`mixa_audio.py`). |
| Movimento | Il render è deterministico e fotogramma per fotogramma: niente animazioni guidate dal tempo reale o casuali. | La macchia dinamica e il logo animato si fanno con la timeline GSAP: si possono fare entrambi. |

**Limiti dal mio lato.** Non c'è un tetto di durata per scrivere la composizione, e posso provarla qui nel browser senza costi prima di qualunque render. Il vero limite è pratico. Un file unico da 5 minuti avrebbe circa 70 scene: è difficile da rivedere, e ogni correzione richiede di rifare il render di tutto.

## 2. Raccomandazione: due video gemelli, non uno

Due composizioni separate, con lo stesso sistema visivo. Il pitch si chiude sul logo; il metodo si apre con il logo. Messi in fila sembrano un video unico, e si possono anche unire in HyperFrames Studio.

Perché:
- **Costo.** Si corregge il pitch senza rifare il render del metodo, e viceversa.
- **Separabilità.** È garantita per costruzione, non affidata a un taglio a posteriori.
- **Momenti forti.** Ognuno ha il suo momento shader: la chiamata all'azione nel pitch, la matrice nel metodo.
- **Usi diversi.** Il pitch va in apertura di incontri e sui social, il metodo va a chi sta valutando.

## 3. Durate consigliate

| Video | Proposta iniziale | Consiglio | Perché |
|---|---|---|---|
| Elevator pitch | ~50 s | **~79 s** (12 scene) | La prima versione da 52 s era troppo veloce da seguire senza voce: ogni scena ora lascia almeno 2,5 s di sola lettura. |
| Metodo | ~250 s (5×) | **~2 min 17 s** (21 scene) | Senza voce, 4 minuti significano più di 60 schermate da leggere: la soglia di attenzione di un video di marketing cade molto prima. Con 2 minuti ogni fase ha circa 10 secondi, in due scene. |

Se servirà una versione lunga per l'onboarding dei clienti (non marketing), la faremo dopo: un capitolo per fase, riusando le stesse scene.

---

## 4. Il sistema visivo in movimento

**Superfici e tipografia.**
- Fondo Paper bianco. Carte Card #F5F6F8 con angoli di 22 px.
- Titoli in Inter 600 con tracking −0,05em, minimo 60 px a 1080p. Testo minimo 20 px, etichette 16 px.
- Accento del titolo in JetBrains Mono 500 Teal scuro, come nelle slide.
- Fonti dei dati in mono, piccole, sempre presenti quando c'è un numero.

**Voce.** Lucida, empatica, pragmatica.
- Diciamo: «Il lavoro cambia: scegliamo insieme come», «Il sapere operativo resta dell'impresa», «Nessuno viene lasciato indietro».
- Evitiamo: superlativi, la parola «sostituire», cifre senza fonte, il linguaggio di controllo.

**Movimento.**
- Nessun rimbalzo e nessun effetto elastico.
- Curve `power3.out` ed `expo.out` per gli ingressi, `sine.inOut` per il respiro continuo.
- Ingressi a 0,2 secondi dall'inizio della scena; tra una scena e l'altra tagli netti.
- Ogni scena resta viva anche dopo l'ingresso: il respiro della macchia, un contatore, una barra che si riempie, un tratto che si disegna.

**La macchia (elemento continuo).** È uno strato sotto il testo che dura per tutto il video. Respira: si espande e si contrae in cicli di 6–8 secondi, scivola nello spazio e cambia colore tra quelli del marchio. Il colore segue il racconto:
- teal quando parla il contesto;
- cobalto quando parlano i dati;
- viola quando emerge il divario;
- un alone ambra quando decide una persona.

Nelle scene dense si ritira in un angolo; nelle aperture e nelle chiusure si espande.

**Il logo Task Matrix in movimento.** L'animazione segue il significato dichiarato nella guida:
1. L'asta sale dal basso.
2. I due moduli entrano in diagonale e «scompongono il processo».
3. La sfera ambra scende e si posa: «il punto in cui una persona guarda e decide».
4. Compare il wordmark «Neartech · AI & CONSULTING».

**La sfera ambra come motivo ricorrente.** Nel metodo la sfera si stacca dal logo e diventa il segno della decisione umana. Compare su ogni fase in cui decide una persona, lungo un binario di 9 tappe che resta fermo in alto a ogni scena: tappe teal per il lavoro del sistema, tappe ambra per le decisioni. Nel finale la sfera torna al suo posto nel logo.

---

## 5. Storyboard · Elevator pitch (~79 s, con effetti sonori)

Versione 2 del 2026-10-17: la prima versione da 52 secondi era troppo veloce da seguire senza voce. Ogni scena ora lascia 2,5–3,5 secondi di sola lettura dopo l'ultimo ingresso. Gli effetti sonori sono sintetizzati in `suoni_pitch.py`: soffio per i titoli, clic per il lavoro del sistema, toni per le quote, campanella a due note per la sfera ambra (la decisione di una persona). Sotto, una musica di sottofondo («Security» di MokkaMusic, in la minore come gli effetti) a livello costante e basso, senza abbassamenti automatici (`mixa_audio.py`): accompagna l'attenzione e copre i silenzi senza coprire gli effetti.

| # | Tempo | Testo a schermo | Movimento e grafica | Fonte |
|---|---|---|---|---|
| 1 | 0–4 | «Neartech» · «AI & CONSULTING» | Costruzione del logo sul bianco. Macchia piccola, teal, che respira. | — |
| 2 | 4–9,5 | «Sai dire quali compiti del tuo lavoro» / *«cambieranno con l'AI?»* | Le righe entrano dal basso una alla volta; l'accento mono si compone lettera per lettera. La macchia si allarga a destra. | — |
| 3 | 9,5–16 | **96%** · «delle organizzazioni italiane intervistate ha già programmi di AI in corso» | Contatore da 0 a 96. Una barra si riempie, con una tacca ambra sulla media mondiale (88%). La macchia passa al cobalto. | WEF, Future of Jobs 2025, Italia |
| 4 | 16–24 | «Entro il 2030 la tecnologia svolgerà *quasi un compito su tre*» | La barra impilata «Oggi 46 / 35 / 18» si trasforma in «2030 34 / 35 / 31»: i segmenti scorrono e la parte della tecnologia cresce. | WEF 2025, p. 157 |
| 5 | 24–32 | «Il 60% dei lavoratori avrà davanti *un percorso di crescita*» | La griglia di 99 punti si colora a gruppi: 27 crescono nel ruolo, 22 cambiano ruolo, 11 seguono un percorso pensato apposta. | WEF 2025, p. 157 |
| 6 | 32–41 | «Quasi 9 organizzazioni su 10 usano l'AI.» → «Solo il 6% le attribuisce almeno il 5% dell'EBIT.» | La barra si riempie fino all'88%, poi si svuota fino al 6% e diventa ambra. La macchia passa al viola. | McKinsey, State of AI 2026 |
| 7 | 41–47 | **25%** · «delle iniziative di AI ha dato il ritorno atteso» | Contatore. La cifra resta sola sul bianco. | IBM IBV, CEO Study 2025 |
| 8 | 47–52,5 | «Il ritorno arriva a chi *ripensa il lavoro*, non solo la tecnologia.» | La macchia si contrae e poi si riapre: è il cambio di passo. | — |
| 9 | 52,5–58 | «Neartech aiuta le organizzazioni a governare il lavoro che cambia.» | Il simbolo del logo ricompare piccolo e respira accanto al testo. | — |
| 10 | 58–66 | «Due assi, per ogni compito.» · assi: «Necessità della presenza umana · vincoli tecnici» e «Desiderabilità della presenza umana · scelte di valore» | Gli assi si disegnano; i quattro quadranti si accendono uno alla volta; i compiti volano nelle loro posizioni. | — |
| 11 | 66–72 | «Prevediamo cosa verrà automatizzato.» / «Le decisioni restano alle persone.» | I punti teal (il sistema) si allineano; la sfera ambra si posa sopra. La macchia prende un alone ambra. | — |
| 12 | 72–79 | «Portateci un ruolo e un documento: *partiamo da lì*.» · pulsante «Fissiamo mezz'ora» · logo | **Transizione shader** `cross-warp-morph`, l'unica del video. Il logo si ricompone, la sfera fa un solo impulso, la macchia si espande a pieno schermo. | — |

## 6. Storyboard · Il metodo (~2 min 17 s, con effetti e musica)

Versione 2 del 2026-10-17. Testi riscritti con la skill `copywriting` (repository boraoztunc/skills) sul percorso in nove passi allineato al workflow della fase 6 (ramo `claude/magical-banach-ac1428`, documento per i clienti, sezione 03). Ritmo: 2,5–3,5 secondi di sola lettura a fine scena, come il pitch. Musica: «Upbeat Inspiring Corporate» di Wavecont/RiseArt (re maggiore, 117 BPM), a livello costante sotto gli effetti; licenza da verificare prima della diffusione.

**Scelte di copy (dalla skill).** Chiarezza prima dell'originalità; benefici prima delle funzioni; parole specifiche e voce attiva; nessun superlativo. Apertura con una domanda retorica sul problema; promessa nella formula «trasformiamo X in Y»; i nove passi raccolti in tre tempi per ridurre la complessità percepita; un'obiezione affrontata apertamente (la riservatezza dei dati); invito con verbo d'azione e ciò che si ottiene.

**Alternative per l'invito.** A) «Fissiamo mezz'ora sul vostro lavoro» (scelta: coerente con il pitch, dice che cosa si ottiene); B) «Portateci un ruolo, partiamo da lì» (più narrativa, meno azione); C) «Vedete il metodo su un vostro ruolo» (più concreta, più lunga).

Il binario delle 9 tappe compare dalla scena 5 e resta fermo in alto: tappe teal per il lavoro del sistema (1, 2, 3, 6), tappe ambra per le decisioni delle persone (4, 5, 7, 8, 9).

| # | Tempo | Tappa | Testo a schermo | Movimento e grafica |
|---|---|---|---|---|
| 1 | 0–3,5 | — | «Neartech» · etichetta «Il metodo, passo per passo» | Il logo si costruisce in 2,5 secondi; la sfera ambra si posa. |
| 2 | 3,5–9 | Apertura | «L'AI cambierà il vostro lavoro.» / *«Sapete già dove, e di quanto?»* | Domanda retorica sul problema. Righe dal basso, accento mono lettera per lettera. |
| 3 | 9–15 | Promessa | «Trasformiamo le vostre job description in una mappa del lavoro che cambia.» · «Compito per compito, con le vostre persone.» | Formula «trasformiamo X in Y». La macchia si apre. |
| 4 | 15–21 | Tre tempi | «Nove passi, in tre tempi.» · «Leggiamo il lavoro» · «Mettiamo la vostra visione nei numeri» · «Verifichiamo, e decidete voi» | Il binario delle 9 tappe si disegna, diviso in tre tratti. |
| 5 | 21–28 | 01 Scomposizione | «Ogni job description diventa una lista di task.» · «Ogni task cita la riga da cui nasce. Niente task inventati.» | Le righe di un mansionario si spezzano in schede; un filo collega una scheda alla sua riga. |
| 6 | 28–35 | 02 Abbinamento | «Ogni task trova il suo riferimento nella base NEARTECH.» · «Standard globali, europei e italiani. Il revisore approva il lotto.» | Le schede si agganciano a una griglia; una spunta ambra approva il lotto. |
| 7 | 35–42,5 | 03 Punteggio | «Task già noto? Eredita il punteggio.» / *«Task nuovo? Lo deriviamo dai più simili.»* | Una scheda tratteggiata si collega a tre task simili con i loro pesi; compare l'etichetta «derivato per somiglianza». |
| 8 | 42,5–48,5 | Dati | «Nella base condivisa entrano solo dati anonimi.» · «I vostri documenti, log e azioni restano nella vostra sezione.» | Due contenitori: la base NEARTECH e la vostra sezione. Risponde all'obiezione sulla riservatezza. |
| 9 | 48,5–55 | 04 Comitato | «Il vostro comitato guida vede ogni task, fino al singolo.» / *«La sua leva vera sono gli indirizzi.»* | Barre per funzione; zoom su un task. La sfera ambra si posa sulla tappa 4. |
| 10 | 55–63 | 05 Indirizzi | «Interviste e questionari traducono la vostra visione in pesi.» · relazione e fiducia · responsabilità · senso del lavoro · valore per chi lo riceve | Quattro cursori si spostano e trovano la loro posizione. |
| 11 | 63–70 | 05 Garanzie | «I pesi aggiungono enfasi sopra il pavimento di legge. Mai sotto.» · «Valgono con l'approvazione del comitato e il via libera dell'auditor.» | Una barra con la linea del pavimento di legge; l'enfasi cresce sopra. Due spunte: comitato, auditor. |
| 12 | 70–77 | 06 Classificazione | «Con i vostri pesi, il calcolo riclassifica tutti i task.» · «Stessi dati, stesse regole, stesso risultato.» | **Transizione shader** `cross-warp-morph` verso la matrice dei due assi; i punti si spostano nei quadranti. |
| 13 | 77–84 | Questionari | «Lavoratori e beneficiari rispondono a un questionario anonimo.» · «Le risposte si leggono solo per gruppi di almeno 5.» | Una scheda «Il tuo lavoro, in 12 domande» con la nota «anonimo · gruppi di almeno 5». |
| 14 | 84–90,5 | 07 Revisione | «I revisori controllano un campione, partendo dai task più incerti.» | Una griglia di task: si accendono quelli del campione, prima i più incerti. |
| 15 | 90,5–98,5 | 08 Correzioni | «Una correzione vale per quel task, ovunque compaia.» · «Un errore sistematico va al comitato. Il sistema non corregge da solo.» | Una cella corretta si propaga alle sue occorrenze; compare la proposta «ricalibrare i pesi?» per il comitato. |
| 16 | 98,5–106 | 09 Restituzione | «Il comitato vede il risultato per funzione e approva la restituzione.» · «Nessun risultato riguarda una singola persona.» | Barre per funzione in quadranti; il marchio «Approvata dal comitato». |
| 17 | 106–112 | Trasparenza | «L'auditor segue ogni passo.» / *«Ogni decisione ha un autore e un perché.»* | Una traccia di quattro atti, ciascuno con autore e motivazione. |
| 18 | 112–118 | Aggiornamento | «La tecnologia cambia. La base si aggiorna, e vi dice cosa è cambiato.» | Il binario si richiude ad anello; la macchia cambia colore. |
| 19 | 118–124 | Risultato | «Sapete cosa automatizzare, cosa potenziare e chi far crescere.» | Tre righe, tre colori: teal, cobalto, ambra. |
| 20 | 124–128,5 | Persone | «Nessuno resta indietro.» | Scena sola, molto spazio bianco. |
| 21 | 128,5–136,5 | Invito | «Portateci un ruolo: in mezz'ora vedete il metodo sul vostro lavoro.» · pulsante «Fissiamo mezz'ora sul vostro lavoro» · logo | La sfera ambra torna nel logo; il lockup si chiude. |

Totale: 136,5 secondi. Ogni scena resta sotto le 20 parole.

---

## 7. Come lo costruirei

1. **Scrivo io la composizione** in HTML con timeline GSAP, secondo il contratto HyperFrames:
   - font Inter e JetBrains Mono incorporati;
   - logo in SVG nel file;
   - macchia e logo animati in modo deterministico.
   La provo qui fotogramma per fotogramma, a costo zero.
2. **La porto in HyperFrames.** L'import accetta solo il link che consegna il pulsante «Send to HyperFrames» di Claude Design. Prima di tutto verifico se quel percorso è disponibile da qui.
   - Se non lo è, l'alternativa è `compose`: gli descrivo il video a parole e l'agente HyperFrames lo costruisce da sé. Funziona, ma con meno controllo sull'identità, perché nessuno dei suoi stili predefiniti è il nostro.
3. **Ritocchi in HyperFrames**, gratuiti, ed eventuale musica.
4. **Render**, il passo a pagamento, solo dopo la tua approvazione del montaggio.

## 8. Decisioni che servono da te

- **A. Due video o uno.** Raccomando due video gemelli.
- **B. Durata del metodo.** Raccomando circa 2 minuti invece di circa 4.
- **C. Font.** Il portfolio che ti è piaciuto è costruito con v0 di Vercel, il cui font predefinito è **Geist**: è possibile che il font che ti ha colpito sia Geist e non Inter. Non posso esserne certo dagli screenshot. Propongo di confrontare i due font su un fotogramma prima di costruire tutto. **Deciso dopo il confronto: Inter + JetBrains Mono.**
- **D. Musica.** Decisa: pitch con «Security» di MokkaMusic (la minore), metodo con «Upbeat Inspiring Corporate» di Wavecont (re maggiore), entrambe a livello costante sotto gli effetti (`mixa_audio.py`), senza abbassamento automatico (si sentiva come pompaggio). Da verificare la licenza e l'eventuale obbligo di citare l'autore prima della diffusione.
- **E. Contatto per la chiamata all'azione.** Serve un recapito reale (sito o email). Le regole HyperFrames vietano i segnaposto, e oggi il pulsante «Fissiamo mezz'ora» non porta da nessuna parte.
