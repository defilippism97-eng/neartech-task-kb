# Verifica del rapporto di deep research (benchmark IA per mansioni di staff)

Ogni affermazione del rapporto è stata riscontrata sulla fonte primaria quando raggiungibile.
"Verificato" significa letto nella fonte; "non verificato" significa non letto o contraddetto.

## Licenze

| Fonte | Licenza nel rapporto | Verifica | Esito |
|---|---|---|---|
| GPTs are GPTs (Eloundou et al.) | MIT | LICENSE su raw.githubusercontent.com | confermata |
| FinQA | MIT | LICENSE | confermata |
| SWE-bench | MIT | LICENSE | confermata |
| WorkArena | Apache 2.0 | LICENSE | confermata |
| OSWorld | Apache 2.0 | LICENSE | confermata |
| AIOE (Felten et al.) | non dichiarata | LICENSE assente al percorso standard | da verificare |
| LegalBench | mista | LICENSE assente al percorso standard | da verificare |
| GDPval (dataset) | **Apache 2.0** | dataset card senza campo licenza | **non confermata**: il dataset non dichiara la licenza nel card |
| AEI (dataset) | **CC-BY-4.0 (dati)** | dataset card Hugging Face | **contraddetta**: il card dichiara MIT |

## Numeri

| Affermazione | Fonte | Esito |
|---|---|---|
| Crashing Waves vs Rising Tides, MIT FutureTech, arXiv 2604.01363, Mertens et al. | arXiv | paper esistente, autori corrispondono |
| "oltre 60.000 valutazioni" | abstract del paper | **discrepanza**: il rapporto ne riporta 17.000 |
| ~60% di successo nel 2024-Q2, >70% nel 2025-Q3, 88-97% entro il 2030 | abstract | confermata (il rapporto cita 60% e 88-97%) |
| Tasso al 60% a soglia 7/9, 49,7% a 8/9, 27% a 9/9; β = -0,27 | non nell'abstract | non verificato: serve il testo completo |
| GDPval: 1.320 task, 220 gold, 44 occupazioni | paper (cdn.openai.com) e dataset | confermata |
| GDPval: Claude Opus 4.1 47,6% win+tie | paper | confermata (già in GDP-01) |
| AEI: 757 SOC | file job_exposure.csv | confermata |
| GPTs are GPTs: 19.262 task, 923 occupazioni | repository | 923 occupazioni confermate (occ_level.csv); 19.262 task non trovati nei file accessibili |

## Fonti da scartare come evidenza

- Blog e siti di sintesi (novoresume, medium, generativeai.pub, sulbhajain.medium): non sono fonti primarie. Se servono, si risale alla fonte originale.
- Articoli su affiliazioni o adozione istituzionale che non misurano capacità o desiderabilità (es. adozione nelle burocrazie).

## Lacune confermate

Il rapporto lo afferma e la verifica lo conferma: per le funzioni di staff (acquisti, risorse umane, qualità,
tesoreria, IT di supporto, segreteria) non ci sono benchmark esecutivi con dataset aperti. Per N, quelle
funzioni restano senza evidenza di capacità a livello di task. Tracciato in carenza-evidenze.md.

## Azioni

1. Chiarire la licenza di GDPval e del dataset AEI prima di qualunque caricamento.
2. Riconciliare il numero di valutazioni di MIT FutureTech (17.000 o 60.000) con la versione del paper più recente.
3. Scaricare il testo completo del paper MIT per le soglie 7/9, 8/9, 9/9 e il coefficiente β.
4. Dataset GPTs-are-GPTs: l'occupazione a livello SOC è scaricata; i dati per task non sono stati trovati.
