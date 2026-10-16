-- Migrazione 0010: parametri di governance versionati e indirizzi del comitato guida.
-- Si applica dopo la 0009. Le righe non si modificano: una versione nuova è una riga nuova.
-- Lo stato di una versione si ricava dal registro delle decisioni. È vigente l'ultima
-- versione approvata, purché non sia stata ritirata; una versione rifiutata non conta.
-- Nessun valore è inserito qui: soglie, quote e regole le approva il comitato guida.

CREATE TABLE parametri_governance (
  parametro_id uuid PRIMARY KEY,
  codice text NOT NULL CHECK (codice ~ '^[a-z][a-z0-9_]*$'),
  org_id uuid REFERENCES organizations,  -- NULL: parametro NEARTECH comune
  versione int NOT NULL CHECK (versione > 0),
  valore jsonb NOT NULL,
  descrizione text NOT NULL,
  proposta_id bigint NOT NULL REFERENCES registro_decisioni,
  creato_il timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX parametri_versione
  ON parametri_governance (codice, COALESCE(org_id, '00000000-0000-0000-0000-000000000000'::uuid), versione);
CREATE TRIGGER parametri_append_only
  BEFORE UPDATE OR DELETE ON parametri_governance
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();

-- Indirizzi di alto livello del comitato guida (ADR 0002). Il testo è un dato:
-- quando un agente lo riceve, non lo esegue come istruzione.
CREATE TABLE indirizzi_comitato (
  indirizzo_id uuid PRIMARY KEY,
  org_id uuid NOT NULL REFERENCES organizations,
  codice text NOT NULL CHECK (codice ~ '^[a-z][a-z0-9_]*$'),
  versione int NOT NULL CHECK (versione > 0),
  testo text NOT NULL,
  ambito text NOT NULL,
  proposta_id bigint NOT NULL REFERENCES registro_decisioni,
  creato_il timestamptz NOT NULL DEFAULT now(),
  UNIQUE (org_id, codice, versione)
);
CREATE TRIGGER indirizzi_append_only
  BEFORE UPDATE OR DELETE ON indirizzi_comitato
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();

CREATE VIEW parametri_vigenti AS
WITH decise AS (
  SELECT p.*, s.ultimo_atto, s.ultimo_atto_id
  FROM parametri_governance p
  JOIN stato_oggetti_governance s
    ON s.tipo_oggetto = 'parametro' AND s.oggetto_id = p.parametro_id::text
  WHERE s.ultimo_atto IN ('approvazione', 'ritiro')
), ultime AS (
  SELECT DISTINCT ON (codice, org_id) * FROM decise ORDER BY codice, org_id, versione DESC
)
SELECT parametro_id, codice, org_id, versione, valore, descrizione, proposta_id,
       ultimo_atto_id AS approvazione_id
FROM ultime WHERE ultimo_atto = 'approvazione';

CREATE VIEW indirizzi_vigenti AS
WITH decisi AS (
  SELECT i.*, s.ultimo_atto, s.ultimo_atto_id
  FROM indirizzi_comitato i
  JOIN stato_oggetti_governance s
    ON s.tipo_oggetto = 'indirizzo' AND s.oggetto_id = i.indirizzo_id::text
  WHERE s.ultimo_atto IN ('approvazione', 'ritiro')
), ultimi AS (
  SELECT DISTINCT ON (org_id, codice) * FROM decisi ORDER BY org_id, codice, versione DESC
)
SELECT indirizzo_id, org_id, codice, versione, testo, ambito, proposta_id,
       ultimo_atto_id AS approvazione_id
FROM ultimi WHERE ultimo_atto = 'approvazione';
