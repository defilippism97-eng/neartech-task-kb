-- Migrazione 0031: campioni delle proposte di abbinamento al dataset consolidato (fase 3, ADR 0006) e
-- convalida del vincolo sulle note dei giudizi (0028), dopo lo spostamento delle note in produzione.
-- Si applica dopo la 0030, nello stesso giro di migra.py che porta gli spazi alla 0008.

SET LOCAL lock_timeout = '10s';

-- 1. Le note dei giudizi esistenti sono state spostate nello spazio (0007 degli spazi, 2026-10-17).
ALTER TABLE giudizi_revisione VALIDATE CONSTRAINT giudizi_nota_nello_spazio;

-- 2. Elementi di tipo 'abbinamento': il riferimento è la proposta nello spazio dell'organizzazione del
--    campione (org_<codice>.proposte_abbinamento), che deve esistere. Per gli altri tipi resta la regola
--    della 0020, con i valori nulli rifiutati come nella 0025.
CREATE OR REPLACE FUNCTION controlla_elemento() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  tipo text;
  codice_org text;
  attese text[];
  chiavi text[];
  presente boolean;
  formato_uuid constant text := '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
BEGIN
  SELECT c.tipo_proposta, o.codice INTO tipo, codice_org
  FROM campioni_revisione c JOIN organizations o USING (org_id) WHERE c.campione_id = NEW.campione_id;
  attese := CASE tipo
              WHEN 'fusione' THEN ARRAY['proposal_id']
              WHEN 'crosswalk' THEN ARRAY['node_id', 'task_id']
              WHEN 'abbinamento' THEN ARRAY['proposta_id']
            END;
  IF attese IS NULL THEN
    RAISE EXCEPTION 'tipo di proposta % non ancora gestito negli elementi', tipo;
  END IF;
  SELECT array_agg(k ORDER BY k) INTO chiavi FROM jsonb_object_keys(NEW.riferimento) AS k;
  IF chiavi IS DISTINCT FROM attese THEN
    RAISE EXCEPTION 'riferimento con chiavi % invece di %', chiavi, attese;
  END IF;
  IF EXISTS (SELECT 1 FROM jsonb_each_text(NEW.riferimento) AS v
             WHERE v.value IS NULL OR v.value !~ formato_uuid) THEN
    RAISE EXCEPTION 'riferimento con identificativi non canonici';
  END IF;
  IF tipo = 'abbinamento' THEN
    IF codice_org IS NULL OR to_regclass(format('%I.proposte_abbinamento', 'org_' || codice_org)) IS NULL THEN
      RAISE EXCEPTION 'l''organizzazione del campione % non ha le proposte di abbinamento', NEW.campione_id;
    END IF;
    EXECUTE format('SELECT EXISTS (SELECT 1 FROM %I.proposte_abbinamento WHERE proposta_id = $1)',
                   'org_' || codice_org)
      INTO presente USING (NEW.riferimento ->> 'proposta_id')::uuid;
    IF NOT presente THEN
      RAISE EXCEPTION 'proposta di abbinamento % inesistente nello spazio dell''organizzazione',
        NEW.riferimento ->> 'proposta_id';
    END IF;
  END IF;
  IF EXISTS (SELECT 1 FROM giudizi_revisione WHERE campione_id = NEW.campione_id)
     OR EXISTS (SELECT 1 FROM misure_precisione WHERE campione_id = NEW.campione_id) THEN
    RAISE EXCEPTION 'il campione % ha già giudizi o misure: gli elementi non cambiano', NEW.campione_id;
  END IF;
  RETURN NEW;
END;
$$;

CREATE UNIQUE INDEX elementi_abbinamento_unico
  ON elementi_campione (campione_id, (riferimento ->> 'proposta_id')) WHERE riferimento ? 'proposta_id';
