-- Migrazione 0019: parametri comuni, campioni di revisione, giudizi e misure di precisione (fase 2).
-- Si applica dopo la 0018. Decisioni: docs/metodologia-estensioni.md, sezione 9.
-- Tutte le tabelle nuove sono append-only. Nessun valore di parametro è inserito qui.

-- 1. Permessi nuovi. La matrice si cambia solo con una migrazione, che disattiva il trigger
-- in modo esplicito e lo riattiva subito.
ALTER TABLE permessi_ruolo DISABLE TRIGGER permessi_no_insert;
INSERT INTO permessi_ruolo (ruolo, azione) VALUES
  ('amministratore_tecnico', 'proporre_parametro_comune'),
  ('amministratore_tecnico', 'approvare_parametro_comune'),
  ('revisore', 'gestire_campioni');
ALTER TABLE permessi_ruolo ENABLE TRIGGER permessi_no_insert;

-- 2. Campioni di revisione: estrazione registrata (criterio, seme, popolazione) da un insieme di proposte.
CREATE TABLE campioni_revisione (
  campione_id uuid PRIMARY KEY,
  org_id uuid NOT NULL REFERENCES organizations,
  tipo_proposta text NOT NULL CHECK (tipo_proposta IN ('crosswalk', 'fusione', 'abbinamento')),
  filtro jsonb NOT NULL DEFAULT '{}'::jsonb,
  criterio text NOT NULL CHECK (criterio IN ('tutte', 'casuale', 'importato')),
  seme bigint,
  popolazione int NOT NULL CHECK (popolazione > 0),
  dimensione int NOT NULL CHECK (dimensione > 0 AND dimensione <= popolazione),
  versione_istruzioni text NOT NULL,
  decisione_id bigint NOT NULL REFERENCES registro_decisioni,
  creato_il timestamptz NOT NULL DEFAULT now(),
  CHECK ((criterio = 'casuale') = (seme IS NOT NULL))
);
CREATE INDEX campioni_org ON campioni_revisione (org_id);
CREATE INDEX campioni_decisione ON campioni_revisione (decisione_id);

-- Elementi del campione: riferimenti alle proposte (identificativi, mai testo del cliente).
CREATE TABLE elementi_campione (
  campione_id uuid NOT NULL REFERENCES campioni_revisione,
  posizione int NOT NULL CHECK (posizione > 0),
  riferimento jsonb NOT NULL,
  PRIMARY KEY (campione_id, posizione),
  UNIQUE (campione_id, riferimento)
);

-- 3. Giudizi: un record per giudizio; un ripensamento è un record nuovo.
CREATE TABLE giudizi_revisione (
  giudizio_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  campione_id uuid NOT NULL,
  posizione int NOT NULL,
  esito text NOT NULL CHECK (esito IN ('corretto', 'parziale', 'errato')),
  nota text,
  revisore_id uuid NOT NULL REFERENCES utenti,
  versione_istruzioni text NOT NULL,
  creato_il timestamptz NOT NULL DEFAULT clock_timestamp(),
  FOREIGN KEY (campione_id, posizione) REFERENCES elementi_campione
);
CREATE INDEX giudizi_elemento ON giudizi_revisione (campione_id, posizione, revisore_id, giudizio_id DESC);
CREATE INDEX giudizi_revisore ON giudizi_revisione (revisore_id);

-- 4. Misure: calcolo deterministico con le sue chiavi (parametri usati, origine delle proposte, versione).
CREATE TABLE misure_precisione (
  misura_id uuid PRIMARY KEY,
  campione_id uuid NOT NULL REFERENCES campioni_revisione,
  n_elementi int NOT NULL,
  n_corretti int NOT NULL,
  n_parziali int NOT NULL,
  n_errati int NOT NULL,
  regola_parziali text NOT NULL,
  parametro_regola_id uuid NOT NULL REFERENCES parametri_governance,
  precisione numeric NOT NULL CHECK (precisione BETWEEN 0 AND 1),
  intervallo_basso numeric NOT NULL,
  intervallo_alto numeric NOT NULL,
  livello_confidenza numeric NOT NULL,
  parametro_confidenza_id uuid NOT NULL REFERENCES parametri_governance,
  soglia numeric NOT NULL,
  parametro_soglia_id uuid NOT NULL REFERENCES parametri_governance,
  esito text NOT NULL CHECK (esito IN ('sopra_soglia', 'sotto_soglia')),
  origine_proposte jsonb NOT NULL,
  versione_calcolo text NOT NULL,
  calcolata_da uuid NOT NULL REFERENCES utenti,
  calcolata_il timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX misure_campione ON misure_precisione (campione_id, calcolata_il);
CREATE INDEX misure_calcolata_da ON misure_precisione (calcolata_da);
CREATE INDEX misure_parametro_regola ON misure_precisione (parametro_regola_id);
CREATE INDEX misure_parametro_confidenza ON misure_precisione (parametro_confidenza_id);
CREATE INDEX misure_parametro_soglia ON misure_precisione (parametro_soglia_id);

-- 5. Append-only.
CREATE TRIGGER campioni_append_only BEFORE UPDATE OR DELETE ON campioni_revisione
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER campioni_no_truncate BEFORE TRUNCATE ON campioni_revisione
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER elementi_append_only BEFORE UPDATE OR DELETE ON elementi_campione
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER elementi_no_truncate BEFORE TRUNCATE ON elementi_campione
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER giudizi_append_only BEFORE UPDATE OR DELETE ON giudizi_revisione
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER giudizi_no_truncate BEFORE TRUNCATE ON giudizi_revisione
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER misure_append_only BEFORE UPDATE OR DELETE ON misure_precisione
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER misure_no_truncate BEFORE TRUNCATE ON misure_precisione
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
