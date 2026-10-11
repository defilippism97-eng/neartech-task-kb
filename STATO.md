# Stato del progetto (aggiornato al 2026-10-10)

Questo file è il punto di ripartenza per le sessioni future. La cronologia della chat
non viene conservata: tutto ciò che serve per riprendere il lavoro è qui o nel codice.

## Cosa è fatto

- **Metodologia**: `docs/piano-sviluppo-v2.md` (piano V2 completo). Regole di progetto in `CLAUDE.md`.
- **Schema**: `db/schema.sql` (PostgreSQL 16 + pgvector), applicato e verificato.
  Vincolo sui profili di pesi attivi, e vista `v_role_metrics` interrogabile.
- **Migrazione 0002** (`db/migrations/`): livelli `ATLANTE_RA` e `ATLANTE_ATTIVITA`,
  tabella `taxonomy_embeddings` per modello. Lo schema originale non è stato modificato.
- **Codice Python** (`src/neartech/`): connessione (`db.py`), modelli validati (`models.py`),
  caricatore tassonomie (`taxonomy.py`), evidenze (`evidence.py`), Scorer con
  `claude-haiku-5-5` (`scorer.py`, 5 campioni per voce, ogni campione salvato come record `llm`).
- **Caricatore completo** (`scripts/carica_tassonomie.py`): carica O*NET 31.0, Atlante (API v2)
  ed ESCO 1.2.1 in italiano con la gerarchia, poi gli embedding bge-m3.
- **Test**: 14 test passano su PostgreSQL 16 + pgvector; 1 test richiede `NEARTECH_ANTHROPIC_API_KEY`.
- **Workflow manuale** (`.github/workflows/test-scorer-reale.yml`): esegue i test con il modello reale
  usando il segreto GitHub `Claude`. Ultimo run riuscito: run #2.
- **Licenze**: confermate dal responsabile del progetto il 2026-10-10. Il testo di ciascuna licenza
  va ancora allegato (vedi "Da fare").

## Dati caricati (nel database locale di sessione, non persistente)

| Fonte | Versione | Nodi | Note |
|---|---|---|---|
| O*NET | 31.0 (testo) | 18.838 task | scheme `ONET_TASK`, lingua `en` |
| Atlante del Lavoro INAPP | API v2, snapshot 2026-10-10 | 961 ADA, 2.482 RA, 7.129 attività | gerarchia ADA → RA → attività |
| ESCO | 1.2.1, CSV italiano | 3.039 occupazioni, 13.939 competenze | 25 righe duplicate già nel file originale: tenuta la prima |

Embedding bge-m3 (1024 dimensioni) per tutti i nodi: 46.388 vettori.
Controllo rapido: i vicini di un task O*NET sono coerenti tra lingue e fonti.

**Attenzione:** i file sorgente e i vettori sono in `/tmp/claude-0/` e spariscono con la sessione.
Il database locale `neartech_kb` non è persistente.

## Recupero dopo il cambio di sessione (storico)

- **Gli embedding non sono salvati da nessuna parte.** I vettori (circa 190 MB) sono in `/tmp/claude-0/kb_work/out/`
  e spariscono con la sessione. Il connettore Google Drive non è adatto: il contenuto passa per il contesto
  della chat e un file così grande non ci entra. Non tentare di caricarli su Drive.
- **Piano di recupero:** appena `DATABASE_URL` è disponibile, lanciare prima schema, migrazione e caricamento dei
  nodi (veloce), poi ricalcolare gli embedding bge-m3 in background (circa 40 minuti su CPU) e scriverli in
  `taxonomy_embeddings`. Il caricatore `scripts/carica_tassonomie.py` lo fa in un solo passaggio, ma richiede
  le fonti scaricate di nuovo (vedi sotto).
- **Manifest delle fonti** (hash e stato): `docs/dati/fonti-manifest.json`. Usalo per verificare che i file
  riscaricati siano gli stessi (stesso SHA-256). ESCO: il pacchetto locale da 3,9 GB non serve, usa solo il
  CSV italiano (`esco_classification_it_csv.zip`, circa 9 MB).
- **Cartella Drive "Metodologia e costruzione Knowledge base" (id `1FX2nP75zZsb3ddehwzrypwNVXHvc1FaR`):**
  contiene la cartella "Job Società Dolce" (id `1g2LGTbuEfNml6a9McwjvEkHQGgFzLwFx`) con i job description
  approvati, da leggere con il connettore Drive quando serve. Il repository resta la fonte del codice e della
  documentazione.
- **Stato all'ultima sessione:** schema e migrazione applicati al database locale (non persistente); nodi di
  O*NET, Atlante ed ESCO caricati localmente; embedding ricalcolati e caricati localmente. Tutto questo va rifatto
  sul database persistente.

### Embedding salvati in chat (da ricaricare nella sessione nuova)

Gli embedding sono stati inviati in chat come file da scaricare, in float16 (perdita di precisione
di circa 1e-4). I file da caricare nella nuova sessione sono:

- `bge_m3_onet_atlante.f16.npy.part00` ... `part03` (O*NET, Atlante)
- `bge_m3_esco.f16.npy.part00` e `part01` (ESCO)
- `embeddings_index.jsonl` e `embeddings_esco_index.jsonl` (indici, stesso ordine dei vettori)
- `fonti-manifest.json` e `checksum-parti.txt` (per verificare le parti)

