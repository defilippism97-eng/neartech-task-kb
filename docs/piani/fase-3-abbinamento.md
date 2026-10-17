# Fase 3: abbinamento al dataset consolidato e priorità di revisione

Data: 2026-10-17. Riferimenti: `docs/HANDOVER.md` sezioni 3 (Canonicalizzazione, versione rivista) e 9, punto 3; registro di metodo, sezione 9 (revisione iniziale a campione, quota come parametro); ADR 0001, 0004, 0005; ADR 0006.

## Obiettivo

Quando un'organizzazione carica i suoi mansionari, ogni attività estratta diventa un **candidato**. Il sistema propone per ciascun candidato il task più vicino del dataset consolidato; il revisore approva il lotto in blocco o rifiuta le proposte sbagliate; l'applicazione è deterministica:
- proposta approvata: l'occorrenza dell'organizzazione si collega al task del dataset, e N e D si trasferiscono (le valutazioni sono per task);
- proposta rifiutata, o dataset senza un task vicino: il candidato entra nel dataset come task nuovo, con il testo del cliente solo nello spazio.

## Flusso

1. **Candidati** (`scripts/scomponi_job.py`): la scomposizione salva le attività nello spazio dell'organizzazione (`candidati`), senza creare task nel dataset.
2. **Proposte** (`neartech.abbinamento.proponi_abbinamenti`): un lotto per esecuzione. Per ogni candidato, embedding locale (bge-m3) e i k task attivi più vicini (k tecnico, come nel Canonicalizer). La proposta è il più vicino; si salvano distanza, margine sul secondo e l'elenco dei vicini. Nessuna soglia di distanza nel codice. Il lotto dichiara il livello di revisione (`campione`, `completa`, `nulla`); con `campione` registra il parametro `quota_revisione_abbinamenti` vigente.
3. **Coda di revisione** (`coda_revisione`): proposte ordinate per ambiguità, cioè margine crescente e poi distanza decrescente. È un ordinamento, non un filtro: nessuna soglia.
4. **Campione e misura**: campione del lotto con la dimensione data dalla quota (`casuale`, con seme) o con tutte le proposte (`completa`); revisione cieca e misura di precisione con la metrica della fase 2 (`soglia_precisione_abbinamento`, `regola_parziali`, `livello_confidenza`).
5. **Decisione in blocco** (`decidi_lotto`): il revisore approva il lotto tranne le proposte che rifiuta. Con livello `campione` o `completa` serve una misura sul campione del lotto; l'atto ne riporta l'esito. Un record per ogni proposta, legato all'atto.
6. **Applicazione** (`applica_lotto`): deterministica, con un atto nel registro. Task nuovi con embedding; occorrenze in public senza testo e nello spazio con il testo.

## Dati

- Spazio dell'organizzazione (migrazione 0008 degli spazi): `candidati`, `lotti_abbinamento`, `proposte_abbinamento`, `decisioni_abbinamento`, `applicazioni_abbinamento`; tutte append-only.
- Public (migrazione 0031): elementi di campione di tipo `abbinamento` (`proposta_id`), convalida del vincolo sulle note dei giudizi.
- Ogni risultato porta le sue chiavi: lotto, modello di embedding, k, livello di revisione, parametro della quota, misura.

## Decisioni metodologiche aperte (non bloccano lo sviluppo)

1. Valore della quota di revisione (`quota_revisione_abbinamenti`): parametro comune da approvare.
2. ~~Se una decisione in blocco va impedita quando la misura del lotto è sotto soglia~~: deciso il 2026-10-17, si registra e non si blocca (registro di metodo, sezione 26).
3. Come il livello di revisione del lotto incide sullo stato dei risultati (oggi: si registra con i risultati).
4. Se aggiungere un giudizio del modello sulle proposte (oggi: solo vicinanza; il prompt del Canonicalizer v2 non ha superato il controllo).

## Test

TDD su Postgres locale con un embedding finto deterministico; nessuna chiamata all'API.
