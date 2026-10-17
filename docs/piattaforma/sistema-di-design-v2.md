# Sistema di design v2 · piattaforma e sito pubblico

**Stato:** specifica di riferimento per l'implementazione, 18 ottobre 2026. Scritta dal direttore creativo; implementa la sessione principale.
**Base:** la direzione «Precisione quieta · carta e inchiostro», scelta da tutte e tre le giurie, con gli innesti indicati come **[TS]** (da «Timbro a secco») e **[PP]** (da «Prima pagina»).
**Rapporto con gli altri documenti:** sostituisce le sezioni 1 e 2 di `direzione-creativa.md` (17/10). Del tracciato a sigilli resta l'idea: tratte di lavoro calcolato separate dai sigilli degli atti. Cambiano gerarchia, misure e banda dell'azione. Voce e termini restano quelli di `voce-e-testi.md`. Palette, caratteri e logo restano quelli di `docs/identita/`. Fonte unica dei token: `web/src/stile.css`, dove si incolla il blocco della sezione 15.

---

## 0. Decisioni in sintesi

1. **Idea guida: il verbale del pilota.** Carta quieta, inchiostro solo dove c'è un significato, un posto preciso per ogni atto. Quattro materiali, ciascuno con un significato: rilievo (si apre o si preme), piano (si legge), incasso (il posto dell'atto), sospeso (temporaneo).
2. **Il percorso diventa la testata della pagina.** L'h1 è «Fase 2 di 4 · Indirizzi» a 24 px. Il tracciato compatto è sulla stessa riga. La banda dell'azione è attaccata alla fase corrente con una linguetta, non con una tacca calcolata. Il percorso è alto 192 px. La mappa intera, con le fasce Q4/Q2 e l'asse N, sta nella prima schermata a 1440×900, 1280×800, 1280×720 e 1300×670.
3. **Sei stili di testo** (32 · 24 · 18 · 14 · 13 · mono 12), pesi 400 e 600. Nessun maiuscolo nell'app, nessun eyebrow. Mono solo per i codici. Numeri in formato it-IT.
4. **Un colore, un significato.** Le tinte q1–q4 compaiono solo sulla mappa. Lo smeraldo scuro vuol dire «giudizio di persona», l'ambra scura «stima del modello», il rosso scuro «qualcosa non va». Il bordo dei controlli è lo stone dell'identità, #64748B: 4,76:1 sul bianco e almeno 4,03 su ogni tinta [PP].
5. **Mappa:** etichette e conteggi stanno in fasce HTML fuori dal disegno, che nessun punto può coprire [PP]. La legenda sta sopra il disegno, con i segni veri e i conteggi [PP]. Due canali binari più un anello. Margine interno di 16 px su entrambi gli assi [PP]. I punti coincidenti si dispongono su un cerchio [PP]. L'ellisse usa unità separate per N e D [PP]. La navigazione da tastiera è spaziale [TS]. Sotto i 520 px la mappa diventa una matrice 2×2.
6. **KPI come lenti [TS]:** tre bottoni con `aria-pressed` che evidenziano i task sulla mappa e filtrano la tabella. Uno solo è pieno in navy: quello che aspetta chi guarda.
7. **Menu:** un solo asse a x = 28 e piede fisso con «Esci» alto 44 e scritto per esteso [TS]. Sotto i 1024 px: barra alta da 56 e barra delle sezioni in basso con al massimo 4 posti [TS].
8. **Nessuna pseudo-azione:** una forma che sembra premibile è sempre un `a` o un `button`. Chi non può agire vede chi decide, mai un comando spento.
9. **Il nome delle voci viene dalla rubrica:** k1–r e d1–d2 da `rubrica-bozza-3.json` (via API), d3–d4 dal questionario. Nessun codice compare da solo.
10. **Sito pubblico:** gli stessi segni e lo stesso tracciato della piattaforma. I due video si avviano solo con un clic e hanno il testo integrale accanto. Una sola superficie navy.

---

## 1. Idea guida e principi

### Il verbale del pilota

Un pilota NEARTECH è un percorso di atti: il codice calcola, le persone firmano. La piattaforma ne è il verbale. Il foglio è neutro e silenzioso, l'inchiostro compare dove c'è un significato e ogni atto ha il suo posto. Il segno riconoscibile del prodotto è la **linguetta**: la fase corrente del tracciato si apre verso il basso nella banda dove si compie l'atto. In riunione, proiettata, la schermata si legge in quest'ordine: **dove siamo e che cosa tocca a voi → dove sta ogni task → quanto è solida la mappa**.

### Principi (verificabili)

| # | Principio | Che cosa vuol dire in pratica |
|---|---|---|
| P1 | **Un colore, un significato** | Ogni colore ha un solo uso (tabella in 4.3). Nessuna tinta dei quadranti fuori dalla mappa. |
| P2 | **Un segno, ovunque lo stesso** | I segni (punto pieno, cerchio vuoto, anello tratteggiato, sigilli) sono identici in mappa, legenda, KPI, tracciato e sito (sezione 8). |
| P3 | **Il materiale dice che cosa si può fare** | *Rilievo*: si apre o si preme. *Piano*: si legge. *Incasso*: il posto dell'atto, vuoto con il comando quando tocca a qualcuno, pieno con il sigillo quando l'atto è posto [TS]. *Sospeso*: temporaneo. Nient'altro ha queste forme. |
| P4 | **Un livello tipografico per riga** | Sei stili. Mai un'etichetta in linea con un titolo. Mono solo per i codici. |
| P5 | **La risposta nella prima schermata** | La mappa intera sta sopra la piega a 1280×800 e a 1300×670 (bilancio in 2.5). |
| P6 | **Niente pseudo-azioni, niente comandi spenti senza motivo** | Forma premibile ⇔ elemento premibile. Chi non può agire legge chi decide. |
| P7 | **I risultati portano le loro chiavi, in parole** | Sotto ogni calcolo: «Pesi: default NEARTECH · rubrica in vigore · calcolo del …». Il dettaglio in codice resta dentro «Chiavi del calcolo». |
| P8 | **Numeri all'italiana** | `Intl.NumberFormat('it-IT')`: «0,45», «62%», «1.234», «1,20 €», «17 ottobre 2026, 14:20». |

---

## 2. Griglia, spazi, punti di rottura

### 2.1 Unità e scala degli spazi

L'unità di base è 4 px e il ritmo verticale è di 8 px. Margini, padding e gap vengono solo da questi token:

| Token | `--s-1` | `--s-2` | `--s-3` | `--s-4` | `--s-5` | `--s-6` | `--s-7` | `--s-8` | `--s-9` |
|---|---|---|---|---|---|---|---|---|---|
| px | 4 | 8 | 12 | 16 | 24 | 32 | 48 | 64 | 96 (solo sito) |

- Sono ammessi anche i valori negativi.
- Non sono spazi, quindi restano fuori dalla scala: bordi (1, 2), scarto del focus (2), sovrapposizione dei sigilli (−4) e dimensioni dei componenti (icone 16/20/24, avatar 32, barre 4/8).
- Spariscono 2, 3, 6, 9, 10, 14, 18, 20, 22, 26, 40 e 60 come spazi, le `clamp()` di `--gap`, `--margine-pagina` e `--colonna-laterale` e tutti i 63 `style={{}}` con spazi o grandezze.
- Tutte le interlinee sono multiple di 4.

### 2.2 Fasce

| Fascia | Finestra | Navigazione | Margini | Colonne | Gutter | Contenuto misurato (colonna) |
|---|---|---|---|---|---|---|
| Ampia | ≥ 1440 | menu 240 | 32 | 12 | 24 | 1440 → 1136 (72,7) · 1920 → 1360 (91,3) |
| Media | 1280–1439 | menu 240 | 32 | 12 | 24 | 1280 → 976 (59,3) · 1366 → 1062 |
| Stretta | 1024–1279 | menu 240 | 24 | 12 | 24 | 1024 → 736 (39,3) · 1100 → 812 |
| Tablet | 768–1023 | barra alta 56 + barra delle sezioni 64 | 24 | 12 | 16 | 768 → 720 (45,3) |
| Telefono | < 768 | barra alta 56 + barra delle sezioni 64 | 16 | 4 | 16 | 390 → 358 (77,5) |

- Contenuto largo al massimo 1360, centrato a destra del menu. Sparisce la variante del menu a 256 px.
- Le colonne della panoramica sono `grid-column: 1 / 9` e `9 / 13` della griglia a 12, non `8fr 4fr`, che sbaglia di 8 px. Larghezze: a 1440 749 | 363, a 1280 643 | 309, a 1920 899 | 437.
- Margini della pagina: 24 sopra e 64 sotto. Sul telefono 24 sopra e 64 + 24 + `env(safe-area-inset-bottom)` sotto, per la barra delle sezioni.

### 2.3 Container query (il componente reagisce alla sua larghezza, non alla finestra)

| Contenitore | Soglia | Effetto |
|---|---|---|
| `.main-contenuto` (`contenuto`) | ≥ 880 | panoramica a due colonne (8 \| 4); sotto, una colonna |
| `.percorso` | < 760 | testata sopra il tracciato; banda a una colonna, comando sotto il testo |
| `.percorso` | < 520 | tratte con solo linea, sigilli, nome e stato; prove in un `<details>` |
| `.mappa-card` (larghezza interna) | < 520 | matrice 2×2 di bottoni al posto della dispersione |
| cella di fascia della mappa | < 120 | solo «Q2 · 4»; i nomi vanno nell'elenco sotto il disegno |

Per lo stack `react` la skill non ha restituito nulla su «container query responsive layout»: container query e `ResizeObserver` sono una scelta mia.

### 2.4 Ritmo verticale (regole)

- Fra superfici sorelle 24, cioè il gutter (16 sotto i 1024).
- Padding delle superfici 24, 16 sotto i 768.
- Dal titolo di una superficie al suo contenuto 16. Fra gruppi nella stessa superficie 24.
- Fra righe di un elenco 8.
- Dall'etichetta al campo 8, dal campo all'aiuto 4.
- Fra le domande di un modulo 32: 16 + filetto + 16.
- Dall'intestazione di pagina al primo contenuto 24.
- Altezze: comandi e righe interattive 44 (48 sul telefono quando sono a tutta larghezza), righe di tabella 48, righe in rilievo almeno 56.

**Altezze basse, `@media (min-width: 1024px) and (max-height: 760px)`:**
- margine alto della pagina 16;
- padding alto del percorso 16;
- padding alto del menu 16 e spazi fra i suoi blocchi 16;
- riga «Pilota in sperimentazione» nascosta.

I bersagli non scendono mai sotto 44.

### 2.5 Bilancio verticale della panoramica (verificabile)

Le misure, dall'alto:
- margine della pagina 24, oppure 16 sotto i 760 px di altezza;
- percorso 192 (184): padding 24 (16), riga di testata 76, spazio 16, banda 76;
- gap 24;
- card della mappa: padding 24, h2 24, spazio 12, riga guida 20, spazio 4, fascia alta 48, poi l'area dei dati (altezza H), la fascia bassa 48 e la riga dell'asse N 24.

**Altezza dell'area dei dati:**

`H = max(224, min(round(Wd × 0,45), innerHeight − topDati − 88, 440))`

- `Wd` è la larghezza dell'area dei dati: larghezza interna della card meno i 40 della gronda di D.
- `topDati` è la posizione dell'area dei dati nel documento, misurata al montaggio e al ridimensionamento, mai durante lo scorrimento.
- 88 = fascia bassa 48 + asse 24 + 16 di aria.

| Finestra | Card della mappa da | Area dei dati da | H | Fine dell'asse N | Piega |
|---|---|---|---|---|---|
| 1440×900 | 240 | 372 | 297 | 741 | 900 ✓ |
| 1280×800 | 240 | 372 | 250 | 694 | 800 ✓ |
| 1280×720 (proiettore) | 224 | 356 | 250 | 678 | 720 ✓ |
| 1300×670 (finestra del responsabile) | 224 | 356 | 226 | 654 | 670 ✓ |
| 1366×657 | 224 | 356 | 224 | 652 | 657 ✓ |
| 1920×1080 | 240 | 372 | 365 | 809 | 1080 ✓ |

La banda dell'azione e il suo comando stanno sempre entro i primi 216 px.

---

## 3. Tipografia

### 3.1 Sei stili (token `font`, mai grandezze scritte a mano)

| # | Stile | Token | Carattere | ≥ 768 | < 768 | Peso | Tracking | Usi |
|---|---|---|---|---|---|---|---|---|
| 1 | Numero | `--t-numero` | Inter, cifre tabellari | 32/40 | 32/40 | 600 | −0,02em | valori dei KPI, il numero di un effetto («4 task su 27 cambiano quadrante»); al massimo 3 per schermata |
| 2 | Pagina | `--t-pagina` | Inter | 24/32 | 24/32 | 600 | −0,015em | h1, uno per schermata; nelle home è «Fase 2 di 4 · Indirizzi» |
| 3 | Titolo | `--t-titolo` | Inter | 18/24 | 18/24 | 600 | −0,01em | h2 delle superfici, titolo della banda e dei dialoghi, domande, conteggi dei quadranti |
| 4 | Corpo | `--t-corpo` / `--t-corpo-forte` | Inter | 14/24 | 16/24 | 400 / 600 | 0 | paragrafi, celle, campi, voci del menu; il 600 per nomi, comandi, etichette di campo e voce attiva |
| 5 | Piccolo | `--t-piccolo` / `--t-piccolo-forte` | Inter | 13/20 | 14/20 | 400 / 600 | 0 | sempre in `--testo-2`: metadati, aiuti, legenda, assi, stati, note; il 600 per intestazioni di tabella, testo dei badge e prima riga delle etichette dei quadranti |
| 6 | Codice | `--t-codice` | JetBrains Mono | 12/16 | 12/16 | 500 | 0 | solo valori da confrontare carattere per carattere: impronte, id di lotto, versioni dentro «Chiavi del calcolo», soggetto SSO, nome tecnico di un parametro |

**Regole**
- Nessun testo sotto i 13 px; solo il Codice scende a 12. Sotto i 768 px il minimo sale a 14. Vale anche per l'SVG, che è disegnato in px reali.
- Un livello tipografico per riga, mai due stili sulla stessa linea di base. Unica eccezione: un prefisso nello **stesso** stile e in un altro inchiostro («Tocca a voi:» in teal-ink dentro un Titolo).
- Nessun `text-transform: uppercase` nell'app e nessun eyebrow. Maiuscola solo sulla prima parola.
- Inter solo a 400 e 600; il 700 resta solo in `.logo-nome`. JetBrains Mono solo con la classe `.codice`.
- Numeri in Inter con `font-variant-numeric: tabular-nums`, mai in mono: N, D e pesi a due decimali («0,56», «0,25»), percentuali intere («74%»), date «17 ottobre 2026, 14:20» nel testo e «17/10/2026» in tabella.
- «Su» per le proporzioni («20 su 27 risultati solidi»), «di» per passi e avanzamenti («Fase 2 di 4», «3 di 8 risposte») [PP].
- Lunghezza della riga: al massimo 72ch nei paragrafi, 64ch nelle descrizioni dentro le card. `text-wrap: balance` sui titoli.
- Corpo e Piccolo si distinguono per colore e ruolo, non solo per grandezza. Il 600 non serve a enfatizzare frasi intere.
- Correzioni di testo già individuate:
  - «sotto il 0.1 o sopra il 0.45» → «sotto 0,10 o sopra 0,45»;
  - «non arriva al 80%» → «non arriva all'80%»;
  - «0.250» → «0,25»;
  - «stima del modello: 2.5» → «Stima del modello: 2,5, fra il livello 2 e il 3».

### 3.2 Sito pubblico (lettura a distanza: stessi ruoli, scalati)

