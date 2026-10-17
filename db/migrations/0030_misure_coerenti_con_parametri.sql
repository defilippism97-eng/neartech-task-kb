-- Migrazione 0030: i valori usati da una misura sono quelli dei parametri che cita (seguito della
-- revisione del 2026-10-17). Si applica dopo la 0029.
-- La 0020 controlla che i parametri citati abbiano il codice atteso; ora anche soglia, livello di
-- confidenza e regola sui parziali devono coincidere con il campo "valore" del parametro citato
-- (neartech.metrica legge lo stesso campo). Il confronto è fra jsonb: i numeri si confrontano come
-- numeri, quindi 0.9 e 0.90 coincidono. Nessun valore di policy nel vincolo.

SET LOCAL lock_timeout = '10s';

CREATE FUNCTION controlla_valori_misura() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF (SELECT valore -> 'valore' FROM parametri_governance WHERE parametro_id = NEW.parametro_soglia_id)
       IS DISTINCT FROM to_jsonb(NEW.soglia)
     OR (SELECT valore -> 'valore' FROM parametri_governance WHERE parametro_id = NEW.parametro_confidenza_id)
       IS DISTINCT FROM to_jsonb(NEW.livello_confidenza)
     OR (SELECT valore -> 'valore' FROM parametri_governance WHERE parametro_id = NEW.parametro_regola_id)
       IS DISTINCT FROM to_jsonb(NEW.regola_parziali) THEN
    RAISE EXCEPTION 'i valori della misura non coincidono con quelli dei parametri citati';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER misure_controlla_valori BEFORE INSERT ON misure_precisione
  FOR EACH ROW EXECUTE FUNCTION controlla_valori_misura();
