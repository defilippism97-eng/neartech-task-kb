-- Migrazione 0009: registro delle decisioni.
-- Si applica dopo la 0008. Ogni atto di governance è una riga: proposta, approvazione,
-- rifiuto, ritiro, segnalazione, blocco, correzione. Le righe non si modificano;
-- una correzione è una riga nuova che rimanda alla precedente (corregge_id).
-- Catena di hash: ogni riga include l'hash della precedente, così l'auditor può
-- verificare che nessuna riga sia stata alterata (neartech.registro.verifica_catena).

CREATE TABLE registro_decisioni (
  decisione_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  posizione bigint NOT NULL UNIQUE,
  org_id uuid REFERENCES organizations,
  tipo_oggetto text NOT NULL,
  oggetto_id text NOT NULL,
  atto text NOT NULL CHECK (atto IN
    ('proposta', 'approvazione', 'rifiuto', 'ritiro', 'segnalazione', 'blocco', 'correzione')),
  autore_id uuid NOT NULL REFERENCES utenti,
  motivazione text NOT NULL CHECK (length(btrim(motivazione)) > 0),
  dettagli jsonb NOT NULL DEFAULT '{}'::jsonb,
  corregge_id bigint REFERENCES registro_decisioni,
  registrata_il timestamptz NOT NULL,
  hash_precedente text NOT NULL,
  hash text NOT NULL UNIQUE
);
CREATE INDEX registro_oggetto ON registro_decisioni (tipo_oggetto, oggetto_id, posizione);
CREATE INDEX registro_org ON registro_decisioni (org_id, posizione);

-- Hash di una riga: serializzazione JSON dei campi, deterministica anche con valori nulli.
CREATE FUNCTION registro_hash(r registro_decisioni) RETURNS text LANGUAGE sql STABLE AS $$
  SELECT encode(sha256(convert_to(jsonb_build_array(
    r.posizione, r.hash_precedente, r.org_id, r.tipo_oggetto, r.oggetto_id, r.atto,
    r.autore_id, r.motivazione, r.dettagli, r.corregge_id,
    to_char(r.registrata_il AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US')
  )::text, 'UTF8')), 'hex')
$$;

-- Posizione, ora e hash li assegna il database, sotto un lock che serializza gli inserimenti.
CREATE FUNCTION registro_concatena() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  ultima_posizione bigint;
  ultimo_hash text;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtext('registro_decisioni'));
  SELECT posizione, hash INTO ultima_posizione, ultimo_hash
  FROM registro_decisioni ORDER BY posizione DESC LIMIT 1;
  NEW.posizione := COALESCE(ultima_posizione, 0) + 1;
  NEW.hash_precedente := COALESCE(ultimo_hash, repeat('0', 64));
  NEW.registrata_il := clock_timestamp();
  NEW.hash := registro_hash(NEW);
  RETURN NEW;
END;
$$;
CREATE TRIGGER registro_concatena
  BEFORE INSERT ON registro_decisioni
  FOR EACH ROW EXECUTE FUNCTION registro_concatena();
CREATE TRIGGER registro_append_only
  BEFORE UPDATE OR DELETE ON registro_decisioni
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER registro_no_truncate
  BEFORE TRUNCATE ON registro_decisioni
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();

-- Ultimo atto decisivo (approvazione, rifiuto, ritiro) per ogni oggetto di governance.
CREATE VIEW stato_oggetti_governance AS
SELECT DISTINCT ON (tipo_oggetto, oggetto_id)
       tipo_oggetto, oggetto_id, atto AS ultimo_atto, decisione_id AS ultimo_atto_id
FROM registro_decisioni
WHERE atto IN ('approvazione', 'rifiuto', 'ritiro')
ORDER BY tipo_oggetto, oggetto_id, posizione DESC;
