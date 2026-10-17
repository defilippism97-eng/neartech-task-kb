-- Migrazione 0032: il livello di revisione di un lotto di abbinamento lo sceglie il revisore con un atto
-- (registro di metodo, sezione 17). Si applica dopo la 0031, nello stesso giro di migra.py che porta gli
-- spazi alla 0009 (tabella livelli_lotto). Fino a oggi in produzione non esistono lotti.

SET LOCAL lock_timeout = '10s';

-- Il livello e la quota stanno in livelli_lotto; la riga del lotto non li porta più.
CREATE FUNCTION abbinamento_controlla_livello() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  codice_parametro text;
  org_parametro uuid;
  dettagli jsonb;
BEGIN
  dettagli := abbinamento_controlla_atto(NEW.decisione_id, TG_TABLE_SCHEMA, 'livello_lotto_abbinamento',
                                         NEW.lotto_id, 'approvazione');
  IF dettagli ->> 'livello_revisione' IS DISTINCT FROM NEW.livello_revisione THEN
    RAISE EXCEPTION 'il livello del lotto % non è quello dell''atto citato', NEW.lotto_id;
  END IF;
  IF (NEW.livello_revisione = 'campione') <> (NEW.parametro_quota_id IS NOT NULL) THEN
    RAISE EXCEPTION 'il livello a campione del lotto % cita la quota, gli altri no', NEW.lotto_id;
  END IF;
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

-- La decisione legge il livello da livelli_lotto: senza livello scelto non si decide.
CREATE OR REPLACE FUNCTION abbinamento_controlla_decisione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  lotto uuid;
  task uuid;
  livello text;
  dettagli jsonb;
BEGIN
  EXECUTE format('SELECT p.lotto_id, p.task_id, v.livello_revisione FROM %1$I.proposte_abbinamento p
                  LEFT JOIN %1$I.livelli_lotto v USING (lotto_id) WHERE p.proposta_id = $1', TG_TABLE_SCHEMA)
    INTO lotto, task, livello USING NEW.proposta_id;
  IF livello IS NULL THEN
    RAISE EXCEPTION 'il lotto % non ha un livello di revisione scelto dal revisore', lotto;
  END IF;
  dettagli := abbinamento_controlla_atto(NEW.decisione_id, TG_TABLE_SCHEMA, 'lotto_abbinamento', lotto,
                                         'approvazione');
  IF NEW.esito = 'approvata' AND task IS NULL THEN
    RAISE EXCEPTION 'la proposta % non ha un task: non si approva', NEW.proposta_id;
  END IF;
  IF livello <> 'nulla' AND NOT (dettagli ? 'misura_id' OR (dettagli ->> 'proposte_con_task') = '0') THEN
    RAISE EXCEPTION 'la decisione del lotto % non cita la misura di precisione', lotto;
  END IF;
  RETURN NEW;
END;
$$;
