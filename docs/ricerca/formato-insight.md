# Formato degli insight per la classificazione dei task

Ogni insight estratto da una fonte diventa **un record** in `evidence_items` (N) oppure
in un registro di riferimento per D. Un insight che non si può ricondurre a una fonte,
a un nodo di tassonomia e a una data non entra nel calcolo.

## Campi obbligatori

| Campo | Significato | Esempio |
|---|---|---|
| `source` | Fonte precisa: autori, anno, identificativo | WORKBank, Shao et al. 2025, arXiv 2506.06576 |
| `source_location` | Pagina o sezione dove sta il dato | §3.2, p. 9 |
| `observed_at` | Data della rilevazione o della pubblicazione | 2025-05 (raccolta), 2025-06 (arXiv) |
| `variable` | Cosa misura il dato | `expert_capability_Ae`, `worker_desire_Aw`, `worker_HAS_Hw` |
| `value_raw` | Valore nella scala originale | 1–5 (Likert) |
| `scale` | Scala originale e significato degli estremi | 1 = Not at all, 5 = Entirely |
| `value_0_4` | Conversione sulla scala 0–4 del piano | calcolata dal codice, non a mano |
| `evidence_type` | Gerarchia di qualità del piano | `benchmark`, `usage_success`, `usage`, `internal_pilot`, `expert`, `llm_prior` |
| `task_link` | Nodo di tassonomia collegato, con relazione | `ONET_TASK 8823` relazione `exact` |
| `relation` | `exact`, `broad`, `narrow`, `related` | exact solo con l'ID O*NET |
| `n` | Numero di giudizi o di campioni alla base del dato | 1.500 valutazioni, 104 occupazioni |
| `agreement` | Accordo tra valutatori, se disponibile | α = 0,539 (Ae) |
| `use` | A cosa serve il dato | `N` · `D_ref` · `validazione` · `contesto` |
| `dimension` | Dimensione della domanda | `any` se il dato non separa k1, k2, k3 |
| `quality` | Qualità dichiarata, da confermare in governance | scala del piano, non ancora definita |
| `licence` | Licenza della fonte, verificata prima del caricamento | da verificare |
| `notes` | Limiti e avvertenze | esperti AI, non benchmark |

## Regole

1. **Un insight = una variabile misurata.** Se una frase contiene due misure, sono due record.
2. **N si alimenta solo di capacità** (`expert`, `benchmark`, `usage_success`, `internal_pilot`).
   Le preferenze dei lavoratori (`Aw`, `Hw`) non entrano in N: sono D di riferimento.
3. **Il collegamento alla tassonomia è esplicito.** L'evidenza passa a un nodo solo con
   relazione `exact` o più stretta; altrimenti resta in contesto.
4. **Nessun valore trasformato a mano.** La conversione alla scala 0–4 è codice versionato.
5. **Un dato senza scala dichiarata non si usa.** Se la scala manca nel paper, il record va
   marcato `scala da verificare` e tenuto fuori dal calcolo.
