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
  lotto text;
  attese text[];
  chiavi text[];
  presente boolean;
  formato_uuid constant text := '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
BEGIN
  SELECT c.tipo_proposta, o.codice, c.filtro ->> 'lotto' INTO tipo, codice_org, lotto
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
    IF lotto IS NULL OR lotto !~ formato_uuid THEN
      RAISE EXCEPTION 'il campione di abbinamento % non indica il suo lotto', NEW.campione_id;
    END IF;
    -- La proposta è del lotto del campione e ha un task proposto: la stessa popolazione di neartech.campioni.
    EXECUTE format('SELECT EXISTS (SELECT 1 FROM %I.proposte_abbinamento
                                   WHERE proposta_id = $1 AND lotto_id = $2 AND task_id IS NOT NULL)',
                   'org_' || codice_org)
      INTO presente USING (NEW.riferimento ->> 'proposta_id')::uuid, lotto::uuid;
    IF NOT presente THEN
      RAISE EXCEPTION 'proposta di abbinamento % non del lotto % o senza task proposto',
        NEW.riferimento ->> 'proposta_id', lotto;
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

-- 3. Un solo campione per lotto: la misura che accompagna la decisione non si sceglie fra più estrazioni.
CREATE UNIQUE INDEX campioni_uno_per_lotto ON campioni_revisione ((filtro ->> 'lotto'))
  WHERE tipo_proposta = 'abbinamento';

-- 4. Controlli delle tabelle dell'abbinamento negli spazi (migrazione 0008 degli spazi). TG_TABLE_SCHEMA è lo
--    spazio; l'organizzazione si ricava dal suo codice. Ogni riga cita l'atto giusto del registro, della stessa
--    organizzazione, e resta coerente con la proposta e con la decisione.

CREATE FUNCTION abbinamento_org_dello_spazio(spazio text) RETURNS uuid
LANGUAGE sql STABLE SET search_path = public, pg_temp AS $$
  SELECT org_id FROM organizations WHERE 'org_' || codice = spazio
$$;

CREATE FUNCTION abbinamento_controlla_atto(atto_id bigint, spazio text, tipo text, oggetto uuid, atto_atteso text)
RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path = public, pg_temp AS $$
DECLARE
  r registro_decisioni;
BEGIN
  SELECT * INTO r FROM registro_decisioni WHERE decisione_id = atto_id;
  IF r IS NULL OR r.org_id IS DISTINCT FROM abbinamento_org_dello_spazio(spazio) OR r.tipo_oggetto <> tipo
     OR r.oggetto_id <> oggetto::text OR r.atto <> atto_atteso THEN
    RAISE EXCEPTION 'l''atto % non è l''atto % % del lotto % in %', atto_id, atto_atteso, tipo, oggetto, spazio;
  END IF;
  RETURN r.dettagli;
END;
$$;

CREATE FUNCTION abbinamento_controlla_lotto() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  codice_parametro text;
  org_parametro uuid;
BEGIN
  PERFORM abbinamento_controlla_atto(NEW.decisione_id, TG_TABLE_SCHEMA, 'lotto_abbinamento', NEW.lotto_id, 'proposta');
  IF NEW.parametro_quota_id IS NOT NULL THEN
    SELECT codice, org_id INTO codice_parametro, org_parametro
    FROM parametri_governance WHERE parametro_id = NEW.parametro_quota_id;
    IF codice_parametro IS DISTINCT FROM 'quota_revisione_abbinamenti'
       OR (org_parametro IS NOT NULL AND org_parametro <> abbinamento_org_dello_spazio(TG_TABLE_SCHEMA)) THEN
      RAISE EXCEPTION 'il lotto % cita un parametro che non è la quota di revisione', NEW.lotto_id;
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

CREATE FUNCTION abbinamento_controlla_decisione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  lotto uuid;
  task uuid;
  livello text;
  dettagli jsonb;
BEGIN
  EXECUTE format('SELECT p.lotto_id, p.task_id, l.livello_revisione FROM %1$I.proposte_abbinamento p
                  JOIN %1$I.lotti_abbinamento l USING (lotto_id) WHERE p.proposta_id = $1', TG_TABLE_SCHEMA)
    INTO lotto, task, livello USING NEW.proposta_id;
  dettagli := abbinamento_controlla_atto(NEW.decisione_id, TG_TABLE_SCHEMA, 'lotto_abbinamento', lotto,
                                         'approvazione');
  IF NEW.esito = 'approvata' AND task IS NULL THEN
    RAISE EXCEPTION 'la proposta % non ha un task: non si approva', NEW.proposta_id;
  END IF;
  -- Con revisione a campione o completa la decisione cita la misura, salvo lotti senza proposte con un task.
  IF livello <> 'nulla' AND NOT (dettagli ? 'misura_id' OR (dettagli ->> 'proposte_con_task') = '0') THEN
    RAISE EXCEPTION 'la decisione del lotto % non cita la misura di precisione', lotto;
  END IF;
  RETURN NEW;
END;
$$;

CREATE FUNCTION abbinamento_controlla_applicazione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  lotto uuid;
  task_proposto uuid;
  esito text;
BEGIN
  EXECUTE format('SELECT p.lotto_id, p.task_id, d.esito FROM %1$I.proposte_abbinamento p
                  JOIN %1$I.decisioni_abbinamento d USING (proposta_id) WHERE p.proposta_id = $1', TG_TABLE_SCHEMA)
    INTO lotto, task_proposto, esito USING NEW.proposta_id;
  PERFORM abbinamento_controlla_atto(NEW.decisione_id, TG_TABLE_SCHEMA, 'applicazione_abbinamento', lotto,
                                     'approvazione');
  -- Approvata: il task del dataset proposto, o quello in cui è confluito, mai un task nuovo.
  IF esito = 'approvata' AND (NEW.task_nuovo OR NOT EXISTS (
       WITH RECURSIVE catena(task_id, merged_into) AS (
         SELECT t.task_id, t.merged_into FROM canonical_tasks t WHERE t.task_id = task_proposto
         UNION
         SELECT t.task_id, t.merged_into FROM canonical_tasks t JOIN catena c ON t.task_id = c.merged_into)
       SELECT 1 FROM catena WHERE task_id = NEW.task_id)) THEN
    RAISE EXCEPTION 'l''applicazione della proposta % non segue la decisione', NEW.proposta_id;
  END IF;
  RETURN NEW;
END;
$$;

-- A fine transazione un lotto è deciso, o applicato, per intero e con un solo atto. TG_ARGV[0]: la tabella.
CREATE FUNCTION abbinamento_lotto_intero() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  proposte bigint;
  righe bigint;
  atti bigint;
BEGIN
  EXECUTE format('SELECT count(*), count(x.proposta_id), count(DISTINCT x.decisione_id)
                  FROM %1$I.proposte_abbinamento p
                  LEFT JOIN %1$I.%2$I x USING (proposta_id)
                  WHERE p.lotto_id = (SELECT lotto_id FROM %1$I.proposte_abbinamento WHERE proposta_id = $1)',
                 TG_TABLE_SCHEMA, TG_ARGV[0])
    INTO proposte, righe, atti USING NEW.proposta_id;
  IF righe <> proposte OR atti <> 1 THEN
    RAISE EXCEPTION 'il lotto della proposta % non è stato trattato per intero con un solo atto (%)',
      NEW.proposta_id, TG_ARGV[0];
  END IF;
  RETURN NULL;
END;
$$;
