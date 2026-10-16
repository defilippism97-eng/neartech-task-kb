-- Migrazione 0017: validità dei ruoli valutata all'istante dell'istruzione (santa-loop, giro 3, 2026-10-16).
-- Si applica dopo la 0016. now() è l'ora di inizio della transazione: una transazione iniziata
-- prima di una chiusura la vedrebbe ancora valida. Controlli e chiusure usano statement_timestamp().
-- Le funzioni applicative (neartech.permessi) usano lo stesso orologio. Presuppone READ COMMITTED.

CREATE OR REPLACE FUNCTION controlla_assegnazione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  ambito_ruolo text;
  istante timestamptz := statement_timestamp();
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'le assegnazioni di ruolo non si cancellano: si chiudono con valida_al';
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF OLD.chiusa_da IS NOT NULL
       OR (OLD.valida_al IS NOT NULL AND OLD.valida_al <= istante)
       OR (NEW.assegnazione_id, NEW.utente_id, NEW.ruolo, NEW.org_id, NEW.valida_dal, NEW.assegnata_da, NEW.creata_il)
          IS DISTINCT FROM
          (OLD.assegnazione_id, OLD.utente_id, OLD.ruolo, OLD.org_id, OLD.valida_dal, OLD.assegnata_da, OLD.creata_il) THEN
      RAISE EXCEPTION 'un''assegnazione di ruolo si può solo chiudere, una volta, finché è valida';
    END IF;
    IF NEW.chiusa_da IS NULL OR NEW.valida_al IS NULL OR NEW.valida_al < istante
       OR NEW.valida_al > COALESCE(OLD.valida_al, 'infinity'::timestamptz) THEN
      RAISE EXCEPTION 'la chiusura richiede chi chiude e una data fra adesso e la scadenza prevista';
    END IF;
    RETURN NEW;
  END IF;
  SELECT ambito INTO ambito_ruolo FROM ruoli WHERE codice = NEW.ruolo;
  IF ambito_ruolo = 'organizzazione' AND NEW.org_id IS NULL THEN
    RAISE EXCEPTION 'il ruolo % richiede un''organizzazione', NEW.ruolo;
  END IF;
  IF ambito_ruolo = 'globale' AND NEW.org_id IS NOT NULL THEN
    RAISE EXCEPTION 'il ruolo % è globale e non ammette un''organizzazione', NEW.ruolo;
  END IF;
  IF NEW.ruolo = 'amministratore_tecnico' AND NEW.valida_al IS NOT NULL THEN
    RAISE EXCEPTION 'l''amministratore tecnico non si assegna a termine: si chiude quando serve';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtext(
    'assegnazione:' || NEW.utente_id::text || ':' || NEW.ruolo || ':' || COALESCE(NEW.org_id::text, '')));
  IF (NEW.valida_al IS NULL OR NEW.valida_al > istante) AND EXISTS (
       SELECT 1 FROM assegnazioni_ruolo a
       WHERE a.utente_id = NEW.utente_id AND a.ruolo = NEW.ruolo
         AND a.org_id IS NOT DISTINCT FROM NEW.org_id
         AND a.chiusa_da IS NULL
         AND (a.valida_al IS NULL OR a.valida_al > statement_timestamp())) THEN
    RAISE EXCEPTION 'esiste già un''assegnazione valida di % per questo utente', NEW.ruolo
      USING ERRCODE = 'unique_violation';
  END IF;
  RETURN NEW;
END;
$$;

-- L'identità SSO di un utente non si cambia: sposterebbe ruoli e storia su un'altra persona.
CREATE FUNCTION soggetto_sso_immutabile() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF NEW.soggetto_sso IS DISTINCT FROM OLD.soggetto_sso THEN
    RAISE EXCEPTION 'il soggetto SSO di un utente non si cambia';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER utenti_soggetto_immutabile
  BEFORE UPDATE OF soggetto_sso ON utenti
  FOR EACH ROW EXECUTE FUNCTION soggetto_sso_immutabile();
