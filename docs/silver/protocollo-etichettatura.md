# Protocollo di etichettatura silver

**Stato:** dataset silver, non golden. Le etichette sono proposte di un modello linguistico, da verificare su un campione umano. Non vanno usate per decisioni organizzative né per la non-inferiorità del sistema, che richiede il golden del panel.

**Rubrica di riferimento:** sezione "La rubrica di valutazione" di `docs/piano-sviluppo-v2.md`, versione `bozza-2`. Ogni etichetta riporta la versione.

## 1. Confine tra N e D

- **N** misura la fattibilità tecnica: k1 (variabilità dell'input), k2 (giudizio), k3 (componente fisico-percettiva), più r come **requisito di affidabilità**.
- **D** misura ciò che deve restare umano per relazione, responsabilità e valore: d1, d2, d3, d4.
- **La riserva di legge entra in D tramite d2**, come fatto documentato con la fonte (articolo di legge). Non è un terzo asse. Un task tecnicamente automatizzabile ma riservato per legge ha N basso e D alto: il quadrante lo mostra senza modificare N.
- **Decisione aperta sulla rubrica di r:** i livelli 3 e 4 di r citano danni reputazionali e a diritti fondamentali. Sono giudizi normativi, non tecnici. Proposta: nel silver r misura solo l'affidabilità richiesta, e i riferimenti a diritti passano in d2. Da approvare dal comitato di governance.

## 2. Cosa il silver può etichettare

| Campo | Etichettabile dal testo del task? | Note |
|---|---|---|
| k1, k2, k3 | Sì | Dal testo del task |
| r | Sì, come affidabilità richiesta | Vedi decisione aperta sopra |
| d1, d2 | Sì, come proxy del panel | Da verificare su campione umano |
| fonte della riserva di legge (d2) | Sì, se citabile | Solo articolo e testo, mai un'opinione |
| **d3** senso del lavoro | **No** | Misura dei lavoratori, con survey |
| **d4** valore per il beneficiario | **No** | Misura degli utenti, con survey |

d3 e d4 restano **vuoti** nel silver. Un'etichetta prodotta dal modello su questi due campi sarebbe un'opinione inventata sulle persone. Il lato "valore" di D si ottiene solo dalle survey.

## 3. Regole sull'input

- Si incolla **solo il testo del task**, con un identificativo. Nessun nome di persona, codice fiscale, riferimento a un individuo o organigramma.
- Prima di incollare un documento in chat va verificato che non contenga dati personali, e che il contratto con il fornitore del modello consenta questo trattamento. Questo è un punto da chiudere prima del primo invio.
- Lotti da 10 task, con identificativi stabili.

## 4. Prompt per N (chat dedicata, senza D)

```
Sei un valutatore per la knowledge base dei task. Classifichi il task usando solo la rubrica allegata (asse N: k1, k2, k3, r). Non considerare valori etici, relazionali o di responsabilità: quelli non sono oggetto di questa valutazione.

Regole:
- Valuta solo il testo del task. Non immaginare contesti non scritti.
- Se un'informazione manca, usa il livello più basso compatibile e segnalalo in "incertezza".
- Per r valuta solo l'affidabilità richiesta, non i danni a diritti o alla reputazione.
- Rispondi solo con righe JSONL, una per task, nel formato indicato. Nessun testo fuori dal formato.

Formato: {"id":"...","k1":0-4,"k2":0-4,"k3":0-4,"r":0-4,"incertezza":"..."}
```

## 5. Prompt per D (chat dedicata, senza N)

```
Sei un valutatore per la knowledge base dei task. Classifichi il task usando solo la rubrica allegata (asse D, componenti d1 e d2). Non valutare la difficoltà tecnica del task: quella non è oggetto di questa valutazione.

Regole:
- d1 e d2 sono proxy di un panel umano: indica sempre la fiducia della valutazione.
- Per d2 indica se il task è riservato per legge a una figura abilitata, e cita l'articolo di legge. Se non sei sicuro della fonte, scrivi "fonte non verificata" e non attribuire la riserva.
- Non produrre valutazioni di d3 né d4: non sono misurabili dal testo del task.
- Rispondi solo con righe JSONL, una per task, nel formato indicato.

Formato: {"id":"...","d1":0-4,"d2":0-4,"riserva_legge":true|false,"fonte_riserva":"...","fiducia":"alta|media|bassa"}
```

## 6. Formato di ritorno e tracciabilità

Ogni riga viene salvata con i metadati, aggiunti da chi incolla le risposte:

```
{"id":"...","asse":"N|D","modello":"Gemini 4 Argon","versione_modello":"...","data":"AAAA-MM-GG","versione_rubrica":"bozza-2","prompt":"N-v1|D-v1","run":1, ...campi di risposta...}
```

Il modello non è versionato come un'API: la versione va scritta dalla chat, quando disponibile, e la data di ogni sessione va registrata.

**Stabilità.** Il piano chiede 5 campioni indipendenti per voce. Per il silver si fanno **3 run su 20 task** per misurare la variabilità della chat. È una deviazione dal piano, da registrare in `docs/metodologia-estensioni.md`.

## 7. Verifica incrociata

- Campione stratificato di 30 task, etichettato anche da un secondo modello.
- Accordo misurato con l'alfa di Krippendorff, per voce.
- I disaccordi vanno al curatore, che decide il caso.

**Attenzione:** l'accordo tra due modelli misura la coerenza, non la validità. Non sostituisce il panel.

## 8. Decisioni aperte

1. **r senza riferimenti a diritti**: confermare la proposta della sezione 1.
2. **Regola di d2 per riserva di legge**: quale livello minimo imporre quando la riserva è citata e verificata. È un valore di governance, non di codice.
3. **Invio di testi a un servizio di terzi**: confermare che il contratto e la policy consentano di incollare i documenti in chat.
4. **Campo fonte della riserva**: la fonte deve essere una norma verificabile. Chi verifica?

## Aggiornamento 2026-10-16

- Decisione su r: approvata come descritta in `docs/metodologia-estensioni.md`, sezione 4. Rubrica bozza-3.
- Campioni: 3 run per voce nel silver, deviazione registrata.
- d3 e d4: fuori dal silver, solo nel golden.
- Testi per Gemini: task canonici da `docs/silver/dataset/task-silver.jsonl`. Il pacchetto di istruzioni è in `docs/silver/pacchetto-gemini.md`.
- Verifica dei testi prima di ogni invio: solo titolo e nota di contesto, nessun nome di persona.
