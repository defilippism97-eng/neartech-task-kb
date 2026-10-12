# Relazione di sintesi: stato della valutazione di N e D

Data: 2026-10-12. Stato: **preliminare**. Nessun peso, soglia o parametro di governance è approvato.

## 1. Cosa è costruito e caricato

- **Tassonomie:** O\*NET 31.0 (18.838 task), Atlante INAPP (10.572 nodi), ESCO 1.2.1 in italiano (16.978 nodi), con embedding bge-m3 per 46.388 nodi. Database PostgreSQL con pgvector su Neon, migrazioni 0001–0006.
- **Job description Dolce:** 36 ruoli, 530 occorrenze (ruolo × attività), caricate dalla proposta approvata con verifica dei passi sul testo.
- **Task canonici:** 384 proposti, 54 fusi dal Canonicalizer (confermate dal responsabile), 295 attivi, 35 aree di responsabilità ritirate perché non sono task.
- **Crosswalk verso le tassonomie:** 6.520 relazioni (esatte, più ampie, più strette, affini). Ogni task attivo ha un giudizio per schema, anche quando è "nessuna corrispondenza". I task senza corrispondenza restano nella KB con la loro origine.
- **Revisione del campione:** 40 relazioni, 36 OK, 2 parziali, 2 no. Precisione 90%, con intervallo di confidenza circa 81%–99%. Solo le 36 confermate sono validate.
- **Domanda preliminare (branch `ricerca/workbank`):** stima di k1, k2, k3, r per 3.083 task O\*NET di staff. Non calibrata.

## 2. Cosa serve per calcolare N

N = divario tra domanda e copertura, amplificato dalla criticità. Servono quattro elementi:

| Elemento | Stato | Cosa manca |
|---|---|---|
| **dₖ, domanda del task** | Disponibile per i task O\*NET di staff (3.083). Non per i 295 task Dolce direttamente. | Valutazione dei task Dolce con la rubrica, e rubrica v2 approvata. Oggi k1 e k3 sono su v1 per 1.226 task. |
| **cₖ(t), copertura tecnologica** | **Assente.** Zero nodi con evidenza di capacità utilizzabile. | Una fonte di capacità a livello di task: le ancore di WORKBank (Ae), o un'altra fonte collegata alle attività. |
| **Pesi w₁–w₃, λ, soglie θₙ e θ_d** | Non approvati. | Decisione del comitato di governance. |
| **Stabilità dei quadranti (80%), emivita delle evidenze (6 mesi)** | Valori di partenza, non tarati. | Backtesting e approvazione. |

Con la copertura assente, N non è calcolabile in modo valido. Le due job di prova hanno solo 6 attività su 22 con una corrispondenza esatta con O\*NET, quindi anche con una copertura completa N coprirebbe circa il 27% del lavoro.

## 3. Cosa serve per calcolare D

D viene dalle preferenze di chi lavora e di chi riceve il servizio. Oggi non ci sono dati.
- **Survey** ai lavoratori (d3) e ai beneficiari o ai loro rappresentanti (d4).
- **Panel** di esperti con la rubrica ancorata per d1 e d2 (3–5 persone: HR, linea, rappresentanza dei lavoratori, voce dei beneficiari).
- **Prior dell'LLM**, usabile solo finché manca il dato raccolto, e sempre etichettato come tale.

## 4. Conoscenze mancanti

1. **Ancore 1–5 di Ae in WORKBank.** Necessarie per la conversione a 0–4. Chiederle agli autori o trovare un'altra fonte.
2. **Licenze:** WORKBank non dichiarata; GDPval, METR e Microsoft da verificare; testi di licenza di O\*NET, Atlante ed ESCO da allegare.
3. **Coerenza della rubrica:** la verifica umana su 15 task usa la v1 per tutte le voci, mentre la versione finale per k2 e r è la v2. La seconda verifica (20 task alla cieca) non è versionata nel repository e non ha l'attribuzione per voce.
4. **Copertura delle Dolce:** quante delle 295 attività hanno un ponte con fonti di capacità, e con quale qualità.

## 5. Valutazioni necessarie, in ordine

| # | Valutazione | Chi | Perché |
|---|---|---|---|
| 1 | Revisione a campione delle 54 fusioni del Canonicalizer | Curatore | Il piano lo prevede; le fusioni sono applicate |
| 2 | Decisione sulle 4 relazioni del crosswalk da correggere | Responsabile del progetto | Relazione corretta o "nessuna" |
| 3 | Ampliamento del campione di revisione, soprattutto sulle relazioni più ampie e più strette | Revisori | Precisione con intervallo di confidenza stretto |
| 4 | Approvazione formale della rubrica v2 e verifica su campione più ampio, con più valutatori e attribuzione per voce | Responsabile metodologico, comitato | Rubrica v1 e v2 mescolate nei dati |
| 5 | Valutazione dei 295 task Dolce con la rubrica | Modello e panel umano | Oggi k dipende da task O\*NET, non dalle attività reali |
| 6 | Richiesta delle ancore di Ae o scelta di un'altra fonte di capacità | Responsabile metodologico | Sblocca cₖ |
| 7 | Decisione su pesi, λ, soglie, stabilità, emivita e soglia di precisione del crosswalk (90%) | Comitato di governance | Parametri di policy |
| 8 | Progettazione e approvazione della survey per D | Responsabile metodologico, rappresentanza dei lavoratori | Dati per d3 e d4 |
| 9 | Verifica delle licenze | Responsabile del progetto | Uso pubblico e conservazione dei dati |

## 6. Ordine proposto

1. Chiudere le valutazioni 1 e 2 (lavoro piccolo, già pronto).
2. Decidere le valutazioni 6 e 7: senza di esse N non si calcola.
3. Avviare la valutazione 5 sui 295 task, che è il lavoro più grande.
4. Preparare il piano approvato per il motore di calcolo di N, da eseguire quando 6 e 7 sono chiuse.
5. Per D, avviare la progettazione della survey (valutazione 8) in parallelo.

## 7. Decisioni da prendere adesso

- Chi approva il piano per il motore di N, e con quali parametri di partenza dichiarati non approvati?
- Chi chiede le ancore di WORKBank agli autori?
- Chi è il responsabile metodologico e chi è nel comitato di governance?
- Si procede con la valutazione dei 295 task Dolce con la rubrica?
