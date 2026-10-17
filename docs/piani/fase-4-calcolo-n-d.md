# Fase 4: calcolo deterministico di N e D

Data: 2026-10-17. Riferimenti: `docs/piano-sviluppo-v2.md` (formule di N e D, quadranti, "Come si calcolano i risultati"); registro di metodo, sezioni 5, 6 e 17; `docs/HANDOVER.md`, sezione 9, punto 4.

## Formule (dal piano, invariate)

- Divario per dimensione: `g_k = max(0, d_k − c_k) / 4`, con domanda `d_k` (k1, k2, k3) e copertura `c_k` su scala 0–4.
- `N = min(1, Σ w_k · g_k · (1 + λ · r/4))`, con pesi `w_k` (somma 1) e λ del profilo approvato.
- `D = Σ w_j · d_j / 4` sulle componenti disponibili, con i pesi del profilo riportati a somma 1 (sezione 17): oggi d1 e d2, D provvisorio.
- Quadrante: N alto se `N ≥ θ_N`, D alto se `D ≥ θ_D` (soglie del profilo). Q1 N alto e D alto; Q2 N alto e D basso; Q3 N basso e D alto; Q4 N basso e D basso.

Verifica con l'esempio svolto del piano: task B (domanda 3, 3, 1; copertura 1, 1, 2; r = 3; pesi 0,4, 0,4, 0,2; λ = 0,5) dà N = 0,55; D (4, 3, 4, 4 con pesi 0,25) = 0,9375.

## Simulazione (sezione 17)

2.000 estrazioni per occorrenza. Ogni voce si estrae dai giudizi registrati per la versione corrente della rubrica: i giudizi di persone sostituiscono quelli del modello; un giudizio sull'occorrenza vale più di uno sul task. La copertura si estrae uniformemente fra `c_low` e `c_high` dello snapshot pubblicato. Seme fisso, derivato dal seme del calcolo e dall'occorrenza: stesso input, stesso risultato.

Risultati in `policy_estimates`: media e deviazione di N e D, probabilità dei quattro quadranti, composizione delle fonti di D. Ogni riga porta le sue chiavi: profilo, snapshot, rubrica, versione del calcolo, seme, numero di estrazioni, tipo di capacità (test o riserva), componenti di D usate, impronta dei giudizi usati.

Senza copertura per il task, N e i quadranti restano vuoti; senza d1 e d2, D resta vuoto. Nessun valore inventato.

## Copertura di riserva (sezione 17)

Finché la capacità di test non è calibrata, lo snapshot di capacità è di **riserva**: la scala di riserva della rubrica, qualità minima, dichiarata nel tipo dello snapshot e quindi in ogni risultato. Lo snapshot si costruisce dalle evidenze con la formula del piano (qualità, forza del collegamento, decadimento) e l'intervallo dato dal disaccordo fra le evidenze.

## Prerequisiti di governance per un calcolo in produzione

Rubrica corrente approvata, profilo di pesi attivo e approvato, snapshot di capacità pubblicato. Oggi in produzione non ci sono: il motore si costruisce e si prova su dati sintetici.