Ricomposizione (nella cartella con i file):

```bash
cat bge_m3_onet_atlante.f16.npy.part* > embeddings_bge_m3.npy
cat bge_m3_esco.f16.npy.part*         > embeddings_esco_bge_m3.npy
sha256sum -c checksum-parti.txt   # verifica le parti; i checksum dei file ricomposti non sono in lista
```

Il caricatore `scripts/carica_tassonomie.py` legge questi nomi e converte i vettori in float32. Per
usarlo servono anche i file sorgente (O*NET zip, Atlante JSON, ESCO CSV zip) con gli hash di
`docs/dati/fonti-manifest.json`. Gli embedding ricaricati evitano i circa 40 minuti di calcolo.

## Stato del database (aggiornato al 2026-10-10, sera)

- Database Neon (Francoforte) con pgvector attivo, schema e migrazione 0002 applicati.
- Tassonomie caricate: O*NET 31.0 (18.838), Atlante API v2 (10.572, con genitori collegati), ESCO 1.2.1 (16.978).
- Embedding bge-m3 caricati per tutti i 46.388 nodi (`taxonomy_embeddings`). Calcolati da etichetta del nodo.
- Il collegamento al database passa dall'endpoint HTTPS di Neon: `NEARTECH_DB_VIA=https`. Le scritture non sono
  in transazione interattiva: i caricamenti sono idempotenti e si rilanciano se si interrompono.

## Scomposizione job description Dolce (completata 2026-10-11)

- 36 job description caricate dalle proposte approvate (file `docs/dati/scomposizione-approvata-2026-10-11.jsonl`,
  sha256 `a86b6304...`). Il file contiene le attività verificate sul testo, e il caricamento le usa senza
  chiamare il modello (`scripts/scomponi_job.py --da-file`).
- Database di produzione: 384 task canonici, 530 occorrenze (ruolo x task), 36 ruoli, 36 fonti `org_document`.
- Noto: 5 titoli compaiono due volte nello stesso ruolo; la base dati ne tiene una sola occorrenza (vincolo unico task-ruolo).
- Il documento `Job_Responsabile Qualità e Altri Sistemi -.docx` è vuoto: escluso.
- Il crosswalk non è ancora stato eseguito sui task di Dolce: `scripts/esegui_crosswalk.py` ora ha i task da mappare.

## Da fare, in ordine

1. **Crosswalk Mapper**: implementato e provato su un task di prova. Per ogni task canonico cerca i 20 nodi più vicini
   per tassonomia, poi il modello assegna la relazione (esatta, più ampia, più stretta, affine, nessuna)
   con una motivazione. Si salvano solo le relazioni diverse da "nessuna".
2. **Job description Dolce**: cartella Drive "Job Società Dolce" (id `1g2LGTbuEfNml6a9McwjvEkHQGgFzLwFx`),
   circa 35 file .docx, uno per ruolo; la lista è paginata, quindi verificare il totale.
   Passo successivo: scomposizione in task canonici (con il modello) e collegamento alle tassonomie.
3. **Allegare i testi delle licenze** di O*NET, Atlante ed ESCO al progetto, e aggiornare la colonna
   `license` in `sources`.
4. **Job di calcolo di N e D** (Monte Carlo, quadranti, baricentro e dispersione): non ancora costruito.
   Si può scrivere con dati sintetici, senza chiavi. Modifica di policy: va approvato in modalità plan.
5. **Primo test reale dello Scorer** sul gold standard, con `NEARTECH_ANTHROPIC_API_KEY`.

## Note tecniche

- Gli embedding ricalcolati usano solo l'etichetta del nodo (`scripts/calcola_embedding.py`).
- Il caricatore `scripts/carica_tassonomie.py` accetta gli embedding anche da file; i file del vecchio calcolo
  non servono più perché i vettori sono nel database.
- Correzione applicata: il genitore di ATLANTE_RA è cercato tra gli ADA, quello di ATLANTE_ATTIVITA tra i RA.

## Decisioni prese

- Il responsabile dell'organizzazione (Dolce) segue i ruoli human in the loop per il pilota.
  Il piano prevede però anche curatore, responsabile metodologico e un rappresentante dei lavoratori
  nel panel: va chiarito chi copre ciascun ruolo, per evitare che un solo soggetto giudichi tutto.
- Nessuna soglia o peso nel codice: stanno in tabelle di governance versionate.
- Niente piattaforma di orchestrazione per ora: script, tabella `jobs` e revisione umana quando
  ci saranno casi reali (piano, F3).

## Limiti noti

- ESCO: la gerarchia delle competenze (`skillsHierarchy`) e le relazioni tra occupazioni non sono ancora caricate.
- Atlante: un'attività che compare sotto più risultati attesi ha come genitore solo il primo.
- Scorer: il test con il modello reale è verde, ma non è ancora stato eseguito sul gold standard.

## Comandi utili

```bash
uv venv -p 3.12 .venv && uv pip install -p .venv -e ".[dev]"
# Test: serve un PostgreSQL 16 con pgvector locale (nella sandbox: apt install postgresql-16 postgresql-16-pgvector)
NEARTECH_TEST_DSN="postgresql://postgres:test@localhost:5432/neartech_test" .venv/bin/pytest
# Il test con il modello reale richiede anche NEARTECH_ANTHROPIC_API_KEY (consuma token).
```
