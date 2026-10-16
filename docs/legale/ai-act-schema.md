# Schema sintetico dell'AI Act per la classificazione dei task

**Fonte:** Regolamento (UE) 2024/1689, testo ufficiale in GU L del 12.7.2024, 144 pagine, scaricato da EUR-Lex il 2026-10-16. Lo schema riporta solo ciò che serve a classificare i task. Per ogni decisione giuridica va consultato il testo originale e, prima dell'uso, il parere di un legale.

**Stato:** bozza. La classificazione legale dei task è una proposta del sistema. Va confermata da una persona competente prima di avere effetti.

## 1. Un punto di metodo: l'AI Act regola usi, non task

L'AI Act disciplina sistemi di IA e il modo in cui vengono usati. Non classifica un task in sé. Il rischio legale di un task dipende quindi dall'uso che si farebbe dell'IA su quel task. Lo stesso task può essere a rischio se l'IA serve a valutare le persone che lo svolgono, e non esserlo se l'IA lo supporta senza influire su decisioni individuali.

Per questo il sistema classifica ogni coppia **task × uso ipotizzato dell'IA**, e non il task da solo.

## 2. Pratiche vietate (art. 5)

Rilevanti per il lavoro:

- **Inferenza delle emozioni nei luoghi di lavoro** (art. 5, par. 1, lett. f): vietata la messa in servizio o l'uso di sistemi che deducono le emozioni di una persona nel lavoro. Eccezioni: motivi medici o di sicurezza.

Se un task prevede di valutare lo stato emotivo dei lavoratori con un sistema di IA, l'uso è vietato. Il task può restare nel dataset, ma l'uso va marcato come non ammesso.

## 3. Sistemi ad alto rischio: lavoro e gestione del personale (Allegato III, punto 4)

Testo, in sintesi:

- **(a) Selezione e reclutamento:** sistemi usati per il reclutamento o la selezione, per pubblicare annunci mirati, per analizzare e filtrare le candidature, per valutare i candidati.
- **(b) Decisioni sul rapporto di lavoro:** sistemi usati per prendere decisioni che incidono sulle condizioni del rapporto di lavoro, su promozioni o cessazioni, per **assegnare compiti in base al comportamento individuale o a tratti personali**, o per **monitorare e valutare le prestazioni e il comportamento** delle persone.

Regola di lettura: il punto 4 riguarda decisioni e valutazioni su persone. Un sistema che supporta un task senza valutare le persone non rientra di per sé in questa categoria.

## 4. Esenzione dal rischio elevato (art. 6, par. 3)

Un sistema dell'Allegato III non è ad alto rischio se non comporta un rischio significativo per salute, sicurezza o diritti fondamentali, cioè se non influisce in modo sostanziale sulle decisioni. Le condizioni previste:

- (a) compito procedurale ristretto;
- (b) miglioramento di un'attività umana già completata;
- (c) individuazione di schemi o scostamenti senza sostituire la valutazione umana;
- (d) compito preparatorio a una valutazione.

L'esenzione va documentata dal fornitore prima dell'uso. Non si applica se il sistema profila persone fisiche.

## 5. Obblighi del datore di lavoro che usa un sistema ad alto rischio (art. 26, par. 7)

Prima di usare un sistema ad alto rischio sul lavoro, il datore di lavoro informa i rappresentanti dei lavoratori e i lavoratori interessati. L'informazione segue le regole nazionali e dell'Unione sull'informazione dei lavoratori.

In Italia la legge 132/2025, art. 11, precisa e rafforza questo obbligo. Il testo italiano non è stato verificato su fonte ufficiale in questa versione dello schema.

## 6. Alfabetizzazione in materia di IA (art. 4)

Chi usa o supervisiona sistemi di IA deve avere un livello adeguato di alfabetizzazione. Il personale che fa revisione sul sistema rientra in questo obbligo.

## 7. Come classificare un task

Per ogni coppia task × uso ipotizzato, il sistema assegna una delle quattro categorie:

| Categoria | Condizione | Esito per il task |
|---|---|---|
| Vietato | Uso previsto dall'art. 5 | Uso non ammesso. Va registrato come pavimento legale massimo |
| Alto rischio | Uso rientra nell'Allegato III, punto 4, senza esenzione | Pavimento legale alto. Obbligo di informare i lavoratori |
| Esente | Uso rientra nel punto 4 ma soddisfa l'art. 6, par. 3 | Nessun pavimento obbligatorio. Esenzione da documentare |
| Non regolato | Uso fuori dall'Allegato III e non vietato | Nessun pavimento legale. Restano gli obblighi generali |

Ogni classificazione riporta: categoria, articolo di riferimento, motivazione in una frase, confidenza (alta, media, bassa), e il flag di revisione legale.

## 8. Cosa il sistema non fa

- Non dà pareri legali. Le classificazioni sono proposte, da confermare.
- Non classifica le persone: classifica task e usi.
- Non tratta il diritto nazionale come completo: la legge italiana è citata solo dove rilevante, e va verificata sul testo ufficiale.