| Stile | ≥ 768 | < 768 | Peso |
|---|---|---|---|
| Apertura | 48/56, −0,03em | 36/44 | 600 |
| Sezione | 32/40, −0,02em | 28/36 | 600 |
| Titolo | 20/28 | 20/28 | 600 |
| Corpo | 16/28 (testo d'apertura in `--testo`, al massimo 56ch) | 16/28 | 400 / 600 |
| Piccolo | 14/20 | 14/20 | 400 / 600 |
| Etichetta di sezione | JetBrains Mono 12/16, +0,08em, maiuscolo, teal-ink, quadratino teal 8×8 | uguale | 600 |

- L'etichetta di sezione è il segno dell'identità (`neartech-identita.css`, `.eyebrow`). Sul sito è ammessa al massimo una volta per sezione, sempre su una riga propria sopra l'h2, mai in linea.
- Il sito non usa il Codice.

Skill: `font-scale`, `weight-hierarchy`, `readable-font-size`, `line-length-control`, `number-tabular`, `number-formatting` e `heading-line-balance`. Dalla tipografia «Dashboard Data» ho preso la regola «Code for data, Sans for labels», ristretta: il mono va ai codici, non alle cifre. Ho scartato per vincolo d'identità i caratteri proposti da `--design-system` (Outfit e Work Sans) e da «Dashboard Data» (Fira).

---

## 4. Colore

### 4.1 Token (palette di marca invariata; nuovi solo neutri di superficie)

| Token | Valore | Ruolo |
|---|---|---|
| `--testo` | #0F172A (obsidian) | testo principale |
| `--testo-2` | #475569 (slate) | **unico** grigio secondario; `--stone-ink` #526175 esce dal testo, perché contro slate dà 1,20:1 |
| `--testo-titolo` | #0B2559 (navy) | titoli, numeri |
| `--link` | #1B499F (cobalt) | link, comando testuale |
| `--testo-su-scuro` / `--testo-su-scuro-2` | #FFFFFF / #CBD5E1 | testo su navy e navy-800 |
| `--accento-su-scuro` | #7EE0E0 | solo l'icona di conferma negli avvisi temporanei |
| `--tela` | #F3F5F9 | fondo della pagina e incasso |
| `--superficie` | #FFFFFF | card, righe, campi |
| `--superficie-scura` | #0B2559 | voce attiva, KPI principale, bottone primario, riga selezionata |
| `--superficie-sospesa` | #07193D | suggerimento della mappa, avviso temporaneo |
| `--contatore-su-scuro` | #324874 (nuovo) | contatore dentro la voce attiva |
| `--bordo-superficie` | #E4E9F1 | raggruppa e separa; decorativo (1,22:1), non porta informazione |
| `--bordo-controllo` | #64748B (stone dell'identità) [PP] | campi, pillole di risposta, livelli, bottoni secondari, caselle, sigilli vuoti, tacche degli assi, tratteggio del futuro |
| `--binario` | #E4E9F1 | parte vuota di tratte e barre; il numero è sempre scritto accanto |
| `--sfondo-dialogo` | rgba(7,25,61,.48) | dietro i dialoghi |

**Da togliere:**
- `--card` #F5F6F8 e `--border` #E2E8F0 (sostituiti da `--bordo-superficie`);
- #94A3B8, #9FB3D9 e #C5CFDD;
- il teal #00B4B4 e l'ambra #F59E0B come segni;
- ogni `opacity` su testo e bottoni;
- i colori saturi delle mini-barre (`Panoramica.tsx:17`);
- tutti gli esadecimali nei componenti.

### 4.2 Contrasti misurati (formula WCAG; ogni coppia in uso)

**Testo**, soglia 4,5:1:

| Inchiostro | bianco | tela | q1 | q2 | q3 | q4 | #E4E9F1 | navy | navy-800 |
|---|---|---|---|---|---|---|---|---|---|
| `--testo` #0F172A | 17,85 | 16,36 | 16,51 | 15,10 | 16,03 | 15,90 | 14,64 | — | — |
| `--testo-2` #475569 | 7,58 | 6,94 | 7,01 | 6,41 | 6,81 | 6,75 | 6,22 (disabilitato) | — | — |
| navy #0B2559 | 14,76 | 13,52 | 13,65 | 12,48 | 13,25 | 13,14 | 12,10 | — | — |
| cobalt #1B499F | 8,40 | 7,70 | 7,77 | 7,10 | 7,54 | 7,48 | — | — | — |
| teal-ink #007272 | 5,75 | 5,27 | 5,32 | 4,87 | 5,17 | 5,12 | 4,72 | — | — |
| emerald-ink #065F46 | 7,68 | 7,04 | 7,11 | 6,50 | 6,90 | 6,84 | 6,30 | — | — |
| amber-ink #92400E | 7,09 | 6,50 | 6,56 | 6,00 | 6,37 | 6,31 | — | — | — |
| risk-ink #9F1239 | 8,02 | 7,34 | — | — | — | — | — | — | — |
| #FFFFFF | — | — | — | — | — | — | — | 14,76 | 17,28 |
| #CBD5E1 | — | — | — | — | — | — | — | 9,94 | 11,64 |
| #7EE0E0 | — | — | — | — | — | — | — | 9,57 | 11,21 |

Altri testi: bianco su cobalt (passaggio sul primario) 8,40; bianco su risk-ink (distruttivo) 8,02; bianco su #324874 (contatore) 9,07.

**Segni, bordi e focus**, soglia 3:1 (WCAG 1.4.11):

| Elemento | Colore | Rapporto |
|---|---|---|
| Bordo dei controlli | #64748B | 4,76 sul bianco · 4,36 sulla tela · 4,40 su q1 · 4,03 su q2 · 4,27 su q3 · 4,24 su q4 |
| Punto «giudizio di persona» | #065F46 pieno | 6,50–7,11 sulle tinte |
| Cerchio «stima del modello» | #92400E, tratto 2 | 6,00–6,56 sulle tinte |
| Anello «incerto» e punto attivo | navy | ≥ 12,48 |
| Punto attenuato da una lente | #475569, tratto 1 | ≥ 6,41 |
| Riempimento della tratta in corso | teal-ink | 4,72 sul binario |
| Barre della sperimentazione | emerald-ink | 6,30 sul binario |
| Tratta da fare, sigillo vuoto | #64748B tratteggiato | 4,76 |
| Focus | teal-ink 2 px | 5,75 sul bianco · 5,27 sulla tela · ≥ 4,87 sulle tinte |
| Focus su navy | #FFFFFF 2 px | 14,76 |

**Coppie bandite, con la misura di oggi:**
- voci «In arrivo» #94A3B8: 2,56;
- primario disabilitato al 50%: 3,13;
- ambra #F59E0B: 2,15 sul bianco, 1,93 su q3;
- teal #00B4B4 sul bianco: 2,56;
- #C5CFDD: 1,57;
- #E2E8F0 sui campi: 1,23;
- #7E8BA0 su q2: 2,92.

### 4.3 Un colore, un significato

| Colore | Significato unico | Dove |
|---|---|---|
| navy | **l'atto e il presente**: dove sei, che cosa premi, che cosa ti aspetta, che cosa è stato posto | voce attiva, primario, KPI principale, riga selezionata, sigillo posto, tratta fatta, conferma di successo |
| teal-ink | **avanzamento in corso e turno** | riempimento della tratta in corso, barra «3 di 8 risposte», prefisso «Tocca a voi:», focus |
| emerald-ink | **giudizio di persona** | punto pieno, barre «giudizi di persona», segno nel badge |
| amber-ink | **stima del modello** | cerchio vuoto, binario della stima nella rubrica, segno nel badge |
| cobalt | **link, e provenienza derivata** | link, passaggio sul primario, mezzo cerchio «derivato per somiglianza», quadrato «nuovo» |
| risk-ink | **qualcosa non va** | errori, «non superato», «non riuscito», distruttivo |
| q1–q4 | **i quadranti** | solo tessere e fasce della mappa, matrice 2×2, campioni nelle intestazioni di tabella |
| violet, teal, ambra, smeraldo | logo e illustrazioni del sito | mai segno, testo o bordo nell'app |

Messaggi di sistema: hanno tutti il fondo `--tela`, un filetto sinistro di 4 px, un'icona e un testo.
- Errore: risk-ink con l'icona warning-circle.
- Successo, avviso e nota: navy, distinti per forma dell'icona (check-circle, warning, info), non per colore. Così l'ambra resta alla stima e il verde alla persona, e scompaiono le collisioni di oggi: «stima» usata per «provvisoria» e «uguali», «persone» per «superato» e «quote».

---

## 5. Superfici, raggi, bordi, ombre

### 5.1 Materiali

| Materiale | Che cosa vuol dire | Fondo | Bordo | Ombra | Usi |
|---|---|---|---|---|---|
| **Tela** | il fondo | `--tela` | — | — | pagina |
| **Superficie** | raggruppa | bianco | 1 px `--bordo-superficie` | `--ombra-superficie` | card, percorso, mappa, KPI, contenitori di tabelle. Mai una superficie con ombra dentro un'altra |
| **Riga in rilievo** | si apre | bianco | 1 px `--bordo-superficie`; al passaggio `--bordo-controllo` | `--ombra-riga`; al passaggio `--ombra-riga-alta` | coda, lotti, coppie, proposte, organizzazioni, elenco dei task, tessere della matrice, lenti |
| **Riga piana** | si legge | trasparente | filetto basso 1 px | — | inviti senza schermata, controlli automatici, righe di tabella |
| **Incasso vuoto** | il posto dell'atto che tocca a qualcuno | `--tela` dentro una superficie | filetto alto 1 px | — | banda dell'azione, linguetta della fase corrente |
| **Incasso pieno (impresso)** [TS] | atto posto | `--tela` | — | `--ombra-impresso` | righe della coda completate, atti del registro, lotti decisi, domande risposte nel riepilogo. Sempre con spunta e testo («registrato», «6 di 6 voci»): l'ombra interna è un canale secondario, in proiezione non basta |
| **Sospeso** | temporaneo | `--superficie-sospesa`, oppure bianco per i pannelli | — | `--ombra-sospesa` | suggerimento, avviso temporaneo, prove di una fase, pannello laterale |
| **Dialogo** | chiede una decisione | bianco | — | `--ombra-dialogo` | `<dialog>` |
| **Comando** | si preme | navy, oppure bianco con bordo | — | `--ombra-comando`, solo sul primario e sulla voce attiva | bottoni, voci, pillole |

### 5.2 Raggi (quattro, ciascuno con un significato)

- **20:** superficie e dialogo.
- **12:** riga, campo, tessera e fascia della mappa, linguetta, suggerimento, messaggio, livello della rubrica.
- **6:** badge (etichetta che non si preme).
- **999:** comando: bottone, voce del menu, pillola di risposta, contatore, indicatore della barra delle sezioni.
- Cerchi (sigilli, avatar, punti) e barre sottili da 4 o 8 px sono geometria, non pillole.
- Regola: un testo dentro una pillola si può sempre premere, quindi un badge non è mai una pillola.
- Spariscono 22, 18, 16, 14 e 10.

### 5.3 Bordi

- 1 px `--bordo-superficie` per superfici, righe e filetti.
- 1 px `--bordo-controllo` per i controlli.
- 2 px navy per la scelta fatta (livello, risposta, lente premuta).
- 2 px tratteggiato `--bordo-controllo` per il futuro del percorso.
- 2 px risk-ink per il campo in errore.
- Mai un bordo colorato per decorare. Sparisce lo spessore 1,5.

### 5.4 Ombre (solo navy, mai nere)

```
--ombra-superficie: 0 1px 2px rgba(11,37,89,.06), 0 4px 12px -4px rgba(11,37,89,.08);
--ombra-riga:       0 1px 2px rgba(11,37,89,.08);
--ombra-riga-alta:  0 2px 4px rgba(11,37,89,.06), 0 8px 16px -8px rgba(11,37,89,.16);
--ombra-comando:    0 1px 2px rgba(11,37,89,.16), 0 4px 12px -4px rgba(11,37,89,.32);
--ombra-sospesa:    0 8px 24px -8px rgba(7,25,61,.32);
--ombra-dialogo:    0 24px 48px -12px rgba(7,25,61,.32);
--ombra-impresso:   inset 0 1px 2px rgba(11,37,89,.10), inset 0 0 0 1px #E4E9F1;
--ombra-scorrimento: 0 -8px 12px -8px rgba(11,37,89,.16);
```

Spariscono:
- l'ombra nera rgba(0,0,0,.45) della banda;
- l'ombra interna delle barre;
- le ombre su misura di accesso e dialogo (0 30px 60px);
- il filtro `feDropShadow` delle tessere della mappa, perché i dati non hanno ombra (`trend-emphasis`).

### 5.5 Livelli

| z-index | Elemento |
|---|---|
| 10 | menu e barre del telefono |
| 20 | barra del task in Revisione |
| 30 | suggerimento della mappa, prove di una fase |
| 40 | pannello laterale |
| 50 | avvisi temporanei |
| strato superiore nativo | dialoghi `<dialog>` |

- Con la barra sticky della Revisione: `scroll-padding-top: 80px`.
- Sotto i 1024: `scroll-padding-bottom: 88px`, per la barra delle sezioni.

Skill: `elevation-consistent`, `spacing-scale`, `z-index-management`, «Focus Not Obscured (Minimum)», `trend-emphasis`. Il `--design-system` «enterprise governance decision tool workforce» (variance 2, motion 2, density 6) restituisce «Minimalism & Swiss Style». Ne prendo griglia, gerarchia ed essenzialità. L'indicazione «sharp shadows if any» cede al riferimento del responsabile: ombre morbide, bordo sottile, raggio ampio. Scartati la palette #1E3A5F / #2563EB / #059669 e i caratteri Outfit e Work Sans.

---

## 6. Movimento

**Token**
- `--dur-breve` 120ms: colore al passaggio, pressione.
- `--dur-media` 200ms: details, suggerimento, avviso, dialogo, sigillo.
- `--dur-lunga` 320ms: barre e tratte che cambiano valore.
- Curve: `--ease` cubic-bezier(.22,1,.36,1) in entrata, `--ease-uscita` cubic-bezier(.4,0,1,1) in uscita.
- Le uscite durano il 60–70% delle entrate.
- Si animano solo `transform` e `opacity`, più colore di fondo e bordo al passaggio.

**Regole**
1. Al primo caricamento non si anima nulla: i dati si leggono subito. Spariscono il riempimento «riempi» al montaggio e le comparse ritardate di «oggi» e della tacca.
2. Al più due movimenti per vista, e solo per mostrare l'effetto di un atto o di un calcolo.
3. Quando un atto è registrato a vista aperta, nell'ordine:
   - il sigillo si riempie di navy (200);
   - la spunta entra da scale(.6) a 1 (160);
   - la tratta va al nuovo `scaleX` (320);
   - parte l'avviso.

   È l'unica «celebrazione» della piattaforma, ed è causa ed effetto.
4. Lente premuta: i punti non evidenziati passano allo stato attenuato in 200, senza spostarsi; la tabella si filtra subito.
5. Tempi di entrata e uscita:
   - suggerimento: opacity, 120 in entrata e 80 in uscita;
   - avviso: translateY(8px → 0) e opacity in 200, uscita in 120;
   - dialogo: opacity e scale(.98 → 1) in 200, uscita in 120; lo sfondo segue gli stessi tempi;
   - details: il contenuto entra con opacity e translateY(4px → 0) in 200, senza animare l'altezza.
6. Al passaggio cambiano solo fondo e bordo, in 120. Nessun `translateY` su bottoni e righe: va tolto il −1 px di oggi.
7. Nessun movimento continuo: niente luccichio nei segnaposto, niente pulsazione sul sigillo atteso, niente spinner infiniti. Per i lavori lunghi basta il testo al gerundio con `aria-busy`.
8. **Rimandato [PP]:** lo scivolamento dei punti dopo un ricalcolo, il punto fantasma e il filo dalla vecchia posizione non si costruiscono finché l'API non restituisce il calcolo precedente. Fino ad allora i punti saltano alla nuova posizione.

**`prefers-reduced-motion: reduce`:**
- resta, senza eccezioni, la regola globale di `stile.css` (transition e animation a none);
- gli stati finali compaiono subito;
- `scrollIntoView` usa `behavior: 'auto'`;
- gli avvisi compaiono fermi e durano comunque 5 s.

Skill: `motion-meaning`, `excessive-motion`, `exit-faster-than-enter`, `animation-optional`, `duration-timing`, `transform-performance`. Il `--design-system` proponeva uno «Scroll Reveal subtle» (GSAP ScrollTrigger): scartato, nell'app e sul sito. In riunione e in stampa il contenuto deve essere leggibile subito.

---

## 7. Icone

**Regole**
1. Una sola famiglia: le icone a tratto di `Icona.tsx`, su griglia 24 con tratto 1,8 ed estremi tondi, sul modello di Phosphor regular (prima scelta della skill). Nessuna libreria aggiunta.
2. Grandezze: 20 nel menu e nei bottoni, 24 nella barra delle sezioni e negli stati vuoti, 16 nel testo, nei badge e negli avvisi.
3. Un'icona sta sempre accanto a un testo che dice la stessa cosa ed è `aria-hidden`. Uniche icone sole: «Esci» sulla barra del telefono e «Chiudi», a 44×44, con `aria-label` e suggerimento.
4. Mai icone nei KPI, nei titoli, negli inviti o come ornamento; mai glifi di testo usati come icone («7», «80%», «2/4», «%», «IA», «θ»); mai emoji.
5. `currentColor`; le icone di stato prendono l'inchiostro del loro stato.
6. I segni dei dati (sezione 8) non sono icone e non stanno in `Icona.tsx`: hanno un loro componente, `Segno`.

**Mappatura** (fra parentesi l'esito della ricerca nella skill, dominio icons)

| Concetto | Icona | Note |
|---|---|---|
| Panoramica | griglia 2×2 (grid-four) | sono i quadranti |
| Indirizzi | bussola (compass) | la direzione |
| Revisione | riquadro con spunta | — |
| Lotti | strati (nessun risultato: disegno nostro) | — |
| Documenti, mansionari | foglio con righe (file-text) | — |
| Persone e ruoli | persone (users) | — |
| Aggiungi una persona | user-plus (trovato) | — |
| Questionari d3/d4 | busta (envelope) | viaggiano per email |
| Parametri e soglie | cursori | scartato gear («Settings»): un parametro approvato dal comitato non è un'impostazione |
| Registro | libro (già in `Icona.tsx`; nessun risultato per «audit log history») | — |
| Organizzazioni (console) | edificio (nessun risultato per «building office company»: disegno nostro) | — |
| Lavori (console) | orologio (clock, trovato) | — |
| Credenziali, password | chiave (key, trovato) | — |
| Mostra la password | occhio (eye, trovato) / occhio barrato | sempre insieme al testo «Mostra» / «Nascondi» |
| Esci | sign-out | — |
| Cambia organizzazione, riga che apre | freccetta a destra (nessun risultato per «caret chevron»: disegno nostro) | — |
| Carica | upload-simple (trovato) | — |
| Scarica il report di audit | download-simple | — |
| Task precedente / successivo | arrow-left / arrow-right | — |
| Chiudi | × (disegno nostro) | — |
| Errore, non superato | warning-circle | — |
| Avviso | warning | — |
| Nota, provvisoria | info (trovato) | — |
| Successo, superato, registrato | check-circle (trovato: «success verified approved») | — |
| Permesso | lock (trovato) | — |
| In coda, in lavorazione | orologio | — |
| Guarda il video | play (trovato) | — |
| Protezione dei dati | scudo | **solo sul sito**, garanzia «I vostri documenti restano in UE»: nella skill lo scudo è Security |

Da togliere da `Icona.tsx`:
- `bersaglio`: diceva che l'automazione è l'obiettivo;
- `freccia` diagonale: indica un link esterno, era lo pseudo-bottone dei KPI.

---

## 8. Vocabolario dei dati (i segni)

Componente `Segno`, SVG da 12 (16 nella legenda, 10 nei badge), identico ovunque: mappa, legenda, KPI, badge, tabelle, sito.

| Segno | Disegno | Significato | Testo |
|---|---|---|---|
| Punto pieno | cerchio emerald-ink, contorno bianco 1,5 | almeno una delle 8 voci del task giudicata da persone | «Giudizio di persona» |
| Cerchio vuoto | fondo bianco, tratto amber-ink 2 | tutte le voci sono stime del modello | «Stima del modello» |
| Mezzo cerchio | metà sinistra cobalt, tratto cobalt 2 | derivato per somiglianza (quando l'API espone l'origine) | «Derivato per somiglianza» |
| Quadrato | quadrato cobalt pieno | task nuovo nel dataset (solo badge e tabelle) | «Nuovo» |
| Anello tratteggiato | navy 1,5, tratteggio 3 2,5 | incerto: il quadrante più probabile resta sotto la soglia di stabilità | «Incerto» |
| Sigillo posto | cerchio navy con spunta bianca | atto registrato | «fatto», «registrato» |
| Sigillo atteso | bianco, anello 2 teal-ink, lettera o punto teal-ink | atto che si aspetta adesso | «atteso: comitato guida» |
| Sigillo vuoto | bianco, anello 2 `--bordo-controllo` | atto futuro | «poi: auditor» |

- Sulla mappa la provenienza ha un ordine: pieno se c'è almeno una voce di persona; altrimenti mezzo cerchio se derivato; altrimenti vuoto.
- Il numero di voci giudicate non si disegna: sta nel suggerimento e nella tabella.

---

## 9. Nomi delle voci della rubrica

La fonte è la rubrica in vigore (`src/neartech/dati/rubrica-bozza-3.json`, già esposta dall'API di revisione come `rubrica.voci[].nome`) e, per d3 e d4, il questionario degli indirizzi (`VOCI` in `Indirizzi.tsx`).
- Un modulo condiviso `voci.ts` riunisce le due fonti, leggendo prima l'API.
- I codici k1…d4 non compaiono mai come testo da soli: solo dentro il `title`, oppure in Codice **accanto** al nome nella Revisione.
- Il maiuscolo dei codici è unico: «k1» (sparisce «K1 · ASSE N»).

| Codice | Asse | Nome (dalla rubrica) | Che cosa misura: proposta di `descrizione` per la prossima versione della rubrica, da approvare | Come si raccoglie |
|---|---|---|---|---|
| k1 | N | **Variabilità dell'input** | Quanto è strutturato e prevedibile ciò che arriva al task. | giudizio del revisore |
| k2 | N | **Giudizio** | Quanto il task chiede di decidere oltre le regole scritte. | giudizio del revisore |
| k3 | N | **Componente fisico-percettiva** | Quanto il task richiede di agire o percepire nel mondo fisico. | giudizio del revisore |
| r | N | **Affidabilità richiesta** | Quanto costa un errore e quanto è correggibile. | giudizio del revisore |
| d1 | D | **Relazione e fiducia** | Quanto conta il rapporto fra persone. | giudizio del revisore |
| d2 | D | **Responsabilità** | Quanto il task incide su diritti, doveri o atti riservati. | giudizio del revisore |
| d3 | D | **Senso del lavoro** | Quanto il task dà senso al lavoro di chi lo svolge. | questionario a chi lavora |
| d4 | D | **Valore per chi riceve il servizio** | Quanto conta, per chi riceve il servizio, che lo svolga una persona. | questionario a chi riceve il servizio |

Nota per il responsabile: il brief proponeva «conoscenza/know-how, giudizio, relazione/interazione, responsabilità/rischio» per k1, k2, k3 e r. **Non corrispondono alla rubrica `bozza-3`** e non vanno usati: k1 è «Variabilità dell'input», k3 «Componente fisico-percettiva», r «Affidabilità richiesta», mentre «Relazione» e «Responsabilità» sono d1 e d2. Le descrizioni sono testi d'interfaccia proposti. Vanno nella rubrica versionata, così restano un parametro e non una tabella del frontend.

---

## 10. Componenti

Ogni componente prevede questi stati: caricamento, vuoto, errore, parziale, successo e permesso. Le regole comuni sono in 10.17; qui sotto, per ciascuno, solo ciò che è specifico.

### 10.1 Guscio · menu laterale (≥ 1024)

**Struttura:** `<aside class="menu">` con logo, organizzazione, `<nav aria-label="Sezioni">` e piede.
- CSS: `width 240; height 100dvh; position sticky; top 0; display grid; grid-template-rows: auto auto minmax(0,1fr) auto; padding 24 16 0`; fondo bianco, bordo destro 1 px.
- **Un solo asse, a x = 28** (padding 16 + 12), per il segno del logo, il nome dell'organizzazione, le icone delle voci, l'avatar e l'icona di «Esci». Le etichette delle voci stanno a x = 60 (icona 20 + 12).

**Logo:** alto 32, padding-inline 12, `Logo` chiaro da 28. Invariato.

**Organizzazione:**
- 24 sotto il logo, padding-inline 12, nessun riquadro.
- Nome in Corpo 600 navy; sotto, in Piccolo, «Pilota in sperimentazione».
- Con più organizzazioni diventa un link a `/app` alto 44, con freccetta: `aria-label="Cambia organizzazione, ora ACME S.p.A."`.
- Il nome dell'organizzazione compare **solo qui**: spariscono l'eyebrow «ACME S.P.A. · COMITATO GUIDA» e il ripetuto nel piede.

**Navigazione:**
- 24 sotto l'organizzazione, `overflow-y: auto; overscroll-behavior: contain; scroll-padding-block: 8`.
- Un solo gruppo, senza etichette di gruppo; oltre 7 voci, un filetto separa le sezioni di consultazione.
- Le voci compaiono solo quando la sezione esiste: nessuna «In arrivo».
- Voce: alta 44, padding 0 12, gap 12, raggio 999, icona 20, Corpo `--testo-2`. Passo 48.
  - Al passaggio: fondo tela, testo navy.
  - Attiva: fondo navy, testo bianco Corpo 600, `--ombra-comando`, `aria-current="page"`.
- Contatore facoltativo (Revisione 26, Lotti 2, Indirizzi 1):
  - min 24×24, padding 0 8, raggio 999, Piccolo 600;
  - fondo tela e testo navy; nella voce attiva fondo #324874 e testo bianco;
  - `aria-label` sulla voce: «Revisione, 26 task da valutare».

**Piede:**
- `position: sticky; bottom: 0`, fondo bianco, filetto alto, padding 12 12 16.
- Riga 1: avatar 32 (cerchio tela, iniziale in Piccolo 600 navy); ruolo in Corpo 600 navy; soggetto in Codice `--testo-2`, con ellissi e `title`.
- Riga 2, 8 sotto: bottone testuale «Esci da Neartech» [TS], alto 44, padding-inline 12, icona sign-out 20 sull'asse x = 28, testo `--testo-2`; al passaggio risk-ink. Oggi Esci misura 36×36.
- Quando l'elenco trabocca, il piede riceve `--ombra-scorrimento` [TS][PP]. Lo rileva una sentinella alla fine dell'elenco, osservata con IntersectionObserver.

**Altezze:**
- con 4 voci servono 464 px (24 + 32 + 24 + 44 + 24 + 4×48 + 124);
- «Esci» si vede da 464 px di altezza in su per comitato, revisore, auditor e amministratore;
- sotto 464, scorre solo l'elenco.

**Telefono e tablet (< 1024):**
- `.app { grid-template-columns: 1fr; grid-template-rows: auto 1fr; min-height: 100dvh }`. Sparisce la riga che si gonfiava fino a 272 px.
- Barra alta, 56 px, statica:
  - segno del logo 24 a x = 16;
  - nome dell'organizzazione in Corpo 600, con ellissi; è un link a `/app` se le organizzazioni sono più di una;
  - a destra «Esci» come icona 44×44, con `aria-label="Esci"` e suggerimento.
- Barra delle sezioni [TS], fissa in basso:
  - alta 64 + `env(safe-area-inset-bottom)`, bianca, filetto alto, `--ombra-scorrimento`;
  - al massimo 4 posti di pari larghezza, centrati in al massimo 560 px (`bottom-nav-limit`, `adaptive-navigation`);
  - con più di 4 sezioni: 3 posti e «Altro», che apre un foglio dal basso con le altre sezioni come righe da 56.
- Posto della barra: indicatore a pillola 56×32 con l'icona 24; sotto, l'etichetta in Piccolo (14).
  - Attivo: pillola navy, icona bianca, etichetta navy 600, `aria-current="page"`.
  - Così la voce attiva è sempre visibile.

**Stati:**
- caricamento: il guscio compare subito, con le voci note dal registro delle rotte;
- permesso: le voci dei ruoli non propri non esistono.

### 10.2 Intestazione di pagina

`<header class="testa-pagina">`: griglia `1fr auto`, `align-items: end`, gap 16, margin-bottom 24.
- A sinistra l'h1 in Pagina e, 4 sotto, una riga in Piccolo (al massimo 72ch) con i fatti e, se la pagina mostra un calcolo, le sue chiavi.
- A destra al massimo un comando secondario, allineato alla prima riga.
- Niente eyebrow, niente «Torna alla mappa» (duplica Panoramica e sul telefono costava 60 px).
- Nelle home l'intestazione è il percorso (10.3).
- Titolo del documento: «{Sezione} · {Organizzazione} · Neartech».

### 10.3 Percorso del pilota: tracciato compatto con linguetta

**Markup**
```html
<section class="superficie percorso" aria-labelledby="titolo-percorso">
  <div class="percorso-riga">                        <!-- grid: max-content minmax(0,1fr); column-gap 32 -->
    <header class="percorso-testa">
      <h1 id="titolo-percorso">Fase 2 di 4 · Indirizzi</h1>
      <p>Percorso del pilota</p>
    </header>
    <ol class="tracciato">                            <!-- 4 colonne minmax(0,1fr); subgrid a 3 righe: 24 / auto / auto -->
      <li class="tratta tratta-fatta">…</li>
      <li class="tratta tratta-corrente" aria-current="step">
        <button class="tratta-comando" aria-expanded="false" aria-controls="prove-indirizzi">
          <span class="tratta-linea" aria-hidden="true"><i></i></span>
          <span class="sigilli" aria-hidden="true">…C · A…</span>
          <span class="tratta-nome">Indirizzi</span>
          <span class="tratta-stato">in corso</span>
          <span class="visually-hidden">Fase 2 di 4, Indirizzi: in corso. 0 di 3 atti. Atteso il comitato guida, poi l'auditor.</span>
        </button>
        <div id="prove-indirizzi" class="tratta-prove" hidden>…</div>
      </li>
      …
    </ol>
  </div>
  <div class="banda" role="group" aria-labelledby="titolo-azione">…</div>
</section>
```

**Testata** (colonna sinistra):
- h1 in Pagina, `white-space: nowrap`; sotto, in Piccolo, «Percorso del pilota».
- A percorso concluso: h1 «Percorso concluso».
- Spariscono l'h2 da 11 px, il «fase 2 di 4» in mono grigio in alto a destra e il segnaposto «oggi».

**Tratta** (colonna destra; ogni tratta è un `button` che apre le sue prove):
- Riga 1, alta 24: linea alta 4 con raggio 999.
  - Fatta: navy.
  - In corso: binario con riempimento teal-ink in `scaleX(progresso)`, con le formule di `progressoFase`, invariate.
  - In anticipo: binario con tratteggio obliquo, `repeating-linear-gradient(135deg, #007272 0 3px, transparent 3px 6px)`. Cambia la forma, non l'opacità: l'opacità .45 di oggi vale 1,90:1.
  - Da fare: niente binario, `border-top: 2px dashed var(--bordo-controllo)`.
  - Sigilli da 24 al confine destro, come in sezione 8; i due degli Indirizzi si sovrappongono di 4.
- Riga 2, 8 sotto: nome in Corpo 600; navy se corrente, `--testo` per le altre fasi.
- Riga 3: stato in Piccolo `--testo-2`: «fatta», «in corso», «in anticipo», «da fare». Nessun chip. Spariscono le tinte #EEF2F9, #E6FAFA e #FEF3C7 sulle fasi.
- Padding-right 24 per i sigilli. Al passaggio, fondo tela con raggio 12. Focus con anello.
- **Linguetta della fase corrente:**
  - è uno pseudo-elemento: `inset: 28px −12px −17px −12px`, fondo `--tela`, bordo 1 px `--bordo-superficie` senza lato basso, raggio 12 12 0 0;
  - scende fino alla banda e copre, per la sua larghezza, il filetto della banda;
  - fase e azione si leggono come una cosa sola, senza calcoli di posizione. Sostituisce la tacca, che le giurie hanno giudicato fragile.

**Prove della fase** (strato sospeso bianco, raggio 12, padding 16, al massimo 320 di larghezza, z 30):
- h3 in Corpo 600, «Indirizzi · in corso»;
- prova in Corpo, da `provaFase`;
- atti in Piccolo con i sigilli da 12, da `sigilloFase`: «Comitato guida: atteso · Auditor: dopo il comitato»;
- «Attende: il comitato guida», da `chiAgisce`.

È un comando che apre e chiude un contenuto, senza essere un dialogo: Esc o un clic fuori lo chiude e il focus resta sulla tratta.

**Banda dell'azione** (incasso vuoto, «A1 incassata»):
- `margin: 16px −24px 0; padding: 12px 24px`, fondo tela, filetto alto, raggio 0 0 20 20.
- Griglia `minmax(0, 72ch) auto; justify-content: start; column-gap: 32; align-items: center`.
- Colonna del testo, un livello per riga:
  - h2 in Titolo navy che comincia sempre con **chi agisce**: «<span class="chi">Tocca a voi:</span> date gli indirizzi». Il prefisso è teal-ink se tocca a chi guarda, `--testo-2` se si attende qualcun altro.
  - sotto, a 4, un paragrafo in Corpo `--testo-2`: una frase di al massimo 88 caratteri, su una sola riga a ≥ 760.
- Comando: primario a 32 px dal testo, centrato sul blocco di 52 px (scarto di 4). Nessuna ombra nera.

Varianti della banda:
- **attesa:** nessun bottone;
- **concluso:** «Percorso concluso: restituzione approvata» · «Atto #93 nel registro, 20 ottobre 2026.»;
- **errore del ricalcolo:** il paragrafo diventa un messaggio con `role="alert"` e icona warning-circle risk-ink, «Ricalcolo non riuscito. Riprova tra qualche istante.», e il comando diventa il secondario «Riprova»;
- **schermata non pronta:** al posto del bottone, in Piccolo, icona orologio e «Schermata in preparazione».

Sotto i 760 di contenitore:
- testata sopra il tracciato;
- banda a una colonna, con il comando sotto il testo, a 12.

Sotto i 520:
- `margin: 16px −16px 0; padding: 16px`;
- bottone al 100%, alto 48;
- le prove di tutte le fasi in un `<details>` sotto la banda, con summary alto 44: «Le prove di tutte le fasi».

**Testi esatti della banda** (titolo · testo · comando)

| Ruolo e situazione | Titolo | Testo | Comando |
|---|---|---|---|
| Comitato · indirizzi senza proposta | Tocca a voi: date gli indirizzi | Otto domande sulla vostra visione dell'innovazione calibrano i pesi di D. | Apri il questionario |
| Comitato · proposta da approvare | Tocca a voi: approvate il profilo di pesi | Prima di approvarlo guardate quanti task cambiano quadrante. | Apri il profilo proposto |
| Comitato · approvato, manca l'auditor | In attesa dell'auditor: verifica del profilo di pesi | Il profilo diventa attivo con il suo ok. | — |
| Comitato · verifica dei revisori | In attesa dei revisori: 7 risultati da confermare | Ogni loro giudizio sostituisce una stima del modello. | — |
| Comitato · esito | Tocca a voi: approvate la restituzione | La mappa è pronta: approvatela come atto del comitato. | Approva la restituzione (apre il dialogo) |
| Revisore · avvio con lotti | Tocca a te: decidi i lotti di abbinamento | 12 task aspettano la tua decisione, dal più ambiguo. | Apri i lotti |
| Revisore · verifica | Tocca a te: controlla le classificazioni a campione | 7 risultati da confermare, dal più incerto. | Apri la coda |
| Auditor · profilo da verificare | Tocca a te: verifica il profilo di pesi del comitato | Controlla limiti ed effetto sui task, poi dai l'ok. | Apri il profilo |
| Amministratore · avvio | Tocca a te: avvia la scomposizione dei mansionari | 6 mansionari caricati: la stima dei costi viene prima della conferma. | Apri i documenti |
| Amministratore · profilo da applicare | Tocca a te: ricalcola la mappa | Comitato e auditor hanno attivato un nuovo profilo di pesi. | Ricalcola la mappa → «Ricalcolo la mappa…» |
| Rappresentante · variazioni | Tocca a te: guarda le variazioni di D | 4 task cambiano D per gli indirizzi del comitato. | Apri le variazioni |
| Qualsiasi ruolo senza azione | In attesa del {chi}: {fase} | testo di `azioni.ts` | — |

La seconda frase della banda di oggi («Finché mancano…») passa alla nota della mappa.

### 10.4 KPI come lenti [TS]

**Markup:** `<section aria-labelledby="titolo-numeri">`, con un h2 visibile solo ai lettori di schermo («La mappa in tre numeri»), poi `<div class="lenti" role="group" aria-label="Evidenzia sulla mappa">` con tre `<button class="lente" aria-pressed="false">`.
- Una sola lente attiva alla volta; premuta di nuovo, si spegne.

**Lente:**
- superficie premibile: raggio 20, padding 16 24, altezza minima 96, `--ombra-superficie`; al passaggio bordo `--bordo-controllo` e `--ombra-riga-alta`;
- riga 1 in flex sulla linea di base, gap 12: valore in Numero navy tabellare, poi il segno da 12 della categoria e l'etichetta in Corpo `--testo`;
- riga 2, a 4: nota in Piccolo, al massimo due righe;
- nessuna icona, nessuna freccia, sparisce `.kpi-testa`.

| Lente | Valore · etichetta | Nota | Evidenzia |
|---|---|---|---|
| 1 | {da_confermare} · ◌ risultati da confermare | Il quadrante più probabile resta sotto l'80% delle simulazioni. | punti con l'anello «incerto» |
| 2 | {stabili} su {n} · risultati solidi | Superano la soglia di stabilità. | punti senza anello |
| 3 | {quota} su 100 · ● giudizi dalle vostre persone (agli altri ruoli: «dalle persone dell'organizzazione») | Gli altri sono stime del modello. | punti pieni |

**Pieno:**
- è pieno, in navy, il KPI di ciò che aspetta chi guarda: la lente 1 per comitato e revisore. Valore ed etichetta bianchi, l'etichetta a 600, nota #CBD5E1, segno bianco;
- per auditor e amministratore nessuna lente è piena, e nessuna quando il valore è 0.

**Premuta:**
- bordo 2 px navy; sulla lente piena, anello interno bianco di 2 px;
- la nota diventa «Evidenziati sulla mappa. Premi di nuovo per vederli tutti.»;
- sotto la legenda, una riga in Piccolo con `aria-live="polite"`: «Sulla mappa: 7 risultati da confermare. La tabella mostra solo questi.»

**Stati:**
- senza soglia di stabilità approvata: lenti 1 e 2 con «—» e «Serve la soglia di stabilità del comitato.», piatte e senza azione (non sono `button`);
- valore 0: la lente non si preme («Nessun risultato da confermare»);
- caricamento: segnaposto 3 × 96.

**Disposizione:**
- colonna di 4: in pila, gap 16;
- fra 1024 e 1279: in riga, s4 ciascuna;
- sul telefono: in pila, a tutta larghezza.

### 10.5 Mappa dei quadranti

Specifica completa nella sezione 11.

### 10.6 Sperimentazione: giudizi di persona, voce per voce

- Superficie nella colonna destra.
- h2 «Giudizi di persona, voce per voce»; sotto, in Piccolo: «Ogni giudizio dei revisori e ogni risposta ai questionari sostituisce una stima del modello al ricalcolo.»
- Due gruppi, ciascuno con un h3 in Piccolo 600: «Necessità (N)» con k1, k2, k3, r e «Desiderabilità (D)» con d1–d4.
- Riga: griglia «nome valore / barra barra», alta 44.
  - Nome in Corpo, può andare a capo.
  - Valore in Piccolo tabellare a destra, «12 di 27».
  - Barra alta 8, raggio 999, binario #E4E9F1, riempimento emerald-ink pari a persone/totale.
  - **Lo zero è solo il binario**: sparisce il 6% ambra.
  - Per i lettori di schermo il valore è «12 di 27 task con giudizi di persona».
- Nota in fondo al gruppo D: «Senso del lavoro e valore per chi riceve il servizio si raccolgono con i questionari via email.»
- Spariscono la ciambella, le barre verticali da 36, «Come si aggiorna» e la riga «Ancora senza giudizi di persona: k1, k3…».
- Stati: caricamento con 8 righe di segnaposto; con 0 su 100, sotto il titolo, «Per ora tutti i giudizi sono stime del modello.»

### 10.7 «Che cosa rende la mappa più solida» (gli inviti di oggi)

- Superficie sotto la mappa, larga 8 colonne. Righe piane: filetto, padding 12 0, nessuna ombra, nessun glifo.
- Per ogni riga:
  - titolo in Corpo 600 con il dato;
  - testo in Piccolo, al massimo 64ch;
  - a destra, in Piccolo, «Decide: il comitato guida».
- Una riga diventa un link in rilievo, con freccetta, solo quando esiste la schermata e chi guarda può agire.
- L'invito sui risultati da confermare esce, perché lo dice la lente 1.
- Se non c'è nessun avviso, la superficie non compare.
- I testi sono all'imperativo per il comitato, all'indicativo per gli altri ruoli (stato «permesso»):

| Avviso | Comitato | Altri ruoli | Testo |
|---|---|---|---|
| Soglia non fissata | Fissate la soglia di stabilità | La soglia di stabilità non è ancora fissata | Senza soglia non si distinguono i risultati solidi da quelli da confermare. |
| Soglia NEARTECH in vigore | Fate vostra la soglia di stabilità | Vale la soglia proposta da NEARTECH | Oggi vale l'80% proposto da NEARTECH. Il comitato può adottarlo o fissarne uno proprio. |
| D provvisorio | D si basa su 2 componenti su 4 | uguale | Mancano senso del lavoro e valore per chi riceve il servizio: si raccolgono con un questionario via email a operatori e utenti. |
| Pesi uguali | Indicate il tempo di ogni task | Ogni task pesa uguale nel suo ruolo | Comitato: «Il baricentro dei ruoli diventa preciso quando indicate quanto tempo occupa ciascun task.» Altri ruoli: «… quando il comitato indica le quote di tempo.» |
| Capacità dell'IA | Capacità dell'IA: stima documentale | uguale | Ogni valore ha fonte e data. Diventa una misura con i test sul campo. Decide NEARTECH. |

### 10.8 Tabelle

- Dentro una superficie.
- `th`:
  - Piccolo 600 `--testo-2`, maiuscola solo iniziale, padding 12 16, filetto basso, sticky dentro il contenitore che scorre;
  - se la colonna si ordina, il `th` contiene un `button` con freccia da 12 e `aria-sort` [PP] (`sortable-table`).
- `td`: Corpo, padding 12 16 (riga da 48), filetto. La prima e l'ultima cella hanno padding-inline 0, così il testo sta sull'asse del titolo.
- Numeri a destra, tabellari, in formato it-IT.
- Passaggio evidenziato solo se la riga si apre.
- Contenitore `overflow-x: auto` con ombre di scorrimento sui bordi (`background-attachment: local`). Sotto i 768, e solo se la tabella scorre davvero, una riga in Piccolo «Scorri per vedere tutte le colonne».

**Ruoli:** Ruolo · Task · N medio · D medio · Q1 · Q2 · Q3 · Q4 · Solidità · Peso dei task.
- Al posto delle mini-barre, quattro colonne di numeri. Nell'intestazione, un campione 12×12 della tinta con bordo 1 px #64748B accanto alla sigla.
- Il massimo della riga in Corpo 600; lo zero è «–» in `--testo-2`.
- «Peso dei task» in testo semplice: «uguale» o «dalle quote di tempo».
- Sotto i 768 ogni ruolo è una riga piana:
  - nome in Corpo 600;
  - poi, in Piccolo, «6 task · N 0,62 · D 0,41»;
  - poi «Q1 2 · Q2 1 · Q3 2 · Q4 1 · solidità 85%».

**Task in tabella:** Task · Ruolo · Quadrante · Probabilità · N · D · Giudizi di persona («2 di 8 voci») · Incerto.
- Ordine predefinito: per quadrante, poi per probabilità crescente.

### 10.9 Righe

- **In rilievo** (si aprono):
  - padding 12 16, altezza minima 56, 8 fra una riga e l'altra;
  - nome in Corpo 600, sotto una riga in Piccolo; a destra un valore in Corpo 600 tabellare, oppure una freccetta da 16;
  - selezionata: fondo navy, testo bianco, secondario #CBD5E1, `--ombra-comando`, `aria-current="true"`;
  - completata: impressa, con spunta e «6 di 6 voci».
- **Piane:** filetto, nessuna ombra.

### 10.10 Badge

- Etichetta di stato che non si preme: alta 24, padding 0 8, raggio 6, Piccolo 600 `--testo`, gap 6, nowrap.
- Fondo tela sul bianco; sulla tela, fondo bianco con bordo 1 px.
- Il segno è il vocabolario della sezione 8.
- Stati di processo con icona da 16:
  - «da avviare»: cerchio vuoto;
  - «in coda», «in lavorazione»: orologio;
  - «scomposto», «applicato»: check-circle navy;
  - «non riuscito»: warning-circle, testo risk-ink.
- Lotti: «livello da scegliere», «campione da estrarre», «campione da giudicare», «precisione da calcolare», «da decidere», «deciso, da applicare», «in applicazione», «applicato».
- Mai un badge al posto di una frase: «mappa provvisoria», «uguali», «quote» e «superato» non sono badge.

### 10.11 Bottoni

- Tutti: alti 44 (48 sul telefono a tutta larghezza), raggio 999, Corpo 600, padding 0 20, gap 8, icona facoltativa da 20.
- **Primario:** navy, testo bianco, `--ombra-comando`; al passaggio cobalt, alla pressione navy-800. Uno per schermata.
- **Secondario:** bianco, bordo 1 px #64748B, testo navy, nessuna ombra; al passaggio fondo tela.
- **Testuale:** cobalt, padding 0 8, alto 44, sottolineato al passaggio.
- **Distruttivo** (solo nei dialoghi): fondo risk-ink, testo bianco.
- **Icona sola** (solo Esci sul telefono e Chiudi): 44×44, con `aria-label` e suggerimento.
- **Disabilitato:**
  - fondo #E4E9F1, testo #475569 (6,22), nessuna ombra, `cursor: not-allowed`;
  - sempre il motivo scritto accanto, in Piccolo, con `aria-describedby`: «Mancano 5 risposte su 8.»;
  - mai `opacity`.
- **In attesa:** verbo al gerundio presente («Registro l'atto…», «Ricalcolo la mappa…»), `aria-busy`, larghezza minima bloccata a quella iniziale.
- **Focus:** anello 2 px teal-ink con scarto 2; bianco sul navy.

### 10.12 Campi e moduli

- Etichetta sopra il campo, in Corpo 600, a 8; aiuto in Piccolo sotto, a 4; segnaposto solo come esempio («Es.: …»).
- Obbligatorietà dichiarata a testo: «(facoltativo)» sui pochi facoltativi.
- **Campo:** alto 44, padding 0 12, bordo 1 px #64748B, raggio 12, Corpo (16 sotto i 768); al passaggio bordo #475569.
- **Area di testo:** altezza minima 96, padding 12, ridimensionabile in verticale, contatore «12 di 4.000 caratteri».
- **Errore:**
  - bordo 2 px risk-ink;
  - sotto, icona warning-circle 16 e testo in Piccolo risk-ink;
  - `aria-invalid` e `aria-describedby`.
- **Dopo un invio fallito:** riepilogo in cima con `role="alert"` e `tabindex="-1"`, link a ogni campo, focus sul riepilogo («Focusable Error Summary»). Gli errori accanto ai campi restano.
- **Password:**
  - `autocomplete` corretto (`username`, `current-password`, `new-password`);
  - incolla sempre permesso e gestori di password ammessi (`accessible-authentication`);
  - comando testuale «Mostra» / «Nascondi» con l'icona occhio, alto 44, dentro il campo a destra (`password-toggle`, `autofill-support`).
- **Domande del questionario:**
  - il `fieldset` non ha bordo; il separatore sta su un `<div class="domanda">` esterno (filetto alto, padding-top 16). Sparisce la linea a metà della legend, che oggi sembra un barrato;
  - la legend contiene una riga in Piccolo, «Domanda 1 di 8 · Relazione e fiducia», e poi la domanda in Titolo navy;
  - spazi: 8 dalla riga alla domanda, 12 dalla domanda alle opzioni, 32 fra le domande;
  - **pillole di risposta:** radio nativo, visivamente nascosto ma focalizzabile; etichetta a pillola alta 44 (oggi 39), padding 0 16, bordo #64748B, gap 8. Scelta: fondo navy, testo bianco 600, spunta 16. Focus con `:focus-within`.
- **Invio:**
  - il bottone non si disabilita per le risposte mancanti; accanto, in `aria-live`, «3 di 8 risposte»;
  - se il modulo è incompleto: riepilogo «Mancano 5 risposte: domande 4, 5, 6, 7, 8.», con i link alle domande.

### 10.13 Livelli della rubrica e stima del modello

- 5 colonne, gap 8. Card a raggio 12, bordo #64748B, padding 12, altezza minima 96.
- Livello «0»–«4» in Corpo 600 navy; descrizione in Piccolo.
- Scelto: bordo 2 px navy, fondo tela, spunta in alto a destra, `aria-pressed`. Sotto la voce, «Il tuo giudizio: 2 · registrato».
- **La stima del modello non marca un livello** (oggi `Math.round` fa di 2,5 un 3):
  - sopra la griglia corre un binario da 4 px, largo quanto la griglia;
  - un cerchio vuoto amber-ink da 12 sta in `x = (stima + 0,5) / 5 × larghezza`, cioè fra i centri dei livelli;
  - accanto, in Piccolo: «Stima del modello: 2,5, fra il livello 2 e il 3». Con una stima intera: «Stima del modello: 3».
- Sotto i 1024: livelli in pila come righe radio alte almeno 56; il binario diventa la sola frase.

### 10.14 Scheda di scenario (ascolto del comitato, momento 3)

Fonte: `fase-ascolto-comitato.md`.
- In testa «Scheda 3 di 14» con una barra teal-ink da 8 e la premessa in Corpo: «Supponete che nei prossimi due anni l'IA possa svolgere ciascuno di questi compiti con la stessa qualità e lo stesso costo di oggi.»
- Domanda in Titolo: «Quale terreste di più alle persone, e quale cedereste più volentieri all'IA?»
- Quattro righe, una per task:
  - nome in Corpo 600, ruolo in Piccolo e descrizione breve in Piccolo, al massimo 2 righe;
  - a destra due pillole radio da 44: «Terrei alle persone» (gruppo `piu`) e «Cederei all'IA» (gruppo `meno`);
  - scegliere lo stesso task in tutti e due i gruppi è impedito, e lo dice il testo «Scegliete due task diversi.»
- Mai i valori di d1–d4 nella scheda.
- «Avanti» primario; «Indietro» testuale.
- Sul telefono, le pillole vanno sotto ogni task.

### 10.15 Procedura a passi (onboarding e lotti)

Usa la grammatica del tracciato: passi come tratte, atti come sigilli.
- h1 «Passo 2 di 5 · Persone e ruoli» (`multi-step-progress`).
- Sotto, i passi come tracciato compatto senza linguetta.
- «Esci dalla procedura» testuale in alto a destra (`escape-routes`).
- Un passo che ha registrato un atto è fatto (sigillo posto), si riapre solo in lettura e non si annulla, perché il registro non si cancella.
- Ogni passo si salva quando si conferma.
- «Indietro» è sempre disponibile verso i passi senza atto.

### 10.16 Mini-grafici [PP]

- **Mini-mappa «Dove sta ora»** (Revisione):
  - 160×100, stessa geometria in piccolo: tessere, punto del task con anello ed ellisse, nessun testo;
  - `aria-hidden`, perché la riga di testo accanto dice quadrante e certezza.
- **Pendenza** (Rappresentante):
  - 120×32: due punti navy (D prima, D dopo) uniti da una linea navy 2, la scala D 0–1 implicita;
  - `aria-hidden`, perché accanto c'è la frase «D da 0,62 a 0,48, scende».

### 10.17 Stati del contenuto (regole per ogni componente)

| Stato | Regola | Testi |
|---|---|---|
| Caricamento | Il guscio compare subito. Dopo 300 ms, segnaposto statici (#E4E9F1 su bianco, raggio 6, nessun luccichio) all'altezza vera: percorso 192, lenti 3×96, mappa all'altezza calcolata. `aria-busy` sulla regione; CLS sotto 0,1 | «Carico la mappa…», «Carico la coda…», «Carico gli indirizzi…», «Carico i lotti…», «Carico i documenti…», «Verifico l'accesso…» |
| Vuoto | Dentro la superficie che conterrà i dati, allineato a sinistra: icona 24, titolo, Corpo al massimo 64ch con che cos'è lo spazio, come si riempie e chi lo riempie. Comando nello stesso blocco se il ruolo può agire, altrimenti «Chi agisce: …». Mai uno zero nel titolo | «La mappa si riempie dopo il primo calcolo» · «Servono i mansionari scomposti in task e abbinati al dataset NEARTECH. Chi agisce: l'amministratore NEARTECH.» |
| Errore | Messaggio dentro il componente: fondo tela, filetto 4 px risk-ink, icona warning-circle 20, titolo in Corpo 600, rimedio, secondario «Riprova»; `role="alert"`. Per 401, 403 e 409 restano i testi di `messaggioErrore` | «Non riesco a caricare la mappa» · «Controlla la connessione e riprova.» · 403: «Non hai un ruolo in questa organizzazione. Chiedilo all'amministratore NEARTECH.» + «Torna alle tue organizzazioni» [TS] |
| Parziale | Si mostra ciò che c'è e si dichiara ciò che manca: «—» con il motivo in Piccolo, mai 0 | «3 task non hanno ancora un risultato: sono in tabella, senza quadrante.» [PP] |
| Successo | L'esito resta dove l'atto si vede (sigillo posto, riga impressa, «registrato»), più un avviso temporaneo | vedi 10.18 |
| Permesso | Chi non può agire non vede comandi né bottoni spenti. Al loro posto lucchetto 16 e Piccolo | «Questa decisione spetta al comitato guida.» |

### 10.18 Avvisi temporanei

Servono solo a confermare un atto riuscito: mai per gli errori, mai come unico accesso a un comando.
- **Posizione:** in basso a destra a 24; sul telefono 16 sopra la barra delle sezioni.
- **Aspetto:**
  - larghezza min(400px, 100% − 32px), fondo #07193D, raggio 12, padding 12 16, `--ombra-sospesa`;
  - icona check-circle 20 #7EE0E0, testo bianco in Corpo;
  - Chiudi da 44 con `aria-label="Chiudi l'avviso"`.
- **Comportamento:**
  - `role="status"`, `aria-live="polite"`, non prende il focus;
  - si chiude dopo 5 s e si ferma al passaggio e al focus;
  - al massimo due impilati;
  - nessun «Annulla» [TS]: il registro non si cancella, e chi cambia idea aggiunge un giudizio.
- **Testi:**
  - «Atto registrato: approvazione della restituzione (#93).»
  - «Atto registrato: ok dell'auditor al profilo (#92).»
  - «Giudizio registrato: Variabilità dell'input, livello 3.»
  - «Mappa ricalcolata con il profilo del comitato.»
  - «Ruoli assegnati a Marta Rossi (#41).»

### 10.19 Dialoghi e pannello laterale

**Dialogo** (`<dialog>` modale):
- **Misure:** larghezza min(560px, 100% − 32px), padding 32 (24 sotto i 768), raggio 20, `--ombra-dialogo`.
- **Titolo:** h2 in Titolo, sempre come domanda: «Approvare la restituzione?». Sotto, in Piccolo: «Atto del comitato guida · resta nel registro».
- **Corpo:**
  - al massimo 64ch, con i fatti: «27 task in 6 ruoli · pesi del profilo approvato il 17 ottobre»;
  - campo «Motivazione dell'atto»;
  - impronta in Codice dentro «Chiavi del calcolo».
- **Comandi:** a destra, gap 12, margin-top 24: «Torna alla mappa» (secondario) e «Approva la restituzione» (primario). L'errore sta sopra i comandi, con `role="alert"`.
- **Focus:**
  - all'apertura va sul primo campo;
  - Esc chiude, ma non durante l'invio;
  - alla chiusura torna al comando d'origine (skill react: «Focus trap in modals, return focus on close»).
- **Telefono:** foglio dal basso, raggio 20 20 0 0, padding inferiore 24 + safe area, comandi impilati con il primario sopra, Chiudi 44 in alto a destra.

**Pannello laterale** (elenco dei task, modifica dei ruoli):
- 400 px da destra, a tutta altezza, raggio 20 0 0 20, `--ombra-sospesa`, z 40;
- intestazione con h2 e Chiudi; contenuto che scorre;
- sul telefono diventa un foglio a tutta altezza.

### 10.20 Video (sito)

- `<figure>` con `<video controls preload="none" playsinline poster="…">`. Mai autoplay né loop («Auto-Play Video»: click-to-play).
- **Aspetto:** raggio 20, bordo 1 px, `--ombra-superficie`, rapporto 16:9.
- **Avvio:** al centro un bottone da 64 (cerchio bianco, icona play navy 24), con `aria-label="Guarda il video: Neartech in 79 secondi"`. Il clic avvia il video e passa ai controlli nativi.
- **Focus del bottone:** `outline: 2px solid #fff` più `box-shadow: 0 0 0 4px var(--navy)`, visibile su qualsiasi fotogramma.
- **Didascalia** in Piccolo: «1 min 19 s · senza voce, con musica» (pitch) e «2 min 17 s · senza voce, con musica» (metodo). Durate lette dai file: 79,0 s e 136,5 s, 1920×1080.
- **Testo del video:**
  - `<details>` «Leggi il testo del video», con summary alto 44;
  - contiene, scena per scena, il testo a schermo di `storyboard-video.md`, sezioni 5 e 6, con le fonti dei numeri;
  - i video non hanno parlato, quindi il testo integrale è l'alternativa al contenuto visivo (WCAG 1.2.3) e non servono sottotitoli.
- **File:**
  - pubblicati in `/media/` del sito, non serviti da `docs/`;
  - poster con il fotogramma del titolo, in WebP 1280×720 (≤ 120 KB);
  - MP4 H.264 come oggi (16 e 21 MB), serviti con richieste per intervalli.

---

## 11. Mappa dei quadranti in dettaglio

### 11.1 Struttura

```html
<section class="superficie mappa-card" aria-labelledby="titolo-mappa">
  <h2 id="titolo-mappa">Dove stanno i 27 task · mappa provvisoria</h2>
  <div class="mappa-guida">                         <!-- flex, space-between, wrap; 12 sotto l'h2 -->
    <p class="asse-d" aria-hidden="true">↑ Desiderabilità (D)</p>
    <ul class="legenda" aria-label="Legenda dei segni">…</ul>
  </div>
  <p class="mappa-lente" aria-live="polite"></p>   <!-- vuota quando nessuna lente è premuta -->
  <div class="mappa" style="--divisione: 297px">     <!-- grid: 40px 1fr; righe 48 / H / 48 / 24 -->
    <div class="fascia fascia-alta">  <p class="etichetta-q q3">…</p><p class="etichetta-q q1">…</p></div>
    <svg role="group" aria-labelledby="titolo-mappa" aria-describedby="sommario-mappa">…</svg>
    <div class="fascia fascia-bassa"> <p class="etichetta-q q4">…</p><p class="etichetta-q q2">…</p></div>
    <div class="asse-n" aria-hidden="true">…</div>
    <div class="suggerimento" hidden>…</div>
  </div>
  <p id="sommario-mappa" class="visually-hidden">Q1 persona necessaria e desiderata: 6 task; …</p>
  <p class="mappa-nota">…</p>
  <p class="mappa-chiavi">…</p><details class="chiavi">…</details>
  <details class="mappa-tabella"><summary>Vedi i 27 task in tabella</summary>…</details>
</section>
```

- Titolo: «Dove stanno i {n} task · mappa provvisoria» [PP, nella forma ridotta proposta dalla seconda giuria: «provvisoria» nel titolo, numeri nelle fasce]. Con la restituzione approvata: «Dove stanno i {n} task · restituzione approvata».
- Niente numeri per quadrante nell'h2: stanno nelle fasce, che a ≥ 657 px di altezza sono tutte nella prima schermata (2.5). Niente «affidare all'IA» su una mappa provvisoria.

### 11.2 Geometria (px reali, `ResizeObserver` come oggi)

- `W` è la larghezza interna della card. Gronda di D: 40. Area dei dati: `Wd = W − 40`. Altezza `H` con la formula della 2.5.
- **Tessere nell'SVG:**
  - quattro rettangoli nelle tinte q1–q4, che vanno ai bordi dell'area dei dati;
  - separati da un canale bianco di 4 px centrato sulle soglie: `x(θN) ± 2`, `y(θD) ± 2`;
  - raggio 12 solo sugli angoli esterni bassi delle tessere basse; quelle alte proseguono nella fascia;
  - nessun filtro, ombra o contorno, e spariscono le linee di soglia tratteggiate.
- **Fasce HTML** [PP]:
  - colonna 2 della griglia, sopra e sotto l'SVG, alte almeno 48;
  - `grid-template-columns: calc(var(--divisione) − 2px) 4px 1fr`, dove `--divisione = x(θN) − 40` lo imposta il componente;
  - ogni cella ha la tinta del suo quadrante, raggio 12 sull'angolo esterno, e prosegue senza giunta nella tessera dell'SVG: fascia e tessera sono un'unica regione.
  - **I punti non possono finire sotto un'etichetta:** stanno nell'SVG, le etichette nelle fasce.
- **Scale:** soglie da `chiavi.soglie_quadranti`, mai dal codice. Respiro di 16 px su **entrambi** gli assi [PP]:
  - `x(v) = 40 + 16 + v × (Wd − 32)`;
  - `y(v) = H − 16 − v × (H − 32)`.

  Un punto a 0 o a 1, anello di raggio 11 compreso, resta intero dentro la sua tessera.
- **Gronda di D** (nell'SVG, x da 0 a 40):
  - valori in Piccolo `--testo-2`, allineati a destra a x = 32: «1» a y(1), «0,50» a y(θD), «0» a y(0);
  - tacche da 4 px #64748B fra x 36 e 40.
- **Riga dell'asse N** (24, colonna 2):
  - valori «0», «0,50», «1» in Piccolo alle loro x;
  - titolo «Necessità (N) →» in Piccolo, nella più ampia delle due distanze fra le tacche, così non si sovrappone mai al valore della soglia.
- **Titolo dell'asse D:** «↑ Desiderabilità (D)», orizzontale, a sinistra della riga guida, sopra la gronda. Mai ruotato.
- I nomi completi («necessità di una persona», «desiderabilità del contributo della persona») stanno nella tabella e nel suggerimento.

### 11.3 Etichette e conteggi dei quadranti (lo spazio del conteggio)

| Cella | Angolo | Allineamento | Riga 1 (Piccolo 600 navy) | Riga 2 (Titolo navy) |
|---|---|---|---|---|
| alta sinistra | Q3 | sinistra | Q3 · Scelta di valore | 7 task |
| alta destra | Q1 | destra | Q1 · Persona necessaria e desiderata | 6 task |
| bassa sinistra | Q4 | sinistra | Q4 · Automazione possibile | 10 task |
| bassa destra | Q2 | destra | Q2 · Necessaria, poco desiderata | 4 task |

- Padding della cella: 4 12 0 in alto, 4 12 0 in basso. Forme: «1 task», «nessun task».
- Il testo è vero: va a capo e non si tronca mai; la fascia cresce con la riga più alta delle due celle.
- Cella sotto i 120 px: solo «Q2 · 4»; i nomi completi vanno in un elenco in Piccolo sotto il disegno.
- Il conteggio non è `aria-hidden`. Il sommario nascosto ripete i quattro conteggi.

### 11.4 Codifica dei punti

Due canali binari e un anello (`pattern-texture`, `color-not-only`).

| Strato (in ordine di disegno) | Disegno |
|---|---|
| 1. ellisse del punto attivo | una deviazione standard **con unità separate** [PP]: `rx = n_dev × (x(1) − x(0))`, `ry = d_dev × (y(0) − y(1))`, minimo 4; riempimento cobalt al 12%, bordo cobalt al 40%. Corregge `MappaQuadranti.tsx:106`, che usa la stessa unità per tutti e due gli assi |
| 2. anelli «incerto» | r 11, navy 1,5, tratteggio 3 2,5; solo se `instabile === true` |
| 3. stime e derivati | r 6: cerchio vuoto (bianco, tratto amber-ink 2) oppure mezzo cerchio cobalt |
| 4. giudizi di persona | r 6 emerald-ink pieno, contorno bianco 1,5 |
| 5. punto attivo o con il focus | r 8, più un anello pieno navy di 2 px a r 12 |

- Sparisce l'opacità a otto gradini (0,25 + 0,75 · voci/8).
- **Punti coincidenti** [PP]: si raggruppano i centri a meno di 10 px. Il gruppo si dispone su un cerchio di raggio 7 attorno al baricentro, a partire da −90°, in ordine di `occorrenza_id`. Dal settimo punto in poi si usa un secondo giro a raggio 14. Lo spostamento massimo è 14 px. I valori del suggerimento e della tabella restano esatti; nel suggerimento, «3 task nello stesso punto».
- **Lente attiva:** i punti che non corrispondono diventano r 3, senza riempimento né anello, con tratto #475569 1 (≥ 6,41:1, conforme a 1.4.11) [la seconda giuria, al posto dell'opacità .25]. I punti che corrispondono restano invariati.
- `pari === true`: il suggerimento aggiunge «Probabilità pari con un altro quadrante: vale l'ordine Q1, Q2, Q3, Q4.»

### 11.5 Legenda

`legend-visible`: sempre sopra il disegno, mai sotto la piega.
- È nella riga guida, a destra del titolo dell'asse D. Sotto i 600 px di card va a capo sotto di esso.
- Ogni voce: segno SVG 16×16 identico a quello del disegno, etichetta in Piccolo e conteggio in Piccolo 600 navy [PP]:
  - «● Giudizio di persona 3»
  - «○ Stima del modello 24»
  - «◐ Derivato per somiglianza 0», solo se maggiore di 0
  - «◌ Incerto 7»
- Criterio: pieni + vuoti + derivati = totale; incerti = KPI «da confermare» = righe con «incerto» in tabella.
- Senza soglia di stabilità (`instabile === null`): niente anelli, e la voce diventa «Stabilità da misurare: manca la soglia».

### 11.6 Interazione

- **Puntatore fine:** bersaglio invisibile r 12 per ogni punto. Al passaggio mostra il suggerimento; al clic lo fissa.
- **Tocco** sulle mappe di almeno 520 px [PP]:
  - si sceglie il punto più vicino entro 22 px (bersaglio equivalente a 44);
  - il dettaglio va in `.mappa-dettaglio`, sotto il disegno, con Chiudi da 44.
- **Tastiera** [TS], con roving tabindex della direzione vincente:
  - i punti sono un `<g role="list" aria-label="27 task">`, con un `<g role="listitem">` per punto;
  - un solo arresto di tabulazione: `tabindex="0"` sull'ultimo punto visitato, −1 sugli altri;
  - ←/→ portano al punto successivo in ordine di N, ↑/↓ in ordine di D (a parità vale l'altro asse); Home e Fine agli estremi di N;
  - Invio o Spazio fissano il suggerimento, Esc lo chiude;
  - il focus visibile è l'anello navy del punto attivo.
- `aria-label` di ogni punto: «Colloquio di selezione, Specialista risorse umane: Q1, persona necessaria e desiderata, probabilità 74%, incerto, 0 voci su 8 giudicate da persone, N 0,56, D 0,93.»
- **Suggerimento:**
  - livello sospeso #07193D, raggio 12, padding 12 16, al massimo 280 di larghezza;
  - sopra il punto; si ribalta sotto se in alto mancano 80 px; non esce mai dalla card;
  - righe:
    - task in Corpo 600 bianco;
    - ruolo in Piccolo #CBD5E1;
    - «Q1 · Persona necessaria e desiderata, nel 74% delle simulazioni»;
    - «N 0,56 · D 0,93»;
    - «Giudizi di persona: 0 di 8 voci», oppure «Solo stima del modello»;
    - se serve, «Incerto: sotto la soglia dell'80%»;
  - una regione nascosta `aria-live="polite"` legge la stessa frase.

### 11.7 Sotto il disegno

1. **Nota** in Piccolo con icona info 16, margin-top 12:
   - con i pesi di default: «Provvisoria: calcolata con i pesi di default NEARTECH. Cambia quando il comitato dà gli indirizzi.»
   - con il profilo proprio: «Provvisoria: calcolata con il vostro profilo di pesi. Diventa definitiva con l'approvazione della restituzione.»
   - approvata: «Approvata dal comitato guida il 20 ottobre 2026 · atto #93.»
2. **Chiavi** in Piccolo: «Pesi: default NEARTECH · rubrica in vigore · calcolo del 17 ottobre 2026, 14:20». Con `<details>` «Chiavi del calcolo», summary alto 44, che mostra in Codice profilo, istantanea della copertura, versione della rubrica e impronta (da `restituzione.chiavi`). Il codice tecnico non sta in vista [terza giuria].
3. **Tabella:** `<details>` «Vedi i 27 task in tabella» (con una lente: «Vedi i 7 task evidenziati in tabella»), summary alto 44 (oggi 36). È la tabella della 10.8, ordinabile.

### 11.8 Contenitore sotto i 520 px: matrice 2×2

La skill (chart, Scatter) sconsiglia la dispersione su mobile.
- Al posto del disegno, quattro `button` con `aria-expanded`, nella stessa disposizione (Q3 Q1 / Q4 Q2), gap 8, raggio 12, nella tinta del quadrante, padding 12, altezza minima 96.
- Dentro ogni bottone:
  - «Q3 · Scelta di valore» in Piccolo 600;
  - «7 task» in Titolo;
  - «2 incerti · 3 con giudizio di persona» in Piccolo.
- Un tocco apre sotto la matrice l'elenco dei task del quadrante, dal meno certo: righe piane con segno, task, ruolo e probabilità.
- Legenda e nota restano sopra e sotto.

### 11.9 Stati della mappa

| Stato | Resa |
|---|---|
| Caricamento | Area riservata all'altezza H. Tessere e fasce in #E4E9F1, senza punti né testi; «Carico la mappa…» per i lettori di schermo; `aria-busy` |
| Vuoto | Tessere in tela con, al centro, «La mappa si riempie dopo il primo calcolo» e chi agisce; per l'amministratore, «Apri i documenti» |
| Errore | Messaggio d'errore dentro la card, con «Riprova» |
| Parziale, risultati mancanti | Riga sotto la legenda: «3 task non hanno ancora un risultato: sono in tabella, senza quadrante.» |
| Parziale, senza soglie dei quadranti | Una sola tessera tela, niente fasce, punti visibili e la riga «Servono le soglie del profilo di pesi approvato per dividere i quadranti.» |
| Parziale, senza soglia di stabilità | Niente anelli; in legenda «Stabilità da misurare» |
| Provvisoria | «· mappa provvisoria» nell'h2 e la nota con l'icona info. Nessun badge |
| Approvata | «· restituzione approvata» nell'h2 e la nota con l'atto |

Skill (chart, «Correlation / Distribution»):
- marcatori di forma diversa con etichette di gruppo dirette;
- il colore rafforza ma non è l'unica distinzione;
- tabella visibile come alternativa;
- con la tastiera, il focus rivela i valori;
- «When NOT to use: mobile-primary», da cui la matrice;
- sotto i 500 punti, SVG.

Regole: `legend-visible`, `contrast-data`, `direct-labeling`, `tooltip-keyboard`, `touch-target-chart`, `responsive-chart`, `screen-reader-summary`, `data-table`, `sortable-table`.

---

## 12. Schermate per ruolo

`sN` = N colonne della griglia a 12.

### 12.1 Comitato guida · Panoramica (home)

**1440×900 e 1280×800:**
- Percorso s12 (y 24–216), con la banda dell'azione.
- Mappa s8 da y 240, con il disegno intero entro 741 (1440) o 694 (1280).
- Colonna s4 dalla stessa y: lenti (3 × 96, gap 16), poi a 24 «Giudizi di persona, voce per voce».
- Sotto la mappa, s8: «Che cosa rende la mappa più solida». Riempie il vuoto di circa 610 px; le due colonne finiscono entro 160 px l'una dall'altra.
- Ruoli s12.

**1024–1279:**
- Percorso s12, con la testata sopra il tracciato quando il contenitore è sotto i 760.
- Mappa s12.
- Lenti in riga, s4 ciascuna.
- Sperimentazione s6 e inviti s6.
- Ruoli s12.

**768–1023:** come sopra, con gutter 16 e barre del telefono.

**390×844:** barra alta 56, poi nell'ordine:
- percorso compatto (h1, quattro nomi con il loro stato, banda con bottone al 100% alto 48, «Le prove di tutte le fasi»);
- lenti in pila;
- matrice 2×2, legenda e nota;
- «Vedi i 27 task» come elenco;
- sperimentazione, inviti, ruoli come righe;
- barra delle sezioni.

**Esito:** «Approva la restituzione» sta nella banda e apre il dialogo (10.19).

### 12.2 Comitato guida · Indirizzi

- Intestazione: h1 «La vostra visione, tradotta in pesi»; sotto «Questionario approvato dal comitato di governance · 8 domande».
  - Spariscono «QUESTIONARIO DEGLI INDIRIZZI · BOZZA-1» e «Profilo {profile_id}». La versione va nelle chiavi.
  - Il profilo si chiama «Profilo dalle risposte del 17 ottobre 2026».
- s8: il questionario (10.12), con il primario «Calcola il profilo di pesi» in fondo.
- s4, sticky a 24: «Il profilo, passo per passo».
  - Quattro sigilli: Risposte del comitato · Approvazione del comitato · Verifica dell'auditor · Profilo attivo.
  - «3 di 8 risposte» con una barra teal-ink da 8.
  - «Nessun peso scende sotto 0,10 o sale sopra 0,45.»: i limiti vengono dal parametro, non dal codice.
- Sotto i 1024 il riepilogo diventa una barra fissa in basso, alta 72, sopra la barra delle sezioni, con «3 di 8 risposte» e il bottone.
- Con una proposta, profilo in s8 e decisione in s4:
  - quattro sigilli;
  - tabella Componente · In uso · Proposto · Variazione, con «+0,05 ▲» (sempre segno e testo);
  - «4» in Numero con «task su 27 cambiano quadrante» e le righe «Colloquio di selezione · Q3 → Q1»;
  - controlli automatici come righe piane con check-circle «superato» o warning-circle risk-ink «non superato»;
  - decisione: campo «Motivazione dell'atto» e il primario «Approva il profilo di pesi», che apre il dialogo «Approvare il profilo di pesi?».
- Quando arriverà la corsia di ascolto, il passo «Risposte del comitato» diventa i quattro momenti (Materiali · Interviste · Scenari · Restituzione) come procedura a passi (10.15), con la scheda di scenario (10.14).
- Revisore e amministratore la vedono in sola lettura, con la nota «Gli indirizzi li dà il comitato guida; l'ok spetta all'auditor.»

### 12.3 Revisore

- **Home** [TS]: decisa da `azione(ruolo, percorso)`.
  - Revisione, se la fase è la verifica e ci sono risultati da confermare.
  - Lotti, se la fase è l'avvio e ci sono task in attesa.
  - Altrimenti la Panoramica, con la banda «In attesa del …».
- **Revisione:**
  - Intestazione: h1 «26 task da valutare, dal meno certo»; sotto «Rubrica in vigore · 6 voci per task · i tuoi giudizi sostituiscono le stime del modello al ricalcolo».
  - Barra del task, s12, sticky in alto, z 20, bianca, alta 64:
    - a sinistra «Task 3 di 26» in Corpo 600 e «certezza 41% · 2 di 6 voci giudicate da te» in Piccolo;
    - a destra «Task precedente» e «Task successivo», secondari con frecce, ed «Elenco dei task», testuale;
    - l'elenco si apre nel pannello laterale (righe in rilievo, la corrente navy, le completate impresse, ricerca per nome);
    - sparisce la coda annidata con scorrimento proprio.
  - Card del task, s12:
    - in testa h2 con il nome del task e, in Piccolo, i ruoli e «Q2 nel 46% delle simulazioni · incerto»;
    - a destra la mini-mappa «Dove sta ora» [PP];
    - `<details>` «Aggiungi una nota per i prossimi giudizi».
  - Le sei voci, a 32 l'una dall'altra:
    - «Voce 1 di 6 · Necessità (N)», con k1 in Codice;
    - h3 in Corpo 600 navy («Variabilità dell'input»);
    - binario della stima e cinque livelli (10.13), a 1280 colonne da circa 179 px.
  - In fondo:
    - «6 di 6 voci giudicate»;
    - il primario «Passa al task successivo»;
    - in Piccolo, «Prossimo: Preparazione del budget annuale».
  - `scroll-padding-top: 80px`.
  - A 390:
    - barra non sticky;
    - precedente e successivo in fondo, a tutta larghezza;
    - livelli come righe da 56.
- **Lotti:**
  - h1 «Lotti di abbinamento».
  - Ogni lotto è una superficie con i cinque passi come procedura a passi (Livello · Campione · Giudizio alla cieca · Precisione · Decisione).
  - Il passo corrente:
    - livello in tre card a raggio 12;
    - coppie come righe con le pillole «Stesso task», «In parte», «Task diverso», alte 44;
    - precisione in Numero;
    - proposte da escludere come righe con casella.
  - Nomi leggibili:
    - «Lotto del 17 ottobre 2026 · 12 proposte», con l'id in Codice nella riga secondaria;
    - «Istruzioni di abbinamento, versione 1».
  - Numeri: «distanza 0,42 · margine 0,08».

### 12.4 Auditor

- **Home:** la Panoramica.
  - Banda «Tocca a te: verifica il profilo di pesi del comitato» solo quando il profilo è approvato e non ancora verificato; altrimenti «In attesa del comitato guida: …».
  - Nessuna lente piena; «Chiavi del calcolo» aperte di default.
- **Verifica del profilo:**
  - h1 «Profilo di pesi da verificare»;
  - s8: sigilli, controlli, tabella dei pesi, effetto sui task;
  - s4, sticky: «Verifica dell'auditor», campo per la motivazione, primario «Dai l'ok al profilo», con il dialogo «Dare l'ok al profilo di pesi?».
- **Registro:**
  - h1 «Registro degli atti»; a destra il secondario «Scarica il report di audit», con l'icona download.
  - Atti come righe impresse:
    - «#92 · Approvazione del profilo di pesi» in Corpo 600;
    - «Comitato guida · 17 ottobre 2026, 15:42» in Piccolo;
    - motivazione in Corpo;
    - impronta in Codice dentro un `<details>`.
  - Filtri come pillole con `aria-pressed`: «Tutti · Comitato · Revisori · Auditor · Amministratore».

### 12.5 Amministratore tecnico

**Console** (`/app/console`, guscio con «Console NEARTECH» al posto dell'organizzazione):
- Sezioni: Organizzazioni · Lavori.
- **Organizzazioni:**
  - h1 «Organizzazioni pilota»; primario «Nuova organizzazione pilota»;
  - righe in rilievo: nome in Corpo 600; in Piccolo «Fase 2 di 4 · Indirizzi · tocca al comitato guida»; a destra «2 lavori in corso» e la freccetta;
  - vuoto: «Nessuna organizzazione pilota» · «Creane una: la procedura crea lo spazio riservato, assegna i ruoli e carica i mansionari.» · «Nuova organizzazione pilota».
- **Lavori:**
  - tabella Lavoro · Organizzazione · Stato · Avviato · Durata · Costo;
  - Lavoro: «Scomposizione · mansionario-educatori.docx»;
  - Stato: badge «in coda», «in lavorazione», «applicato», «non riuscito»;
  - Avviato: data e chi;
  - per i lavori non riusciti, il secondario «Riavvia», con il dialogo e la motivazione, perché è un atto nuovo;
  - filtri a pillola «Tutti · In corso · Non riusciti»;
  - con lavori in corso, l'elenco si aggiorna da solo; i conteggi stanno in una regione `aria-live`.

**Procedura «Nuova organizzazione pilota»** (onboarding, 10.15): una colonna s8 centrata, con il riepilogo in s4 da 1280.

| Passo | Contenuto | Atto e comando |
|---|---|---|
| 1 Organizzazione | Nome · Settore · Codice breve, proposto dal sistema e modificabile finché non si conferma · nota «Lo spazio riservato `org_<codice>` si crea in UE.» | «Crea l'organizzazione» (atto) |
| 2 Persone e ruoli | Righe persona: Nome e cognome · Email di lavoro · Ruoli (caselle con descrizione). Servono almeno un membro del comitato guida, un revisore e un auditor; finché mancano, il riepilogo lo scrive. Casella «Attiva la vista del rappresentante dei lavoratori»; il rappresentante lo nomina poi il comitato | «Assegna i ruoli e invia gli inviti» (un atto per assegnazione, una motivazione) |
| 3 Mansionari | Area di caricamento (incasso con bordo tratteggiato #64748B, raggio 12, padding 32): «Trascina qui i mansionari .docx» e il secondario «Scegli i file .docx»; elenco dei file con stato | «Carica i mansionari» (atto) |
| 4 Stima dei costi | Lente piena «Costo stimato 1,20 €» e tre KPI bianchi «Al massimo, con i tentativi», «Token in ingresso ~12.400», «Token in uscita»; parametro `prezzi_scomposizione` in Codice; campo per la motivazione | «Conferma la stima e avvia la scomposizione» (atto). Senza parametro approvato: permesso, con «La scomposizione non parte: manca il parametro approvato dei prezzi. Decide il comitato di governance NEARTECH.» |
| 5 Riepilogo | Che cosa succede ora: «La scomposizione è in coda. Poi il revisore decide gli abbinamenti.» | «Apri l'organizzazione» |

**Persone e ruoli** (dentro un'organizzazione):
- h1 «Persone e ruoli»; sotto «Ogni assegnazione è un atto nel registro.»; primario «Aggiungi una persona», con l'icona user-plus.
- Tabella:
  - Persona: nome in Corpo 600, email in Piccolo;
  - Ruoli, in testo: «Comitato guida, Revisore»;
  - Accesso: «Attivo · ultimo accesso il 17 ottobre», «Invito inviato il 16 ottobre» oppure «Primo accesso da fare»;
  - testuale «Modifica i ruoli».
- **Pannello laterale dei ruoli:** caselle con descrizione:
  - Comitato guida: «Dà gli indirizzi, approva il profilo di pesi e la restituzione.»
  - Revisore: «Decide gli abbinamenti e giudica i task sulla rubrica.»
  - Auditor: «Verifica il profilo di pesi e segue il registro. Per il resto legge.»
  - Amministratore tecnico: «Carica i mansionari, avvia i lavori, assegna i ruoli.» Solo per persone NEARTECH.
  - Rappresentante dei lavoratori: se la vista non è attiva, non c'è; se è attiva, la casella è al suo posto con il lucchetto e «Lo nomina il comitato guida.»
- Campo obbligatorio «Motivazione dell'atto»; primario «Assegna i ruoli».
- Se l'API rifiuta una combinazione (per esempio comitato e auditor alla stessa persona, se il motore la vieta), l'errore sta sopra i comandi con il testo dell'API. La UI non inventa regole.
- Togliere un ruolo apre il dialogo «Togliere il ruolo di revisore a Marta Rossi?», con motivazione.
- Card «Vista del rappresentante dei lavoratori»: «Non attiva» e il secondario «Attiva la vista», con dialogo e motivazione.

**Documenti:**
- Intestazione: h1 «Mansionari e abbinamento»; sotto «Il testo resta nello spazio riservato dell'organizzazione.»
- Vuoto: area di caricamento con messaggio e comando insieme: «Nessun mansionario caricato» · «Caricali in formato .docx: la scomposizione parte solo dopo la conferma della stima dei costi.» Oggi il bottone sta a circa 900 px dal messaggio.
- Pieno:
  - tabella File · Ruolo · Stato · Task · Stima;
  - «Scomposizione», con la stima come al passo 4;
  - «Abbinamento al dataset»: «12 task in attesa di abbinamento» oppure «Nessun task in attesa di abbinamento», al posto di «0 task da abbinare»;
  - tabella dei lotti con nomi leggibili.

### 12.6 Rappresentante dei lavoratori (vista bonus)

- h1 «Variazioni di D da guardare»; sotto «Dovute agli indirizzi del comitato, dall'ultimo calcolo.»
- Una riga in rilievo per task:
  - nome in Corpo 600, ruolo in Piccolo;
  - pendenza 120×32 [PP];
  - «D da 0,62 a 0,48 · scende», con ▼ e la parola;
  - «Q1 → Q3».
- Per riga, due secondari: «Va bene così» e «Riporta al comitato». Il secondo apre il dialogo «Riportare al comitato la variazione di “Colloquio di accoglienza”?», con motivazione obbligatoria e il primario «Riporta al comitato».
- Tono di verifica: niente rosso, niente allarme. Le righe trattate diventano impresse, con «Riportata al comitato · atto #57».
- Vuoto: «Nessuna variazione di D da guardare» · «Gli indirizzi del comitato non hanno abbassato D per nessun task.»

### 12.7 Questionario d3/d4 sul telefono (senza account)

- Una colonna larga al massimo 560, margini 16, Corpo 16/24, senza guscio.
- In testa:
  - segno del logo 24 e «Questionario sul senso del lavoro · Educatori», in Piccolo;
  - «Anonimo: le risposte si leggono solo insieme a quelle di almeno 5 colleghi.» Il 5 viene da `minimo_rispondenti_gruppo`.
- Un task per schermata:
  - «Task 3 di 12», con una barra teal-ink da 8;
  - card con il task in Titolo e la domanda in Corpo, presi dal questionario approvato (parametro versionato), mai scritti nel frontend;
  - cinque risposte come righe radio a tutta larghezza, alte 56, raggio 12, bordo #64748B. Scelta: navy con spunta.
- Barra sticky in basso: «Indietro» testuale e «Avanti» primario da 48, più la safe area. All'ultimo task il primario diventa «Invia le risposte».
- **Stati:**
  - fine: «Grazie. Il risultato del tuo gruppo torna a te quando il questionario si chiude.»;
  - link già usato o scaduto: «Questo link è già stato usato o è scaduto. Chiedine uno nuovo a chi te l'ha inviato.»;
  - rete assente: le risposte restano sul telefono e «Avanti» riprova; il testo è «Non riesco a inviare. Le tue risposte restano qui: riprova quando hai campo.»

### 12.8 Accesso, primo accesso, scelta dell'organizzazione

**Accesso:**
- Card centrata, larga al massimo 440, padding 32, raggio 20, `--ombra-superficie`, logo da 32.
- h1 «Accedi alla tua organizzazione».
- Con SSO configurato: primario a tutta larghezza «Accedi con l'account aziendale».
- Con credenziali (corsia amministrazione):
  - campi «Email di lavoro» (`autocomplete="username"`) e «Password» (`current-password`, «Mostra»);
  - primario «Accedi»;
  - sotto, in Piccolo: «Password dimenticata? Chiedine una nuova all'amministratore NEARTECH.»
- Accesso di sviluppo, solo in locale e separato da un filetto: etichetta «Accesso di sviluppo (solo in locale)», campo «Soggetto SSO di prova» con l'esempio «prova|comitato», secondario «Entra in sviluppo».
- In fondo, in Piccolo Inter (non mono): «Dati ospitati in UE · nessuna valutazione di singole persone».
- **Errori:**
  - «Email o password non corrette. Riprova, oppure chiedi una nuova password all'amministratore NEARTECH.»
  - «Troppi tentativi. Riprova fra {minuti} minuti.» Il valore lo decide il server.

**Primo accesso** (password temporanea):
- Stessa card. h1 «Scegli la tua password»; sotto «La password che hai ricevuto vale solo per questo primo accesso.»
- Campi: «Nuova password» (`new-password`, «Mostra») e «Ripeti la nuova password».
- Sotto il primo campo, una lista di controlli che si aggiorna mentre scrivi, con icona e testo, mai solo colore:
  - «Almeno 12 caratteri»;
  - «Diversa dalla password ricevuta»;
  - «Le due password coincidono».

  La lunghezza minima la decide il server; il testo la riporta.
- Primario «Salva la password e continua». Errori accanto ai campi e riepilogo.
- **Orientamento**, una sola schermata e solo al primo accesso:
  - h1 «Sei nel comitato guida di ACME S.p.A.»;
  - tre righe piane:
    - «Che cosa decidete: gli indirizzi, il profilo di pesi, la restituzione.»
    - «Dove siamo: Fase 2 di 4 · Indirizzi.»
    - «Tocca a voi: date gli indirizzi.»
  - primario «Vai alla panoramica».
  - Per ogni ruolo cambiano solo le tre righe.

**Scelta dell'organizzazione:**
- h1 «Le tue organizzazioni».
- Righe in rilievo: nome in Corpo 600, codice in Codice, «Fase 2 di 4 · Indirizzi · tocca a te» in Piccolo, freccetta.

---

## 13. Sito pubblico

### 13.1 Impianto

- Larghezza massima 1200, 12 colonne, gutter 24.
- Margini 32 (≥ 1024), 24 (768–1023), 16 (< 768).
- Fra le sezioni 96 (64 sul telefono); dal titolo al contenuto 48.
- Scala tipografica in 3.2. Stessi token di colore, superfici e segni dell'app.
- Una sola superficie navy, la banda finale.
- Nessuna macchia, nessun gradiente, nessun carosello di loghi, nessuna testimonianza non documentabile.
- I video contengono la macchia dell'identità: è il loro contenuto. La pagina intorno non ne aggiunge.

**Navigazione** (alta 72, bianca, fissa, filetto basso dopo lo scorrimento):
- logo; «Il metodo · Programma pilota · Garanzie»; secondario «Accedi» (porta a `/app`); primario «Candidate la vostra organizzazione»;
- sotto i 1024, logo e «Menu» (44), che apre un foglio con le stesse voci.

**Termini:**
- il sito usa «task», spiegato alla prima occorrenza: «i task, cioè i singoli compiti di un ruolo»;
- usa «IA».

I video dicono «compiti» e «AI»: lo accetto finché non si rifà il render. Il testo del video li trascrive com'è.

### 13.2 Home

Struttura dalla skill landing: «Trust & Authority + Conversion» ed «Enterprise Gateway» (apertura → prova → soluzione → invito, percorsi per ruolo); «Product Demo + Features» per il video (sottotitoli o testo, play e pausa visibili, niente autoplay).

1. **Apertura** (s6 + s6; una colonna sotto i 1024, con il video sotto il testo).
   - Etichetta «Programma pilota 2027».
   - h1 «L'IA entrerà nei vostri ruoli. Decidete voi dove.»
   - Testo d'apertura (Corpo, `--testo`, 56ch): «Neartech scompone i mansionari in task e, per ciascuno, misura quanto serve una persona e quanto conta che lo sia. Il vostro comitato guida legge la mappa, dà gli indirizzi e approva: ogni scelta resta in un registro verificabile.»
   - Primario «Candidate la vostra organizzazione»; secondario «Leggete come funziona il metodo».
   - In Piccolo: «Sperimentazione 2027 · dati ospitati in UE · nessuna valutazione di singole persone».
   - A destra il **video del pitch** (10.20), con la didascalia «Neartech in 1 min 19 s · senza voce, con musica» e «Leggi il testo del video».
2. **«Il ruolo è l'unità sbagliata.»** (s5 + s7): un paragrafo, e una striscia con gli 8 task di un ruolo d'esempio, ciascuno con il segno e il suo quadrante.
3. **«Due assi, per ogni task.»**
   - s5: due paragrafi su N e D.
   - s7: la **mappa vera** (stesso componente, stessa legenda, stessi segni) con dati sintetici, e il badge «Esempio con dati sintetici».
   - Tre annotazioni con filo [PP]:
     - «Colloquio con le famiglie: la persona è necessaria e conta»;
     - «Diario di bordo del turno: automazione possibile»;
     - «Accoglienza del mattino: scelta di valore».
4. **«Come funziona.»**
   - Il **tracciato a sigilli** della piattaforma, statico, a tutta larghezza:
     - Avvio: «Caricate i mansionari» · sigillo «Il revisore decide gli abbinamenti»;
     - Indirizzi: «Il comitato dà gli indirizzi» · «Comitato e auditor»;
     - Verifica: «I revisori controllano a campione»;
     - Esito: «Approvate la restituzione» · «Atto nel registro».
   - Sotto, s8 centrata, il **video del metodo** con la didascalia «Il metodo in 2 min 17 s» e il testo.
   - Poi il testuale «Leggete il metodo per esteso».
5. **«Per chi decide» e «Per chi lavora»**: s6 + s6, come superfici, con i percorsi per ruolo («Enterprise Gateway»).
6. **«Garanzie»:** griglia 2×2, icona 24, titolo e testo:
   - «I vostri documenti restano in UE» (scudo);
   - «Leggiamo task e ruoli, mai le persone» (persone);
   - «Ogni decisione è un atto nel registro» (libro);
   - «La sperimentazione si dichiara voce per voce» (check-circle).
7. **Banda finale navy:**
   - raggio 20, padding 64 (32 sul telefono);
   - h2 bianco «Cerchiamo le prime organizzazioni pilota del 2027.»;
   - testo #CBD5E1;
   - bottone bianco «Candidate la vostra organizzazione», con focus bianco.
8. **Piede** in Piccolo: privacy, contatti, «NEARTECH · AI & Consulting».

Le cifre del pitch (96%, 25%, ecc.) compaiono fuori dal video solo con la loro fonte in Piccolo.

### 13.3 Il metodo (`/metodo`)

- h1 «Capire il lavoro per decidere meglio» e il video del metodo in apertura.
- Le sezioni di `metodo-neartech-per-clienti.html`:
  - «Due assi per ogni compito», con la mappa d'esempio;
  - «Dalla mansione alla restituzione», nove passi come elenco verticale; ogni passo ha un badge di tipo, «decisione delle persone» (sigillo) oppure «calcolo» (tratta), e la riga «Chi agisce: …»;
  - «Le persone decidono, l'IA prepara»;
  - «Nessuna scatola nera»;
  - «Una vista per ciascun ruolo».
- Chiude la banda finale.

### 13.4 Programma pilota (`/pilota`)

- h1 «Il programma pilota 2027».
- Sezioni:
  - «Che cosa vi chiediamo»: i mansionari, un comitato guida, due o tre revisori, un auditor;
  - «Che cosa ricevete»: la mappa dei task, la restituzione approvata, il registro degli atti;
  - «Come si svolge»: il tracciato a quattro fasi, con «La prima mappa richiede alcune settimane»;
  - «Sperimentazione dichiarata»: che cosa è provvisorio e come lo rendete solido;
  - «Domande frequenti»: righe con `<details>`, summary alti 44, risposte impresse.
- Nessuna durata, nessun prezzo, nessun numero che non sia documentato (`voce-e-testi.md`). Dove non è deciso: «Lo definiamo con voi al primo incontro.»

### 13.5 Candidatura (`/candidatura`)

- Una colonna larga al massimo 560.
- h1 «Candidate la vostra organizzazione».
- Campi:
  - «Che cosa vi serve» (radio): «Partecipare al programma pilota» oppure «Un primo incontro di mezz'ora» (riprende «Fissiamo mezz'ora» del video);
  - Organizzazione;
  - Settore;
  - Numero di ruoli (fasce);
  - Nome e cognome;
  - Ruolo di chi scrive;
  - Email di lavoro;
  - Messaggio (facoltativo);
  - casella «Ho letto l'informativa sulla privacy», con il link.
- Primario «Invia la candidatura».
- Errori accanto ai campi, con il riepilogo.
- Successo, al posto del modulo: «Candidatura ricevuta. Vi rispondiamo via email all'indirizzo indicato.» Nessuna scadenza promessa.

---

## 14. Checklist: ogni punto della critica e della diagnosi, risolto

| Punto | Correzione | Dove | Criterio |
|---|---|---|---|
| 1a · badge «Date gli indirizzi» rotto | L'eyebrow non esiste più; il titolo della banda comincia con chi agisce («Tocca a voi: date gli indirizzi»), un livello per riga | 10.3 | 8 |
| 1b · bottone schiacciato a destra, 670 px dal titolo | Griglia `minmax(0,72ch) auto` con `justify-content: start`: il comando sta a 32 px dal testo, centrato sul blocco; testo su una riga; ombra navy | 10.3 | 8 |
| 2a · gerarchia, 20 stili, 11 grandezze, 63 stili inline | 6 stili come token `font`, pesi 400/600, un solo grigio secondario, mono solo per i codici, nessuno `style={{}}` | 3, 15 | 1, 2, 5 |
| 2b · chip del percorso illeggibili (contrasto AA sì, 11 px no) | I chip delle fasi spariscono: stato scritto a 13 px in `--testo-2` (6,94). Corretti i veri fallimenti: menu 2,56, punto stima 2,15, tratta in anticipo 1,90, futuro 1,57, barra vuota 1,47, bordi 1,23 | 4.2, 10.3 | 3 |
| 2c · «fase 2 di 4» nascosto | h1 «Fase 2 di 4 · Indirizzi» a 24 px, a sinistra | 10.3 | 8 |
| 3a · numeri senza gabbia, il «10» invade Q1 | «Qn · nome / n task» in fasce HTML negli angoli esterni, fuori dall'area dei dati | 11.3 | 10 |
| 3b · pallini anonimi, legenda lontana | Legenda sopra il disegno, segni identici e conteggi; due canali binari più l'anello; via l'opacità a otto gradini | 11.4, 11.5 | 10 |
| 3c · segni tagliati, etichette fuori a 390 | Respiro di 16 px su entrambi gli assi; testo HTML che va a capo; «Qn · n» sotto i 120 px; matrice sotto i 520 | 11.2, 11.8 | 10 |
| 4a · KPI «10/20», numero gigante e testo minuscolo | Lenti: Numero 32 ed etichetta 14 sulla stessa linea di base, nota 13; principale «7 risultati da confermare»; il conteggio di Q4 non è più un KPI | 10.4 | 11 |
| 4b · scudo e bersaglio | Nessuna icona nei KPI; scudo solo sul sito per la protezione dei dati; bersaglio tolto | 7, 10.4 | 11 |
| 4c · ciambella minuscola ed elenco k1…r | Otto righe con il nome, barre orizzontali da 8, zero = solo binario, niente ciambella | 9, 10.6 | 12 |
| 5a · voci disallineate | Un solo asse a x = 28, etichette a x = 60 | 10.1 | 6 |
| 5b · icone grigie, interlinea (smentito) | Voci «In arrivo» tolte (pseudo-voci a 2,56:1) | 10.1 | 6, 13 |
| 5c · piede che esce dallo schermo, Esci 36 | Piede sticky, «Esci da Neartech» alto 44, visibile da 464 px; ombra di scorrimento; sul telefono `grid-template-rows: auto 1fr` | 10.1 | 6, 7 |
| Verdetto · «finto-moderna» | Griglia a 12 su base 4, 9 spazi, 4 raggi, 8 ombre in navy, materiali con un significato; l'architettura resta | 2, 5 | 5 |
| Altri problemi: fallimenti AA (disabilitato 3,13, mini-barra Q1 2,56) | Disabilitato #475569 su #E4E9F1 (6,22), con il motivo scritto; mini-barre tolte | 4.2, 10.11 | 3 |
| Altri problemi: guscio del telefono (voce attiva fuori, barra 121/272) | Barra alta 56 e barra delle sezioni con al massimo 4 posti: voce attiva sempre visibile | 10.1 | 7 |
| Altri problemi: identità tre volte, «Torna alla mappa» | Organizzazione solo nel menu; «Torna alla mappa» tolto | 10.1, 10.2 | 13 |
| Altri problemi: fieldset e legend «barrati», ritmo ambiguo | Separatore sul `div.domanda`; 8 / 12 / 32 | 10.12 | 15 |
| Altri problemi: pillole da 39, bottone disabilitato muto, «BOZZA-1» | Pillole da 44; bottone sempre attivo con «3 di 8 risposte» e riepilogo; versione nelle chiavi | 10.12, 12.2 | 15 |
| Altri problemi: numeri non italiani | `Intl.NumberFormat('it-IT')`; «sotto 0,10» | 3.1 | 14 |
| Altri problemi: Revisione con `Math.round`, senza avanzamento | Binario della stima fra i livelli; «2 di 6 voci»; «Passa al task successivo» | 10.13, 12.3 | 14 |
| Altri problemi: codici interni nelle etichette | «Lotto del 17 ottobre 2026», «Istruzioni di abbinamento, versione 1», «Profilo dalle risposte del …»; codici solo in Codice e nelle chiavi; «k1» con un solo maiuscolo | 9, 12 | 12 |
| Altri problemi: inviti pseudo-bottoni, glifi, permesso | Righe piane senza glifi; link solo se esiste la schermata; testi all'indicativo per gli altri ruoli | 10.7 | 13, 17 |
| Altri problemi: provenienza diluita | Un colore, un significato; avvisi e note in navy con l'icona | 4.3 | 4 |
| Altri problemi: mini-barre dei ruoli | Colonne Q1–Q4 numeriche con campione di tinta; righe sul telefono | 10.8 | 14 |
| Altri problemi: mappa senza tastiera, bersagli da 10, summary da 36 | Roving tabindex con frecce spaziali; bersagli r 12/22; summary 44 | 11.6, 11.7 | 10 |
| Altri problemi: h1 e titolo della mappa ripetuti | h1 = fase; h2 della mappa = «Dove stanno i 27 task · mappa provvisoria» | 10.3, 11.1 | 8 |
| Altri problemi: Documenti vuota (zero nel titolo, bottone lontano) | Area di caricamento con messaggio e comando insieme; nessuno zero nei titoli | 12.5 | 17 |
| Altri problemi: coda annidata | Pannello laterale e barra del task; nessuna area di scorrimento annidata | 12.3 | 14 |
| Altri problemi: Accesso (mono 11, bordo 1,23) | Etichetta in Corpo 600, nota in Piccolo Inter, bordo #64748B | 12.8 | 1, 3 |
| Altri problemi: 7 raggi, ombra nera, inline | 4 raggi, ombre-token, nessuno stile inline | 5, 15 | 5 |
| Giurie · bilancio verticale (Q4/Q2 sotto la piega a 1280×800 e 1300×670) | Percorso compatto (192), testata con il tracciato sulla stessa riga, H che tiene conto della finestra | 2.5 | 9 |
| Giurie · #7E8BA0 a 2,92 su Q2 | Bordo dei controlli #64748B (≥ 4,03) | 4.1 | 3 |
| Giurie · scarto di 3 px inefficace | Cerchio di raggio 7, poi 14 | 11.4 | 10 |
| Giurie · respiro verticale e conteggi in legenda | 16 px su entrambi gli assi; conteggi in legenda | 11.2, 11.5 | 10 |
| Giurie · tacca e pannello fragili | Linguetta come pseudo-elemento della tratta, senza calcoli di posizione | 10.3 | 8 |
| Giurie · identità poco memorabile | Il verbale con i sigilli: linguetta, quattro materiali, gli stessi segni nell'app e sul sito | 1 | 20 |
| Giurie · ellisse con una sola unità | `rx` e `ry` con unità separate | 11.4 | 10 |
| Giurie · opacità .25 delle lenti sotto 1.4.11 | Punto attenuato con tratto #475569 (≥ 6,41) | 11.4 | 3 |

---

## 15. Blocco dei token CSS (da incollare in `web/src/stile.css`)

Sostituisce l'attuale `:root` e le sue varianti. Le classi esistenti che usano `--t-xs`, `--t-s`, `--t-m`, `--t-l`, `--t-xl`, `--t-2xl`, `--t-3xl`, `--stone-ink`, `--border`, `--gap`, `--colonna-laterale` e `--tracciato-*` vanno riscritte con i token nuovi. Nessun alias di compatibilità: se restasse, rimarrebbe anche la scala vecchia.

```css
/* Sistema di design v2 (docs/piattaforma/sistema-di-design-v2.md). Fonte unica dei token.
   Palette, caratteri e logo dall'identità v3.1 (docs/identita/neartech-identita.css): invariati. */
:root {
  /* Marca (invariata) */
  --navy: #0B2559; --navy-800: #07193D; --cobalt: #1B499F; --teal: #00B4B4; --teal-ink: #007272;
  --violet: #521983; --amber: #F59E0B; --amber-ink: #92400E; --emerald: #10B981; --emerald-ink: #065F46;
  --risk: #E11D48; --risk-ink: #9F1239;
  --obsidian: #0F172A; --slate: #475569; --stone: #64748B; --paper: #FFFFFF;
  --q1: #E6FAFA; --q2: #F1E9F9; --q3: #FEF3C7; --q4: #EEF2F9;   /* solo mappa e campioni dei quadranti */

  /* Testo */
  --testo: var(--obsidian);            /* 17,85 bianco · 16,36 tela */
  --testo-2: var(--slate);             /* unico grigio secondario: 7,58 bianco · 6,94 tela · ≥ 6,41 tinte */
  --testo-titolo: var(--navy);
  --link: var(--cobalt);
  --testo-su-scuro: #FFFFFF;           /* 14,76 navy · 17,28 navy-800 */
  --testo-su-scuro-2: #CBD5E1;         /* 9,94 navy · 11,64 navy-800 */
  --accento-su-scuro: #7EE0E0;         /* solo icona di conferma negli avvisi */

  /* Superfici e bordi */
  --tela: #F3F5F9;
  --superficie: #FFFFFF;
  --superficie-scura: var(--navy);
  --superficie-sospesa: var(--navy-800);
  --contatore-su-scuro: #324874;       /* bianco 9,07 */
  --bordo-superficie: #E4E9F1;         /* decorativo, 1,22 */
  --bordo-controllo: var(--stone);     /* 4,76 bianco · 4,36 tela · ≥ 4,03 tinte */
  --binario: #E4E9F1;
  --sfondo-dialogo: rgba(7, 25, 61, .48);

  /* Significati: un colore, un significato */
  --azione: var(--navy); --azione-hover: var(--cobalt); --azione-premuta: var(--navy-800);
  --avanzamento: var(--teal-ink);      /* 4,72 sul binario */
  --persone: var(--emerald-ink);       /* giudizio di persona: ≥ 6,50 sulle tinte */
  --stima: var(--amber-ink);           /* stima del modello: ≥ 6,00 sulle tinte */
  --somiglianza: var(--cobalt);        /* derivato per somiglianza, nuovo */
  --incerto: var(--navy);
  --errore: var(--risk-ink);           /* 8,02 bianco · 7,34 tela */
  --focus: var(--teal-ink);            /* 5,75 bianco · 5,27 tela */
  --focus-su-scuro: #FFFFFF;
  --disabilitato-fondo: #E4E9F1; --disabilitato-testo: var(--slate);   /* 6,22 */

  /* Caratteri e scala: sei stili */
  --f-ui: 'Inter', -apple-system, 'Segoe UI', sans-serif;
  --f-mono: 'JetBrains Mono', ui-monospace, Consolas, monospace;
  --t-numero: 600 32px/40px var(--f-ui);        --tr-numero: -0.02em;
  --t-pagina: 600 24px/32px var(--f-ui);        --tr-pagina: -0.015em;
  --t-titolo: 600 18px/24px var(--f-ui);        --tr-titolo: -0.01em;
  --t-corpo: 400 14px/24px var(--f-ui);
  --t-corpo-forte: 600 14px/24px var(--f-ui);
  --t-piccolo: 400 13px/20px var(--f-ui);
  --t-piccolo-forte: 600 13px/20px var(--f-ui);
  --t-codice: 500 12px/16px var(--f-mono);
  /* Sito pubblico */
  --ts-apertura: 600 48px/56px var(--f-ui);     --tr-apertura: -0.03em;
  --ts-sezione: 600 32px/40px var(--f-ui);      --tr-sezione: -0.02em;
  --ts-titolo: 600 20px/28px var(--f-ui);
  --ts-corpo: 400 16px/28px var(--f-ui);
  --ts-corpo-forte: 600 16px/28px var(--f-ui);
  --ts-piccolo: 400 14px/20px var(--f-ui);
  --ts-etichetta: 600 12px/16px var(--f-mono);  --tr-etichetta: 0.08em;

  /* Spazi (base 4, ritmo 8) */
  --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px; --s-5: 24px; --s-6: 32px; --s-7: 48px; --s-8: 64px; --s-9: 96px;

  /* Raggi: quattro significati */
  --r-superficie: 20px; --r-riga: 12px; --r-badge: 6px; --r-comando: 999px;

  /* Ombre (solo navy) */
  --ombra-superficie: 0 1px 2px rgba(11, 37, 89, .06), 0 4px 12px -4px rgba(11, 37, 89, .08);
  --ombra-riga: 0 1px 2px rgba(11, 37, 89, .08);
  --ombra-riga-alta: 0 2px 4px rgba(11, 37, 89, .06), 0 8px 16px -8px rgba(11, 37, 89, .16);
  --ombra-comando: 0 1px 2px rgba(11, 37, 89, .16), 0 4px 12px -4px rgba(11, 37, 89, .32);
  --ombra-sospesa: 0 8px 24px -8px rgba(7, 25, 61, .32);
  --ombra-dialogo: 0 24px 48px -12px rgba(7, 25, 61, .32);
  --ombra-impresso: inset 0 1px 2px rgba(11, 37, 89, .10), inset 0 0 0 1px #E4E9F1;
  --ombra-scorrimento: 0 -8px 12px -8px rgba(11, 37, 89, .16);

  /* Movimento */
  --ease: cubic-bezier(.22, 1, .36, 1); --ease-uscita: cubic-bezier(.4, 0, 1, 1);
  --dur-breve: 120ms; --dur-media: 200ms; --dur-lunga: 320ms;

  /* Guscio e griglia */
  --larghezza-menu: 240px; --margine-pagina: 32px; --gutter: 24px; --larghezza-contenuto: 1360px;
  --margine-alto: 24px; --padding-superficie: 24px; --padding-alto-percorso: 24px; --menu-spazio: 24px;
  --barra-alta: 56px; --barra-sezioni: 64px;
  --bersaglio: 44px; --bersaglio-telefono: 48px;

  /* Livelli */
  --z-menu: 10; --z-barra-task: 20; --z-suggerimento: 30; --z-pannello: 40; --z-avvisi: 50;
}
@media (max-width: 1279px) { :root { --margine-pagina: 24px; } }
@media (max-width: 1023px) { :root { --gutter: 16px; } }
@media (max-width: 767px) {
  :root {
    --margine-pagina: 16px; --padding-superficie: 16px;
    --t-corpo: 400 16px/24px var(--f-ui); --t-corpo-forte: 600 16px/24px var(--f-ui);
    --t-piccolo: 400 14px/20px var(--f-ui); --t-piccolo-forte: 600 14px/20px var(--f-ui);
    --ts-apertura: 600 36px/44px var(--f-ui); --ts-sezione: 600 28px/36px var(--f-ui);
  }
}
@media (min-width: 1024px) and (max-height: 760px) {
  :root { --margine-alto: 16px; --padding-alto-percorso: 16px; --menu-spazio: 16px; }   /* bersagli invariati */
}

/* Regole di base che fanno rispettare i token */
body { background: var(--tela); color: var(--testo); font: var(--t-corpo); font-variant-numeric: tabular-nums;
  -webkit-font-smoothing: antialiased; }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.su-scuro :focus-visible, .su-scuro:focus-visible { outline-color: var(--focus-su-scuro); }
.codice { font: var(--t-codice); }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; animation: none !important; scroll-behavior: auto !important; }
}
```

---

## 15 bis. Avvio dell'implementazione

Questi passi sono indicazioni per la sessione principale: io non ho modificato `web/`.

1. Incollare il blocco della sezione 15 in `stile.css` e riscrivere le classi esistenti sui token nuovi; nessuna grandezza o spazio fuori scala.
2. Togliere i 63 `style={{}}` dalle viste.
3. Ricostruire, in quest'ordine, la mappa (`MappaQuadranti.tsx`), il percorso (`BarraPercorso.tsx`) e il menu (`Guscio.tsx`). Poi i KPI come lenti (`Panoramica.tsx`), la sperimentazione con i nomi (`Avanzamento.tsx` e il nuovo `voci.ts`) e gli inviti (`inviti.ts`, senza glifi).

Ogni passo si chiude con i criteri della sezione 16 che lo riguardano.

---

## 16. Criteri di accettazione

Si verificano nel browser sull'istanza :8010, con i soggetti di prova comitato, revisore, auditor e admin, a zoom 100%. Le finestre sono 1440×900, 1280×800 e 390×844, più quelle indicate.

1. **Tipografia.**
   - Grandezze calcolate: sopra i 768 solo 12 (e solo in JetBrains Mono con `.codice`), 13, 14, 18, 24 e 32; sotto i 768 solo 12, 14, 16, 18, 24 e 32. SVG compreso.
   - Inter solo a 400 e 600; il 700 solo in `.logo-nome`. Nessun `text-transform: uppercase`.
   - Al massimo 8 combinazioni di famiglia, grandezza e peso per vista, più il logotipo.
2. **Mono.** Ogni elemento in JetBrains Mono ha `.codice`. Nessun numero di KPI, tabella o asse è in mono.
3. **Contrasto** (axe più calcolo).
   - Testo ≥ 4,5:1 ovunque, disabilitati compresi.
   - Bordi di campi, pillole, livelli e secondari ≥ 3:1 su ogni fondo, Q2 compresa.
   - Segni della mappa ≥ 3:1 sulla loro tessera, anche attenuati da una lente.
   - Focus ≥ 3:1 sul fondo vicino.
4. **Esadecimali.**
   - Nessun esadecimale in `web/src` fuori da `stile.css`.
   - Le tinte q1–q4 solo in mappa, matrice e campioni.
   - Nessun `style={{}}` con fontSize, margin, padding o gap.
5. **Spazi, raggi, ombre.**
   - Margin, padding e gap calcolati solo 0, 4, 8, 12, 16, 24, 32, 48, 64 (96 sul sito), anche negativi.
   - `border-radius` solo 0, 6, 12, 20, 999 o 50%.
   - Ombre solo dai token, nessun `rgba(0,0,0,…)`.
6. **Menu.**
   - Segno del logo, nome dell'organizzazione, icone, avatar e icona di «Esci» a x = 28 ± 1; etichette delle voci a x = 60 ± 1.
   - Nessuna voce «In arrivo».
   - «Esci da Neartech», alto 44, è visibile senza scorrere a 1366×657, 1280×520 e 1280×464 per tutti e quattro i ruoli.
7. **Telefono, 390×844.**
   - Barra alta 56 in ogni vista, Lotti vuota compresa.
   - Barra delle sezioni con al massimo 4 posti e la voce attiva visibile.
   - `scrollWidth === innerWidth`.
   - Nessun testo sotto i 14 px, salvo il Codice.
8. **Percorso.**
   - h1 «Fase 2 di 4 · Indirizzi» a 24 px, a sinistra; nessun testo mono o maiuscolo nella superficie.
   - La linguetta della fase corrente tocca la banda, coprendone il filetto.
   - Nessuna etichetta in linea con un titolo.
   - Con contenitore ≥ 760: testo della banda su una riga a 1280 e 1440, bottone a ≤ 32 px dal testo, centro del bottone entro ±4 px dal centro del blocco di testo.
   - Ogni tratta è un bottone che apre le sue prove, che si chiudono con Esc.
9. **Bilancio verticale.**
   - La card della mappa comincia a y ≤ 240 a 1280×800 e 1440×900, e a y ≤ 224 a 1300×670.
   - Fascia bassa Q4/Q2 e asse N interi sopra la piega a 1440×900, 1280×800, 1280×720, 1300×670 e 1366×657.
10. **Mappa**, a 1024, 1280 e 1440.
    - Legenda tutta sopra il disegno, con gli stessi segni; i conteggi tornano con lenti e tabella.
    - Nessun punto (anello compreso) tocca un'etichetta, un conteggio o il bordo dell'area.
    - Q3 in alto a sinistra, Q1 in alto a destra, Q4 in basso a sinistra, Q2 in basso a destra, ognuno con «Qn · nome» e «n task», mai troncati.
    - Nessuna coppia di centri a meno di 7 px.
    - Valori degli assi con la virgola.
    - L'ellisse cambia forma con N e D separatamente.
    - Da tastiera: un solo arresto di tabulazione; ←/→ seguono N e ↑/↓ seguono D; Invio fissa il suggerimento, Esc lo chiude.
    - A 390: matrice 2×2 di bottoni alti almeno 96; un tocco apre l'elenco.
11. **Lenti.**
    - Nessuna icona né freccia; numero a 32 sulla stessa linea di base dell'etichetta.
    - `aria-pressed`; una lente premuta attenua gli altri punti e filtra la tabella, e la riga `aria-live` lo dice.
    - Al massimo una lente piena: nessuna per auditor e amministratore, né quando il valore è 0.
12. **Nomi delle voci.**
    - Nell'interfaccia «k1», «k2», «k3», «r», «d1»–«d4» non compaiono mai da soli come testo.
    - La sperimentazione ha 8 righe con i nomi della sezione 9; uno zero mostra solo il binario e «0 di 27».
13. **Nessuna pseudo-azione.**
    - Ogni elemento con `--ombra-riga`, o con raggio 999 e un testo dentro, è un `a` o un `button`.
    - Nessun bottone disabilitato senza il motivo scritto.
    - Il nome dell'organizzazione compare una volta per schermata.
14. **Dati e liste.**
    - Numeri a destra in formato it-IT; tabelle ordinabili con `aria-sort`; Ruoli con Q1–Q4 in colonne numeriche.
    - Revisione: con stima 2,5 il cerchio sta fra i livelli 2 e 3 e il testo dice «fra il livello 2 e il 3»; dopo l'ultima voce c'è «Passa al task successivo»; nessuna area di scorrimento annidata.
15. **Moduli.**
    - Campi e pillole alti almeno 44; nessuna linea a metà della legend; domande a 32 l'una dall'altra.
    - Con il questionario incompleto, l'invio porta il focus sul riepilogo con i link.
    - I campi password accettano l'incolla e hanno «Mostra».
16. **Focus.** Visibile su ogni elemento interattivo (2 px teal-ink, bianco sul navy) e mai coperto dalla barra sticky della Revisione né dalla barra delle sezioni.
17. **Stati.**
    - Con la rete rallentata, i segnaposto compaiono dentro il guscio dopo 300 ms e il CLS resta sotto 0,1.
    - Un errore 500 dà il messaggio con «Riprova» dentro il guscio.
    - Con l'organizzazione vuota, ogni stato vuoto ha il comando nello stesso blocco.
    - Auditor e revisore non vedono inviti all'imperativo né comandi che non possono usare.
18. **Avvisi temporanei.** Dopo un atto: `role="status"`; il focus resta dov'era; l'avviso si chiude dopo 5 s, si ferma al passaggio e non ha «Annulla».
19. **Movimento.** Al caricamento nessuna transizione; con `prefers-reduced-motion` nessuna transizione, nemmeno dopo un atto.
20. **Sito.**
    - Nessuna macchia né gradiente nella pagina; una sola superficie navy.
    - Mappa e tracciato sono gli stessi componenti della piattaforma.
    - I video non partono da soli, hanno `preload="none"`, poster e «Leggi il testo del video» con tutte le scene.
    - A 1440 l'apertura con il video sta nella prima schermata; a 390 non c'è scorrimento orizzontale.
    - Gli errori della candidatura stanno accanto ai campi.

---

## 17. Regole della skill `ui-ux-pro-max` usate

**Design system**
- Ricerca `--design-system` «enterprise governance decision tool workforce» (variance 2, motion 2, density 6).
- Preso «Minimalism & Swiss Style»: griglia, gerarchia, essenzialità.
- Scartati palette, caratteri e «Scroll Reveal» (sezioni 5 e 6).

**UX**
- Progress Indicators («Step 2 of 4»).
- Empty States.
- Toast Notifications (3–5 s).
- Focus Not Obscured (Minimum): `scroll-padding`.
- Focusable Error Summary.
- Accessible Authentication (Minimum): incolla e gestori di password.
- Password Visibility.
- Sticky Navigation.
- Table Handling.
- Auto-Play Video: click-to-play, `preload="none"`, testo.
- Target Size e Touch Target Size: per il web la WCAG chiede 24 px; il vincolo del progetto resta 44.

**Chart**
- Correlation / Distribution (Scatter): forme, etichette dirette, tabella, valori al focus, niente dispersione su mobile.
- Performance vs Target: numero e testo accanto alla barra, niente ciambella.

**Icons**
- check-circle, lock, user-plus, play, key, eye, clock, upload-simple, info, warning-circle.
- Lo scudo è Security.

**Landing**
- Trust & Authority + Conversion.
- Enterprise Gateway.
- Product Demo + Features.

**Typography**
- Dashboard Data: «Code for data, Sans for labels», ristretta ai codici.

**Stack react**
- «Focus trap in modals, return focus on close».

**Quick reference**
- `color-contrast`, `color-not-only`, `focus-states`, `aria-labels`, `escape-routes`, `accessible-authentication`, `safe-area-awareness`, `progressive-loading` (applicata senza luccichio), `heading-line-balance`, `progressive-disclosure`, `password-toggle`, `autofill-support`, `multi-step-progress`;
- `bottom-nav-limit`, `bottom-nav-top-level`, `adaptive-navigation`;
- `legend-visible`, `contrast-data`, `sortable-table`, `direct-labeling`, `tooltip-keyboard`, `touch-target-chart`, `responsive-chart`, `screen-reader-summary`, `data-table`, `trend-emphasis`, `pattern-texture`;
- `spacing-scale`, `elevation-consistent`, `z-index-management`, `font-scale`, `weight-hierarchy`, `readable-font-size`, `line-length-control`, `number-tabular`, `number-formatting`;
- `primary-action`, `disabled-states`, `focus-management`, `toast-accessibility`;
- `motion-meaning`, `excessive-motion`, `exit-faster-than-enter`, `animation-optional`.

**Ricerche senza risultato**
- `--stack react` «container query responsive layout»;
- icons «building office company» e «caret chevron right»;
- ux «bottom navigation mobile»: ha restituito Back Button e Sticky Navigation, non la barra in basso. Per la barra ho usato `bottom-nav-limit` e `adaptive-navigation` della quick reference;
- ux «wizard multi step form»: solo Progress Indicators e Submit Feedback; il resto della procedura a passi è mio.

---

## 18. Scelte aperte (due, con raccomandazione)

1. **Dove sta il percorso.**
   - **Raccomandato:** testata compatta a tutta larghezza, con il tracciato sulla stessa riga dell'h1 e la banda con la linguetta (sezione 10.3). Tiene il tracciato approvato il 17/10, mette «Fase 2 di 4 · Indirizzi» come titolo della pagina e fa stare la mappa intera fino a 657 px di altezza.
   - Alternativa [TS]: percorso verticale nella colonna s4, accanto alla mappa. Libera altri 100 px in alto, ma l'azione scende in una colonna da 309–363 px, la colonna destra si allunga e il tracciato approvato va rifatto, con una nuova approvazione.
2. **Fondo della banda dell'azione.**
   - **Raccomandato:** incasso tela (A1). Il navy resta a «dove sei, che cosa premi, che cosa ti aspetta», e la linguetta tela unisce fase e azione.
   - Alternativa: banda navy (A2), con «Tocca a voi:» in #7EE0E0, testo #CBD5E1 e bottone bianco con `--ombra-comando`. In proiezione si vede di più, ma mette due masse navy nella stessa vista (banda e lente principale) che chiedono attenzione insieme.
