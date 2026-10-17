-- Migrazione 0037: indirizzi del comitato e verifica dell'auditor (fase 6, fetta 3; registro di metodo, sezione 27).
-- Si applica dopo la 0036.
-- 1. Atto nuovo "verifica": l'ok dell'auditor su un profilo di pesi approvato dal comitato.
-- 2. Permesso dell'auditor per verificare i profili di pesi.
-- 3. L'applicazione può approvare e attivare un profilo di pesi di un'organizzazione solo se nel registro ci
--    sono l'approvazione del comitato e la verifica dell'auditor; il profilo comune resta del proprietario.

SET LOCAL lock_timeout = '10s';

ALTER TABLE registro_decisioni DROP CONSTRAINT registro_decisioni_atto_check;
ALTER TABLE registro_decisioni ADD CONSTRAINT registro_decisioni_atto_check CHECK (atto IN
  ('proposta', 'approvazione', 'rifiuto', 'ritiro', 'segnalazione', 'blocco', 'correzione',
   'adozione', 'richiesta_ricalibrazione', 'verifica'));

ALTER TABLE permessi_ruolo DISABLE TRIGGER permessi_no_insert;
INSERT INTO permessi_ruolo (ruolo, azione) VALUES ('auditor', 'verificare_profilo');
ALTER TABLE permessi_ruolo ENABLE TRIGGER permessi_no_insert;

GRANT UPDATE (approved_by, approved_at, is_active) ON weight_profiles TO neartech_app;

CREATE FUNCTION profilo_attivabile() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  proprietario name;
BEGIN
  SELECT tableowner INTO proprietario FROM pg_tables WHERE schemaname = 'public' AND tablename = 'weight_profiles';
  IF pg_has_role(current_user, proprietario, 'MEMBER') THEN
    RETURN NEW;
  END IF;
  IF (OLD.approved_by IS NULL AND NEW.approved_by IS NOT NULL) OR (NEW.is_active AND NOT OLD.is_active) THEN
    IF NEW.org_id IS NULL THEN
      RAISE EXCEPTION 'il profilo comune si approva con la procedura del proprietario';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM registro_decisioni WHERE tipo_oggetto = 'profilo_pesi' AND oggetto_id = NEW.profile_id
                   AND org_id = NEW.org_id AND atto = 'approvazione')
       OR NOT EXISTS (SELECT 1 FROM registro_decisioni WHERE tipo_oggetto = 'profilo_pesi' AND oggetto_id = NEW.profile_id
                      AND org_id = NEW.org_id AND atto = 'verifica') THEN
      RAISE EXCEPTION 'il profilo % si attiva solo con l''approvazione del comitato e la verifica dell''auditor', NEW.profile_id;
    END IF;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER profili_attivabili BEFORE UPDATE ON weight_profiles
  FOR EACH ROW EXECUTE FUNCTION profilo_attivabile();

-- Un profilo si approva e si verifica una volta.
CREATE UNIQUE INDEX registro_una_approvazione_profilo ON registro_decisioni (org_id, oggetto_id)
  WHERE tipo_oggetto = 'profilo_pesi' AND atto = 'approvazione';
CREATE UNIQUE INDEX registro_una_verifica_profilo ON registro_decisioni (org_id, oggetto_id)
  WHERE tipo_oggetto = 'profilo_pesi' AND atto = 'verifica';
