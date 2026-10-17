# Direzione creativa della piattaforma

Documento del direttore creativo (fase 6). Decide la direzione visiva e d'interazione; chi implementa è la sessione principale. Fonte unica dei token: `web/src/stile.css`. Palette, caratteri e logo dell'identità restano quelli che ci sono: qui si aggiungono solo token di spazio, tipografia, superficie e layout.

---

## 2026-10-17 · Il percorso del pilota come tracciato a sigilli, e l'equilibrio della panoramica a zoom 100%

Osservazione del responsabile dopo la fetta 6 (commit e6a8ae2): il menu laterale piace; la barra delle fasi è «orribile», il testo è spostato a sinistra e non dà l'idea di una roadmap; a zoom 67% la pagina «si stabilizza» e la mappa respira, ma c'è comunque «qualcosa che non va». Niente soluzioni banali.

### 0. Difetti concreti nel reso attuale

Misure ricavate da `stile.css` e dagli screenshot. Lo schermo del responsabile a 100% ha una finestra utile stimata di **circa 1300 × 670 px CSS** (il menu da 256 px occupa 360 px dell'immagine: fattore 1,4).

| # | Dove | Che cosa | Perché danneggia la lettura |
|---|---|---|---|
| D1 | `.percorso` | Colonna fissa di 320 px per «Tocca a te» più 4 tessere in `1fr`: a 1300 px ogni tessera è larga ~152 px; tolti padding (32), segno (28) e gap (12) restano **~78 px di testo**. A 1280 sono ~68 px, a 1440 ~108 px, a 67% (~1970 px CSS) ~240 px. | Sottotitoli a capo parola per parola («La / visione / del / comitato…»). È la causa diretta della differenza tra 100% e 67%. |
| D2 | `.fase` | Le tessere si allungano all'altezza del riquadro navy (`align-items: stretch`, ~247 px) ma il testo resta in alto a sinistra, accanto al segno. | Un blocco stretto incollato all'angolo e un vuoto sotto: è il «testo sposizionato a sinistra». |
| D3 | `.fasi` | Quattro tessere uguali e staccate, senza linea che le unisca, senza misura di avanzamento, senza «adesso», senza chi deve agire. | Sembrano quattro schede di un menu, non un percorso nel tempo. Le fasi sovrapposte (indirizzi e verifica entrambe «in corso») non si capiscono. |
| D4 | Ordine della pagina | Intestazione (~116 px) + fasi (~247) + sperimentazione (~230) + spazi: la mappa comincia a **~630 px**, cioè sotto la piega a 100%. A 67% la finestra diventa ~1010 px CSS e la mappa entra nella prima schermata. | Il titolo promette «dove sta ciascuno» e la prima schermata mostra processo e avanzamento, non la risposta. È questo il «qualcosa che non va» più grave: a 67% non migliora la scala, migliora l'ordine percepito. |
| D5 | `MappaQuadranti` | L'SVG ha `viewBox` 640 × 430 e si adatta in larghezza: la colonna `s7` a 1300 px dà ~517 px di disegno (fattore 0,81). Le etichette dei quadranti da 10,5 diventano **8,5 px**, gli assi da 11 diventano 8,9 px, i conteggi da 20 diventano 16. | Testo sotto la soglia di leggibilità, peggio in proiezione. Le etichette dei quadranti finiscono sotto i punti (Q3 e Q1 nello screenshot). |
| D6 | `.exp` | `.items` ha `min-width: 330px` in una banda a tutta larghezza; il titolo da 22 px va su due righe in ~540 px. | Una banda alta 230 px per un dato secondario. |
| D7 | Griglia | Un solo punto di rottura (1100 px). Tra 1100 e 1440 le larghezze fisse (menu 256, «Tocca a te» 320, barre 330) si mangiano lo spazio; tutto il resto è in frazioni della `g-12`. | La pagina è stata verificata solo a 1440 e a 390: la fascia 1200–1439, quella del responsabile, non ha regole. |
| D8 | Scala tipografica | Tredici grandezze in uso (10,5 · 11 · 12 · 12,5 · 13 · 13,5 · 14 · 15 · 16 · 17 · 20 · 22 · 34). | Gerarchia piatta: tra 12,5 e 15 non si distingue un livello dall'altro. |
| D9 | `.btn` | `min-height: 42px`. | Sotto i 44 px richiesti per i bersagli. |

---

### 1. Il percorso del pilota: il tracciato a sigilli

#### Idea guida

**Il lavoro scorre sulle tratte; si passa da una fase all'altra solo con un sigillo, cioè con l'atto di una persona.**

È il vincolo del progetto reso visibile: «gli agenti propongono, il codice calcola, le persone decidono». Una roadmap generica mostra date e caselle spuntate; questa mostra quattro **tratte** di lavoro calcolato (che si riempiono con i fatti del motore) separate da **sigilli** (gli atti che chiudono ciascuna fase: abbinamenti decisi, profilo approvato dal comitato *e* verificato dall'auditor, mappa senza risultati da confermare, restituzione approvata). La fase degli indirizzi ha **due sigilli affiancati**, comitato e auditor: la regola delle due chiavi (sezione 27 del registro di metodo, migrazione 0037) si legge senza spiegazioni.

Tre tempi, tre registri di testo:

- **passato** (fatta): le *prove*, cioè i fatti e gli atti che la chiudono;
- **presente** (in corso): l'*avanzamento* della tratta e **chi deve agire**;
- **futuro** (da fare): *che cosa succederà* e chi lo farà.

Un segnaposto **«oggi»** sta sul fronte della tratta corrente, come la linea di oggi in un cronoprogramma. Dal segnaposto scende la **banda dell'azione** («Tocca a voi» / «Tocca a te»): l'azione è attaccata al punto del percorso in cui va compiuta.

#### Dove sta «Tocca a te»

**Dentro la stessa superficie del tracciato, in basso, a tutta larghezza, con una tacca che punta al segnaposto «oggi».** Non più una colonna a destra: la colonna fissa di 320 px è la causa di D1, e separava l'azione dal punto del percorso a cui appartiene.

Alternativa (non raccomandata): azione compatta nell'intestazione, a destra del titolo, al posto del bottone di approvazione. Guadagna ~70 px di altezza ma stacca di nuovo l'azione dal percorso e mette due primarie in competizione con l'approvazione. La raccomandazione resta la banda agganciata.

Conseguenza: nella fase di esito, per il comitato, **la banda contiene «Approva la restituzione»** (apre la stessa finestra di dialogo di oggi) e il bottone sparisce dall'intestazione. Una sola azione primaria per schermata.

#### Struttura e markup

```tsx
<section className="percorso" aria-labelledby="titolo-percorso"
  style={{ '--fronte': fronte } as CSSProperties}>          {/* 0..1, posizione di «oggi» sull'intero tracciato */}
  <header className="percorso-testa">
    <h2 id="titolo-percorso" className="eyebrow">Percorso del pilota</h2>
    <p className="percorso-dove mono">fase 2 di 4 · Indirizzi</p>
  </header>

  <ol className="tracciato">
    {fasi.map((f, i) => (
      <li className={`tratta tratta-${f.stato}${anticipo ? ' tratta-anticipo' : ''}`}
          aria-current={corrente ? 'step' : undefined}
          style={{ '--progresso': progresso } as CSSProperties}>
        {corrente && <span className="oggi" aria-hidden="true">oggi</span>}
        <span className="tratta-linea" aria-hidden="true"><i /></span>
        <span className="sigilli" aria-hidden="true">{/* 1 sigillo; 2 per Indirizzi: «C» e «A» */}</span>
        <div className="tratta-testa">
          <span className="tratta-numero mono">{i + 1}</span>
          <b>{TITOLI_FASI[f.codice]}</b>
          <span className={`chip-fase chip-fase-${statoMostrato}`}>{ETICHETTA_STATO}</span>
        </div>
        <p className="tratta-prova">{prova}</p>          {/* il fatto: passato = prova, presente = avanzamento, futuro = che cosa */}
        <p className="tratta-sigillo">{sigillo}</p>      {/* l'atto: fatto, atteso da chi, o che verrà */}
        <span className="visually-hidden">{frase completa, vedi testi}</span>
      </li>
    ))}
  </ol>

  <div className={`percorso-azione${attesa ? ' percorso-azione-attesa' : ''}`}
       role="group" aria-labelledby="titolo-azione">
    <div className="azione-testo">
      <span className="eyebrow">{eyebrow}</span>
      <h3 id="titolo-azione">{tocca.titolo}</h3>
      <p>{tocca.testo}</p>
    </div>
    <div className="azione-comando">{/* Link o button esistenti; «schermata in arrivo» come oggi */}</div>
  </div>

  {/* Solo sotto i 640 px di contenitore: dettaglio della fase corrente e prove di tutte le fasi */}
  <div className="percorso-dettaglio" aria-hidden="true">…</div>
  <details className="percorso-prove"><summary>Le prove di tutte le fasi</summary>…</details>
</section>
```

`BarraPercorso.tsx` resta il componente; i testi nuovi vanno in `azioni.ts` (funzioni `provaFase`, `sigilloFase`, `chiAgisce`, `progressoFase`), accanto a `TITOLI_FASI`. Nessun dato nuovo dall'API: tutto si ricava da `Percorso.fasi[*].fatti`.

#### Avanzamento delle tratte (solo rapporti tra fatti, nessuna soglia nuova)

| Fase | `progresso` (0–1) |
|---|---|
| avvio | `attivita > 0 ? (attivita − in_attesa_di_abbinamento) / attivita : 0` |
| indirizzi | `profilo_proprio ? 1 : [proposta presente, proposta.approvata, proposta.verificata].filter(Boolean).length / 3` |
| verifica | `risultati > 0 && da_confermare !== null ? (risultati − da_confermare) / risultati : 0` |
| esito | `approvazione !== null ? 1 : 0` |

Fatta = 1, da fare = 0 a prescindere. **Fronte** (`--fronte`, posizione di «oggi» e della tacca) = `(indice_corrente + clamp(progresso, 0.08, 0.92)) / 4`.

Una fase **in anticipo** è una fase `in_corso` che viene *dopo* `fase_corrente` (nei dati di prova: verifica mentre gli indirizzi sono in corso). Si riempie come le altre ma con il riempimento attenuato e il chip «in anticipo»: i suoi risultati sono provvisori.

#### Token nuovi (in `:root` di `stile.css`)

```css
/* Tracciato del percorso */
--tracciato-linea: 6px;            /* spessore della tratta */
--tracciato-binario: #E4E9F1;      /* = --bordo-superficie: binario vuoto */
--tracciato-futuro: #C5CFDD;       /* tratteggio delle tratte da fare (grigio di superficie, non colore di marca) */
--sigillo: 22px;                   /* diametro; 20px quando sono due */
--oggi-altezza: 22px;
```

Colori usati, tutti già esistenti: tratta fatta `--navy`; riempimento in corso `--teal-ink` (#007272, 5,9:1 sul bianco: il teal #00B4B4 su bianco è 2,5:1 e non basta per un elemento grafico, WCAG 1.4.11); punto interno del sigillo atteso `--teal`; banda azione `--navy`, attesa `--tela`.

#### Valori

```css
.percorso { container: percorso / inline-size; background: #fff; border: 1px solid var(--bordo-superficie);
  border-radius: var(--r-superficie); box-shadow: var(--ombra-1); padding: 16px 24px 0; overflow: hidden;
  margin-bottom: var(--gap); }
.percorso-testa { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 6px; }
.percorso-dove { font-size: var(--t-xs); color: var(--stone-ink); }

.tracciato { list-style: none; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-template-rows: var(--oggi-altezza) 10px var(--tracciato-linea) 14px auto auto auto; column-gap: 6px; }
.tratta { grid-row: 1 / -1; display: grid; grid-template-rows: subgrid; position: relative; min-width: 0; padding-right: 20px; }
/* righe: 1 oggi · 2 aria · 3 linea · 4 aria · 5 testa · 6 prova · 7 sigillo (la subgrid allinea le righe fra le quattro tratte) */

.tratta-linea { grid-row: 3; margin-right: -20px; height: var(--tracciato-linea); border-radius: 99px;
  background: var(--tracciato-binario); overflow: hidden; }
.tratta-linea i { display: block; height: 100%; background: var(--teal-ink); border-radius: inherit;
  transform-origin: left; transform: scaleX(var(--progresso)); }
.tratta-fatta .tratta-linea, .tratta-fatta .tratta-linea i { background: var(--navy); }
.tratta-anticipo .tratta-linea i { opacity: .45; }
.tratta-da_fare .tratta-linea { background: none; height: 0; margin-top: 2px; border-top: 2px dashed var(--tracciato-futuro); }

.sigilli { grid-row: 2 / 5; justify-self: end; align-self: center; margin-right: -31px; z-index: 1; display: flex; }
.sigillo { width: var(--sigillo); height: var(--sigillo); border-radius: 50%; display: grid; place-items: center;
  background: #fff; border: 1.5px solid var(--tracciato-futuro); font-family: var(--f-mono); font-size: 11px; font-weight: 700; color: var(--stone-ink); }
.sigillo + .sigillo { margin-left: -6px; }                        /* due sigilli affiancati: C e A */
.sigillo-posto  { background: var(--navy); border-color: var(--navy); color: #fff; }   /* con segno di spunta SVG 12px */
.sigillo-atteso { border: 2px solid var(--teal-ink); color: var(--teal-ink); box-shadow: 0 0 0 4px #E6FAFA; }

.oggi { grid-row: 1; justify-self: start; position: relative; left: calc(var(--progresso-oggi) * 100%);
  transform: translateX(-50%); background: var(--navy); color: #fff; font-family: var(--f-mono); font-size: 11px;
  font-weight: 600; letter-spacing: .08em; text-transform: uppercase; padding: 3px 9px; border-radius: 99px; line-height: 16px; }
.oggi::after { content: ""; position: absolute; left: 50%; top: 100%; width: 1.5px; height: 10px; background: var(--navy); }
/* --progresso-oggi = clamp(progresso, .08, .92); vicino ai bordi translateX(0) o (-100%) per non uscire dalla tratta */

.tratta-testa { grid-row: 5; display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.tratta-numero { font-size: var(--t-xs); color: var(--stone-ink); }
.tratta-testa b { font-size: var(--t-l); font-weight: 600; color: var(--navy); letter-spacing: -.015em; }
.tratta-prova { grid-row: 6; font-size: var(--t-s); line-height: 1.4; color: var(--obsidian); margin-top: 4px; }
.tratta-sigillo { grid-row: 7; font-size: var(--t-xs); font-family: var(--f-mono); color: var(--stone-ink); margin: 6px 0 18px;
  display: flex; gap: 6px; align-items: flex-start; }
.tratta-da_fare .tratta-prova { color: var(--slate); }
.tratta[aria-current="step"] .tratta-testa b { color: var(--navy); }   /* la corrente si distingue per «oggi» e linea, non per un bordo */

.chip-fase { font-family: var(--f-mono); font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 99px; white-space: nowrap; }
.chip-fase-fatta    { background: #EEF2F9; color: var(--navy); }
.chip-fase-in_corso { background: #E6FAFA; color: var(--teal-ink); }
.chip-fase-anticipo { background: #FEF3C7; color: var(--amber-ink); }
.chip-fase-da_fare  { background: transparent; color: var(--stone-ink); border: 1px dashed var(--tracciato-futuro); }

.percorso-azione { position: relative; margin: 0 -24px; padding: 16px 24px 18px; background: var(--navy); color: #fff;
  display: grid; grid-template-columns: minmax(0, 1fr) auto; column-gap: 24px; align-items: center; }
.percorso-azione::before { content: ""; position: absolute; top: -8px;
  left: calc(24px + (100% - 48px) * var(--fronte) - 8px); width: 16px; height: 16px; background: inherit;
  transform: rotate(45deg); border-radius: 3px; }                 /* la tacca: punta a «oggi» */
.percorso-azione h3 { color: #fff; font-size: var(--t-xl); margin: 2px 0; }
.percorso-azione p { color: #CBD5E1; font-size: var(--t-m); max-width: 76ch; }
.percorso-azione .eyebrow { color: #7EE0E0; }
.percorso-azione .btn-pill { background: #fff; color: var(--navy); min-height: 44px; }
.percorso-azione-attesa { background: var(--tela); color: var(--obsidian); border-top: 1px solid var(--bordo-superficie); }
.percorso-azione-attesa h3 { color: var(--navy); font-size: var(--t-l); }
.percorso-azione-attesa p { color: var(--slate); }
.percorso-azione-attesa .eyebrow { color: var(--teal-ink); }
.percorso-azione .errore { color: #FECDD3; grid-column: 1 / -1; }  /* su navy: 10:1 */
.percorso-dettaglio, .percorso-prove { display: none; }
```

Altezza risultante a 1280–1440: testa ~22 + tracciato ~130 + banda ~84 = **≤ 230 px** (oggi 247 + 230 della sperimentazione).

#### Testi esatti

Titoli delle fasi invariati: «Avvio», «Indirizzi», «Verifica», «Esito». I sottotitoli attuali (`SOTTOTITOLI_FASI`) escono dal tracciato: il loro contenuto vive nella riga «prova» delle fasi da fare. `{n}` sono i fatti dell'API; i plurali seguono il numero (1 mansionario / 2 mansionari).

Chip di stato: «fatta» · «in corso» · «in anticipo» · «da fare».

**Avvio**

| Stato | Prova | Sigillo |
|---|---|---|
| da fare (`documenti` = 0) | Nessun mansionario caricato | Poi: il revisore decide gli abbinamenti |
| in corso | {documenti} mansionari · {in_attesa_di_abbinamento} task in attesa di abbinamento | Attende: il revisore, sui lotti |
| fatta | {documenti} mansionari · {occorrenze} task nella mappa | ✓ Abbinamenti applicati |

Nota di voce: «task», non «attività» (termine fisso di `voce-e-testi.md`). Correggere anche `azioni.ts`, dove oggi compare «attività in attesa di abbinamento».

**Indirizzi** (sigilli «C» comitato, «A» auditor)

| Stato | Prova | Sigillo |
|---|---|---|
| da fare | Il questionario del comitato calibra i pesi di D | Poi: approvazione del comitato e verifica dell'auditor |
| in corso, nessuna proposta | Mappa con i pesi di default NEARTECH | Attende: il comitato, sul questionario |
| in corso, proposta da approvare | Profilo di pesi proposto dal questionario | Attende: il comitato, poi l'auditor |
| in corso, approvata non verificata | Profilo approvato dal comitato | ✓ Comitato · attende: l'auditor |
| fatta | Profilo di pesi del comitato in vigore · `{profilo_proprio}` (mono, primi 8 caratteri) | ✓ Comitato · ✓ Auditor |

**Verifica**

| Stato | Prova | Sigillo |
|---|---|---|
| da fare | I revisori controllano a campione le classificazioni | Poi: nessun risultato da confermare |
| in anticipo | {risultati} risultati provvisori · {da_confermare} da confermare | Si chiude dopo gli indirizzi |
| in corso, `risultati` = 0 | Ricalcolo con il nuovo profilo in attesa | Attende: l'amministratore NEARTECH |
| in corso, `da_confermare` null | {risultati} risultati · stabilità da misurare | Attende: la soglia di stabilità del comitato |
| in corso | {risultati} risultati · {da_confermare} da confermare · {quota}% giudizi di persona | Attende: i revisori |
| fatta | {risultati} risultati stabili · {quota}% giudizi di persona | ✓ Nessun risultato da confermare |

**Esito**

| Stato | Prova | Sigillo |
|---|---|---|
| da fare | Il comitato approva la restituzione come atto | Poi: atto nel registro, con impronta |
| in corso | Mappa pronta da approvare | Attende: il comitato |
| fatta | Atto #{approvazione} nel registro · impronta `{impronta[0:8]}…` | ✓ Restituzione approvata |

**Testa del tracciato:** «Percorso del pilota» (eyebrow) · a destra «fase {i} di 4 · {Titolo}»; a percorso concluso «percorso concluso · atto #{approvazione}».

**Frase per lettori di schermo** (in ogni `li`): «Fase {i} di 4, {Titolo}: {stato}. {Prova}. {Sigillo}.», con «in corso in anticipo, risultati provvisori» per la fase in anticipo.

**Banda dell'azione.** Titoli e testi restano quelli di `azione()` in `azioni.ts`. Cambia l'eyebrow:

- azione richiesta, comitato guida: «Tocca a voi» (il comitato è un *voi*, `voce-e-testi.md`);
- azione richiesta, persona (revisore, auditor, amministratore): «Tocca a te»;
- nessuna azione: «In attesa · ora agisce {chi}», dove `chiAgisce(percorso)` restituisce: avvio senza documenti → «l'amministratore NEARTECH»; avvio con task in attesa → «il revisore»; indirizzi senza proposta o non approvata → «il comitato guida»; approvata non verificata → «l'auditor»; verifica senza risultati → «l'amministratore NEARTECH»; verifica → «i revisori»; esito non approvato → «il comitato guida». A percorso concluso l'eyebrow è «Percorso concluso».
- Esito, comitato: bottone «Approva la restituzione» nella banda (stessa finestra di dialogo).

#### Comportamento per larghezza

Il tracciato reagisce alla **propria** larghezza (container query su `percorso`), non alla finestra: così regge identico nella panoramica, in una colonna o in proiezione.

| Finestra | Larghezza del contenitore | Comportamento |
|---|---|---|
| 1440 × 900 | ~1104 px (menu 256, margini 40) | Tracciato orizzontale, tratte da ~265 px; prova su una riga; banda su due colonne (testo / bottone). |
| 1280 × 800 (≈ il responsabile a 100%) | ~976 px (menu 240, margini 32) | Tracciato orizzontale, tratte da ~230 px; prova al massimo su due righe (la subgrid allinea le righe delle quattro tratte); banda su due colonne. Nessuna parola da sola su una riga. |
| contenitore 640–879 px (finestre 1024–1199) | | Come sopra; la banda va a una colonna, bottone sotto il testo, allineato a sinistra. |
| 390 × 844 (contenitore < 640 px) | ~358 px | Tracciato **compatto**: quattro tratte orizzontali da ~80 px con linea, sigilli e solo numero + titolo (`b` a 14 px, chip nascosto, stato detto dall'icona del sigillo); spariscono le righe prova e sigillo nelle tratte. Sotto, `.percorso-dettaglio` mostra prova e sigillo della fase corrente (e di quella in anticipo, se c'è); poi la banda, bottone a tutta larghezza da 48 px; in fondo `<details>` «Le prove di tutte le fasi». Il segnaposto «oggi» resta. |

```css
@container percorso (max-width: 879px) {
  .percorso-azione { grid-template-columns: 1fr; row-gap: 12px; }
  .azione-comando { justify-self: start; }
}
@container percorso (max-width: 639px) {
  .percorso { padding: 14px 16px 0; }
  .tracciato { grid-template-rows: var(--oggi-altezza) 10px var(--tracciato-linea) 12px auto; }
  .tratta { padding-right: 12px; }
  .tratta-prova, .tratta-sigillo, .chip-fase, .tratta-numero { display: none; }
  .tratta-testa b { font-size: 14px; }
  .tratta-testa { margin-bottom: 14px; }
  .percorso-dettaglio { display: block; border-top: 1px solid var(--bordo-superficie); padding: 12px 0; }
  .percorso-prove { display: block; padding: 0 0 14px; }
  .percorso-azione { margin: 0 -16px; padding: 16px; }
  .percorso-azione .btn-pill { width: 100%; min-height: 48px; }
}
```

`.percorso-dettaglio` è `aria-hidden` perché le stesse informazioni sono già nella frase nascosta di ogni `li`; `<details>` è navigabile da tastiera.

#### Stati

| Stato | Resa |
|---|---|
| Caricamento | La pagina mostra già «Carico la mappa…». Se il percorso arriva separato: stessa superficie ad altezza riservata (230 px a ≥ 640, 300 a < 640, nessuno spostamento del layout), quattro binari `--tracciato-binario`, due righe di testo grigie per tratta, `aria-busy="true"` e testo nascosto «Carico il percorso…». Nessuna animazione infinita. |
| Vuoto | Nessun documento: tutte le tratte tratteggiate, «oggi» all'inizio di Avvio, prova «Nessun mansionario caricato». Amministratore: banda «Tocca a te» con l'azione esistente; altri ruoli: «In attesa · ora agisce l'amministratore NEARTECH». |
| Errore | Errore di pagina invariato. Errore del ricalcolo dentro la banda, `role="alert"`, colore #FECDD3 su navy: «Ricalcolo non riuscito. Riprova tra qualche istante.» |
| Parziale | Due fasi in corso: la corrente ha «oggi», la successiva riempimento attenuato e chip «in anticipo», prova «… risultati provvisori …», sigillo «Si chiude dopo gli indirizzi». |
| Successo | Tutte e quattro navy, cinque sigilli posti, «oggi» sparisce; banda in variante attesa con eyebrow «Percorso concluso», titolo «Restituzione approvata», testo «Atto #{n} nel registro. Il percorso del pilota è concluso.» |
| Permesso | Chi non ha azioni (auditor fuori dalla verifica, rappresentante dei lavoratori) vede la banda in attesa e chi agisce; nessun bottone finto. «schermata in arrivo» resta come chip quando `pronta` è falso. |
| In lavorazione | «Ricalcolo la mappa…» con bottone disabilitato e `aria-busy`; al termine i dati si aggiornano e il tracciato anima solo il cambiamento (sotto). |

#### Movimento

Due soli elementi animati (regola `excessive-motion`), solo `transform` e `opacity` (`transform-performance`), con il token `--ease` esistente:

1. **Al primo montaggio** le tratte si riempiono: `scaleX(0 → progresso)`, 520 ms, ritardo 60 ms per tratta (`stagger-sequence`); poi «oggi» e la tacca compaiono: `opacity 0→1`, `translateY(4px→0)`, 200 ms, ritardo 360 ms. Non si ripete ai successivi aggiornamenti dei dati.
2. **Quando cambia un fatto** (dopo un ricalcolo o un atto): la tratta interessata passa al nuovo `scaleX` in 320 ms; un sigillo che diventa posto riempie lo sfondo in 180 ms e la spunta entra con `scale(.6→1)` in 160 ms. È il solo momento in cui la piattaforma «celebra» un atto, ed è causa-effetto (`motion-meaning`).

Con `prefers-reduced-motion: reduce` nessuna transizione: lo stato finale compare subito (la regola globale in `stile.css` già lo garantisce; non aggiungere eccezioni). Nessun impulso continuo sul sigillo atteso: lo distingue l'anello, non il movimento.

#### Accessibilità

- `<ol>` con `aria-current="step"` sulla fase corrente; frase completa nascosta per ogni fase.
- Stato mai solo colore: chip testuale + forma della linea (piena, parziale, tratteggiata) + forma del sigillo (spunta, anello, vuoto) + testo del sigillo.
- Contrasti: teal-ink su bianco 5,9:1; navy su bianco 14:1; stone-ink #526175 su bianco 6,1:1; ambra-ink su #FEF3C7 6,9:1; #CBD5E1 su navy 9,6:1.
- Bersagli: bottoni ≥ 44 px (portare `.btn` a `min-height: 44px` in tutta la piattaforma, D9).

---

### 2. Perché a 100% «c'è qualcosa che non va» e come si corregge

#### Diagnosi: che cosa cambia tra 100% e 67%

| Aspetto | 100% (~1300 × 670 px CSS) | 67% (~1970 × 1010 px CSS) |
|---|---|---|
| Larghezze fisse (menu 256 + «Tocca a te» 320 + barre 330) | ~70% della larghezza: le parti in `fr` restano strette (D1, D6) | ~46%: le frazioni respirano |
| Testo nelle tessere delle fasi | ~78 px, parola per riga | ~240 px, una riga |
| Inizio della mappa | ~630 px: **sotto la piega** | ~575 su 1010: la mappa entra nella prima schermata |
| Disegno della mappa | ~517 px; etichette a 8,5 px, assi a 8,9 px | ~900 px; etichette a ~15 px CSS, la mappa domina la colonna |
| Rapporto mappa / colonna KPI | 7:5 fisso, KPI a ~190 px l'uno con etichette su due righe | 7:5 fisso, KPI larghi e vuoti |

Il 67% non «sistema» la scala: allarga la finestra in px CSS, così le parti fisse pesano meno e la mappa sale nella prima schermata. Da qui le tre cause di sistema:

1. **Ordine verticale sbagliato per lo schermo reale**: due bande di processo (fasi 247 px + sperimentazione 230 px) prima della risposta che il titolo promette.
2. **Larghezze fisse in un layout a frazioni**, con un solo punto di rottura a 1100 px: la fascia 1200–1439 non è progettata.
3. **Mappa scalata dal `viewBox`**: il testo del disegno cambia grandezza con la colonna invece di restare in px reali.

A queste si aggiunge la scala tipografica frammentata (D8), che toglie gerarchia proprio quando lo spazio è poco.

#### Correzioni di sistema

**A. Ordine della panoramica.** Intestazione → tracciato (≤ 230 px) → corpo a due colonne: **mappa** a sinistra; a destra KPI, **sperimentazione compatta**, inviti → ruoli a tutta larghezza. La banda «Sperimentazione» lascia la larghezza piena: è un fatto della verifica e sta accanto alla mappa che spiega.

Sperimentazione compatta nella colonna destra (stessa superficie `.card`, padding 18 px):
- riga 1: anello da 64 px (spessore 8, testo mono 14 px) + titolo `h3` a 16 px («3 giudizi su 100 vengono dalle vostre persone»);
- riga 2: le otto barre a tutta larghezza della card, `grid-template-columns: repeat(8, minmax(0, 1fr))`, altezza 36 px, nessun `min-width`;
- riga 3: testo a 13 px, solo «Ancora senza giudizi di persona: k1, k3, r, d2, d3, d4.»; la frase esplicativa lunga va in un `<details>` «Come si aggiorna», così il testo resta disponibile senza occupare spazio.

**B. Griglia e larghezze.**

```css
:root {
  --larghezza-menu: 240px;                         /* 256px da 1440 in su */
  --margine-pagina: clamp(20px, 2.5vw, 40px);      /* 32 a 1280, 36 a 1440 */
  --gap: clamp(16px, 1.4vw, 20px);                 /* sostituisce 18px e 12px sparsi */
  --larghezza-contenuto: 1360px;                   /* proiettore e schermi larghi: niente righe infinite */
  --colonna-laterale: clamp(320px, 27vw, 392px);   /* KPI, sperimentazione, inviti */
}
@media (min-width: 1440px) { :root { --larghezza-menu: 256px; } }

.app { grid-template-columns: var(--larghezza-menu) minmax(0, 1fr); }
.main { padding: 32px var(--margine-pagina) 64px; }
.main-contenuto { max-width: var(--larghezza-contenuto); margin-inline: auto; }   /* nuovo involucro in Guscio */
.corpo-panoramica { display: grid; gap: var(--gap);
  grid-template-columns: minmax(0, 1fr) var(--colonna-laterale); align-items: start; }
.colonna-laterale { display: grid; gap: var(--gap); }
```

Larghezze risultanti: a 1280 contenuto 976 px, colonna laterale 346, mappa (card) 610; a 1440 contenuto 1104, colonna 389, mappa 695. Le larghezze fisse spariscono: «Tocca a te» è nel tracciato, le barre non hanno più `min-width`.

**C. Punti di rottura sistematici** (sostituiscono l'unico a 1100; `breakpoint-consistency`):

| Fascia | Finestra | Regole |
|---|---|---|
| ampia | ≥ 1440 | menu 256; corpo a due colonne |
| media | 1200–1439 | menu 240; corpo a due colonne; KPI in coppia |
| stretta | 1024–1199 | menu 240; corpo a **una** colonna: mappa a tutta larghezza, sotto la colonna laterale come griglia `repeat(auto-fit, minmax(280px, 1fr))` |
| tablet e telefono | < 1024 | menu come barra in alto con pillole (comportamento attuale, spostato da 1100 a 1023) |
| telefono | < 768 | margini 16 px; KPI in coppia restano; ruoli in tabella scorrevole |

Il tracciato non usa questi punti: segue la sua container query (sezione 1).

**D. Mappa in px reali.** `MappaQuadranti` misura la propria larghezza (`ResizeObserver` sul contenitore) e la passa come `larghezza`; `altezza = clamp(320, round(larghezza × 0,62), 520)`; il `viewBox` coincide con le dimensioni reali, quindi il testo non scala più. Grandezze nel disegno: etichette dei quadranti 12 px mono 600; conteggi 22 px; assi 12 px; raggio dei punti 5 (6 se attivo); anello incerto 10. Etichette con alone bianco (`paint-order: stroke; stroke: #fff; stroke-width: 3px; stroke-linejoin: round`) così restano leggibili quando un punto ci passa sotto (D5). Risultato: a 1280 disegno ~562 × 348, a 1440 ~647 × 401, testo sempre ≥ 12 px.

**E. Scala tipografica** (`font-scale`): sette grandezze, rapporto ~1,15–1,25.

```css
--t-xs: 11px;    /* solo etichette mono: eyebrow, chip, stati, assi */
--t-s: 13px;     /* testo secondario, prove del tracciato, inviti */
--t-m: 14px;     /* corpo dell'interfaccia */
--t-l: 16px;     /* h3, titoli delle fasi */
--t-xl: 18px;    /* titolo della banda dell'azione */
--t-2xl: 22px;   /* h2 di sezione */
--t-3xl: clamp(28px, 1.4vw + 14px, 34px);   /* h1 e numero dei KPI: 32 a 1280, 34 da 1440 */
```

Da eliminare: 10,5 · 12 · 12,5 · 13,5 · 15 · 17 · 20 (ognuna va alla grandezza più vicina della scala). Corpo minimo sul telefono 14 px per l'interfaccia, 16 px nei campi di testo.

**F. Bilancio verticale** (regola di progetto, verificabile): a 1280 × 720 il **disegno della mappa comincia entro 470 px** dall'alto della finestra; a 1440 × 900 la card della mappa comincia entro 400 px. Conto a 1280: intestazione ~110 + tracciato ~230 + gap 18 + titolo e nota della mappa ~80 = ~438.

**G. Bottoni**: `.btn { min-height: 44px; }` ovunque.

---

### Regole e risultati della skill `ui-ux-pro-max` usati

- `ux` «Progress Indicators»: indicatore di passi con «passo 2 di 4» → testa «fase 2 di 4 · Indirizzi» e `aria-current="step"`.
- `ux` «Active State»: posizione corrente indicata visivamente → segnaposto «oggi» e tacca, non solo un bordo.
- `ux` «Text Reflow and Spacing» (critica) ed «Essential Text Truncation» (critica): niente riquadri fissi che spezzano il testo, niente troncamenti → tratte senza larghezze fisse, prova su ≤ 2 righe con subgrid, dettaglio completo su telefono.
- `ux` «Container Width» / `container-width` / `line-length`: larghezza massima del contenuto (1360) e testo della banda a 76ch.
- `breakpoint-consistency`, `mobile-first`, `horizontal-scroll`, `content-priority` (quick reference §5): fasce sistematiche e, sul telefono, prima la fase corrente e l'azione.
- `font-scale`, `weight-hierarchy`, `color-not-decorative-only`, `color-accessible-pairs` (§6): scala a sette grandezze, stato con testo + forma, teal-ink al posto del teal per gli elementi grafici.
- `ux` «Reduced Motion», «Excessive Motion», «Transform Performance», `stagger-sequence`, `motion-meaning`, `layout-shift-avoid` (§7): due sole animazioni, `transform`/`opacity`, sfalsamento 60 ms, nulla con riduzione del movimento, altezza riservata in caricamento.
- `primary-action` (§4): una sola primaria per schermata → l'approvazione entra nella banda.
- Stile `data-dense-dashboard`: preso solo come limite (griglia, KPI, tabelle scorrevoli); scartati padding 8–12 px e testo a 12 px, troppo fitti per un uso in riunione e in proiezione.
- Ricerche senza risultato utile: `"timeline roadmap milestone" --domain chart` (restituisce il grafico a linee, non pertinente) e `"responsive grid layout" --stack react` (nessun risultato; il ritentativo ha dato solo regole generali di React). Per tracciato a sigilli e container query la direzione è mia, non della skill.

---

### Criteri di accettazione (da verificare nel browser)

Dati di prova ACME S.p.A., come comitato guida salvo dove indicato; zoom del browser al 100%.

1. **1280 × 800 e 1300 × 670.** Nessuna parola da sola su una riga nel tracciato; ogni riga «prova» occupa al massimo due righe; le righe testa / prova / sigillo sono allineate alla stessa altezza nelle quattro tratte (subgrid).
2. Il testo di ogni tratta comincia allineato all'inizio della sua linea; nessuna tratta ha più di 24 px di vuoto sotto l'ultima riga.
3. Le quattro tratte formano una linea continua interrotta solo dai sigilli; Avvio piena navy; Indirizzi parziale in teal-ink con «oggi» sul fronte; Verifica attenuata con chip «in anticipo»; Esito tratteggiata. La fase Indirizzi mostra due sigilli, «C» e «A».
4. La tacca della banda punta allo stesso punto di «oggi» (scarto orizzontale ≤ 8 px).
5. Eyebrow della banda: «Tocca a voi» come comitato; «Tocca a te» come revisore in verifica; «In attesa · ora agisce …» quando non c'è azione. Nessun testo dell'interfaccia contiene «attività» al posto di «task».
6. Altezza del tracciato (banda compresa) ≤ 240 px a 1280 e a 1440.
7. **Bilancio verticale:** a 1280 × 720 l'SVG della mappa comincia entro 470 px dall'alto; a 1440 × 900 la card della mappa comincia entro 400 px.
8. Nella mappa, misurato con gli strumenti del browser: etichette dei quadranti e degli assi ≥ 12 px di altezza resa a 1280, 1440 e a tutta larghezza su 1024–1199; nessuna etichetta illeggibile sotto un punto.
9. A 1280 la colonna laterale è 320–392 px; i due KPI stanno affiancati; la sperimentazione è nella colonna laterale e le otto barre non escono dalla card.
10. A 1920 × 1080 il contenuto non supera 1360 px di larghezza ed è centrato nello spazio a destra del menu.
11. A 1100 × 800 il menu laterale resta; mappa a tutta larghezza; colonna laterale sotto. A 1000 × 800 il menu diventa la barra in alto.
12. **390 × 844:** `document.documentElement.scrollWidth === innerWidth`; tracciato compatto con quattro titoli leggibili; dettaglio della fase corrente e banda prima della mappa; bottone della banda a tutta larghezza e alto ≥ 48 px; «Le prove di tutte le fasi» si apre da tastiera.
13. Tastiera: Tab raggiunge il bottone della banda con focus visibile; un lettore di schermo legge per ogni fase «Fase n di 4, …: stato. prova. sigillo.»; la fase corrente ha `aria-current="step"`.
14. Con `prefers-reduced-motion: reduce` le tratte compaiono già riempite, senza transizioni; senza la preferenza, il riempimento parte una volta al caricamento e non si ripete dopo un aggiornamento dei dati.
15. Come amministratore in verifica senza risultati: «Ricalcola la mappa» nella banda; durante il ricalcolo il bottone è disabilitato e dice «Ricalcolo la mappa…»; un errore compare nella banda, leggibile su navy.
16. Come comitato in fase di esito: «Approva la restituzione» compare solo nella banda (non più nell'intestazione) e apre la finestra di conferma esistente.
17. Tutti i bottoni della panoramica hanno altezza ≥ 44 px; nessun colore nuovo fuori dalla palette dell'identità (unico grigio aggiunto: `--tracciato-futuro` #C5CFDD per il tratteggio).
