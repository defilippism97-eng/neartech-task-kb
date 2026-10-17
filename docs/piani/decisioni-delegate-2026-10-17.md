# Decisioni prese su delega del responsabile del progetto (2026-10-17)

Il responsabile del progetto ha chiesto di portare il software a termine senza attendere sue decisioni ("Quando
tornerò qui non voglio trovarti bloccato in attesa di qualche mia decisione"). Le scelte sotto adottano le opzioni
raccomandate dalla mappa delle lacune della fase 6 e dalla proposta della fase di ascolto. Restano rivedibili dal
responsabile e dal comitato guida: ogni valore numerico sta in un parametro di governance, mai nel codice, e nei
dati di prova è etichettato come valore di prova. Restano sospese, come da indicazione del responsabile: verifica
della legge 132/2025, parere del DPO, verifica legale dello schema AI Act, scelta del fornitore di ospitalità.

## Flusso del pilota
1. **Ricalcolo dopo i giudizi delle persone.** Sempre disponibile all'amministratore tecnico il comando "Ricalcola
   la mappa" (job con atto). In più, ricalcolo automatico accodato dopo i giudizi, governato dal parametro
   `ricalcolo_automatico`; il job gira con un utente di servizio dedicato, con il solo permesso di ricalcolare, e
   l'atto cita gli atti che lo hanno causato.
2. **Chiusura della verifica e approvazione.** La verifica si chiude con il criterio del parametro
   `chiusura_verifica` (mai "zero instabili"). Il comitato può approvare la restituzione in ogni fase con risultati;
   l'atto registra fase, avvertenze e quota provvisoria.
3. **Restituzione approvata conservata**: storico, chiavi visibili, stampa e PDF dal browser.
4. **Giudizi dei revisori limitati alla propria organizzazione**: un giudizio sulla rubrica vale nel calcolo della
   sola organizzazione del revisore (un record per giudizio, con l'organizzazione); entra nel dataset condiviso
   solo con un atto NEARTECH di promozione.
5. **Task non abbinati (passo 3b)**: valutati per somiglianza con il parametro `somiglianza_task` (vicini, somiglianza
   minima, pesatura); valori marcati "derivato per somiglianza" con un valutatore dedicato.
6. **Ricalibrazione**: scostamento sistematico per voce fra persone e modello, con intervallo e minimo di giudizi da
   parametri; proposte al comitato (d1, d2) o a NEARTECH (k1–k3, r); mai applicate da sole.
7. **Lavoro dei revisori**: coda unica; distribuzione a rotazione dal meno certo; quota a doppia valutazione da
   parametro; disaccordo risolto da un terzo revisore con un atto.
8. **Motivazioni**: nessun testo fisso come motivazione di una persona; dove serve un testo di sistema, l'atto lo
   dichiara (`testo_di_sistema`).

## Indirizzi e governo
9. Il comitato può **adottare il profilo comune NEARTECH** come proprio (atto di adozione, poi verifica
   dell'auditor). Il questionario `bozza-1` resta come via rapida; la **fase di ascolto** diventa il metodo
   principale.
10. **Pavimento legale**: finché non ci sono pavimenti registrati il controllo si mostra "non verificabile", mai
    "superato".
11. L'auditor può **chiedere chiarimenti** (atto di rifiuto motivato); il comitato può **ritirare** un profilo in
    attesa; chi verifica deve essere una persona diversa da chi approva.
12. L'amministratore tecnico **non si assegna** ruoli di comitato, revisore o rappresentante.
13. **Rappresentante dei lavoratori**: vede solo le riduzioni di D causate da un profilo degli indirizzi; una
    sospensione non cambia numeri, ferma l'approvazione della restituzione finché il comitato risponde. Nomina con
    atto del comitato, ruolo assegnato dall'amministratore citando la nomina.

## Fase di ascolto del comitato (proposta del 2026-10-17, decisioni aperte 1–12)
14. Schede best–worst da quattro task; nel primo giro si stima solo il rapporto fra w_d1 e w_d2 (w_d3, w_d4 dal
    profilo di partenza); giro individuale; il comitato approva le schede; margine del comitato sulla stima con
    motivazione registrata e controllo dell'auditor; vincoli dei documenti come testo per la discussione; nessun
    uso fuori dall'organizzazione; limiti e scostamento di `bozza-1`, altri valori fissati dopo la prova di
    recupero sui dati di prova; nessuna enfasi per classi; `bozza-1` resta come via rapida; ripetizione su
    richiesta del comitato; intensità delle interviste pari a metà dello scostamento massimo.

## Accessi e amministrazione
15. **Credenziali**: oltre allo SSO, l'amministratore tecnico crea utenti con una password temporanea, mostrata una
    volta; al primo accesso l'utente la cambia. Password con hash lento, blocco dopo tentativi falliti, sessioni
    revocabili dal server, utenti disattivabili.
16. **Organizzazioni**: l'amministratore le crea dalla console; la creazione dello spazio (che richiede il ruolo
    proprietario) la esegue il lavoratore come job, non l'API.
17. **Console dell'amministratore**: piloti, profilo di ogni organizzazione, utenze per organizzazione, ruoli,
    costi, job, candidature, base di conoscenza.

## Base di conoscenza
18. Ruoli globali (amministratore, auditor) vedono tutto il dataset, con i piloti indicati dal codice; comitato e
    revisore vedono la copertura della propria organizzazione e i task che vi ricorrono.
19. Lo **stato di validazione** si deriva dai dati (giudizi di persona per voce), senza scritture.
20. I materiali di ricerca solo su file (prior O*NET, calibrazione, WORKBank) si mostrano come riferimenti, mai
    caricati come giudizi.

## Questionari d3/d4
21. Modello "urna": nessun legame conservato fra indirizzo, gettone e risposta; promemoria a tutti; risultati solo
    dopo la chiusura, inviati a tutti gli invitati; indirizzi cancellati dopo l'invio dei risultati.
22. Aggregazione: **mediana** sulla scala 0–4 (a parità il valore centrale superiore); `minimo_rispondenti_gruppo`
    = 5 come parametro comune che un'organizzazione può solo alzare; contenuto nel parametro versionato
    `questionario_d3d4`.
23. Giudizio di gruppo come giudizio di persona sull'occorrenza (`worker` per d3, `beneficiary` per d4), locale
    all'organizzazione; una campagna più recente sostituisce la precedente.
24. **Invio delle email** con un mittente intercambiabile: file locale in sviluppo e prova, SMTP configurabile in
    esercizio. Il fornitore resta da scegliere.

## Sito e prodotto
25. **Sito pubblico** alla radice, piattaforma sotto `/app`; candidature dei piloti in una tabella dedicata, con
    conservazione da parametro (proposta 12 mesi).
26. Caratteri **Inter + JetBrains Mono**; KPI evidenziato: avanzamento della sperimentazione.
27. Termini fissi: "amministratore NEARTECH" nei testi per il cliente, "Neartech" per il prodotto, "predefiniti"
    invece di "default".

## Costi e modelli
28. Prezzi del modello in dollari (`_usd_`), tetto di spesa mensile per organizzazione come parametro controllato
    prima di ogni avvio a pagamento; uso effettivo registrato accanto alla stima.
29. Nessun prompt v3 del Canonicalizer per il pilota: abbinamento per embedding e revisione cieca dei lotti.

## Reversibilità (richiesta del responsabile)
30. Tutto ciò che una persona inserisce si può **modificare o cancellare finché non passa alla fase successiva**:
    le bozze (documenti caricati prima della scomposizione, risposte e scelte prima dell'invio, campagne prima della
    spedizione, giudizi prima del ricalcolo che li usa) si cambiano liberamente. Dopo il passaggio, una correzione
    è un record nuovo o un atto di ritiro: lo storico non si cancella (regola "un record per ogni giudizio").

## Rinviate, con motivo
31. **RLS fra organizzazioni**: rinviata; con la catena del registro letta per intero un criterio per riga la
    romperebbe. L'isolamento resta nel motore (`richiedi`) con un test di negazione per ogni rotta.
32. **Ospitalità, SSO multi-fornitore, ambiente di prova in cloud**: si prepara un'immagine indipendente dal
    fornitore; la scelta resta del responsabile.
33. **Metodo `calcolo-nd-v3`** (riproducibilità fra reimportazioni): cambia i risultati, resta proposta.
