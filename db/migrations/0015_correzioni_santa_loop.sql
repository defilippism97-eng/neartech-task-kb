-- Migrazione 0015: correzioni dalla revisione incrociata (santa-loop, giro 1, 2026-10-16).
-- Si applica dopo la 0014.

-- 1. Assegnazioni di ruolo. Un'assegnazione a termine si può revocare prima della scadenza
-- (solo accorciando la validità); due assegnazioni ancora valide per lo stesso utente,
-- ruolo e organizzazione non possono coesistere, anche se a termine.
CREATE OR REPLACE FUNCTION controlla_assegnazione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  ambito_ruolo text;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'le assegnazioni di ruolo non si cancellano: si chiudono con valida_al';
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF OLD.chiusa_da IS NOT NULL
       OR (OLD.valida_al IS NOT NULL AND OLD.valida_al <= now())
       OR (NEW.assegnazione_id, NEW.utente_id, NEW.ruolo, NEW.org_id, NEW.valida_dal, NEW.assegnata_da, NEW.creata_il)
          IS DISTINCT FROM
          (OLD.assegnazione_id, OLD.utente_id, OLD.ruolo, OLD.org_id, OLD.valida_dal, OLD.assegnata_da, OLD.creata_il) THEN
      RAISE EXCEPTION 'un''assegnazione di ruolo si può solo chiudere, una volta, finché è valida';
    END IF;
    IF NEW.chiusa_da IS NULL OR NEW.valida_al IS NULL OR NEW.valida_al < now()
       OR NEW.valida_al > COALESCE(OLD.valida_al, 'infinity'::timestamptz) THEN
      RAISE EXCEPTION 'la chiusura richiede chi chiude e una data fra oggi e la scadenza prevista';
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
  IF (NEW.valida_al IS NULL OR NEW.valida_al > now()) AND EXISTS (
       SELECT 1 FROM assegnazioni_ruolo a
       WHERE a.utente_id = NEW.utente_id AND a.ruolo = NEW.ruolo
         AND a.org_id IS NOT DISTINCT FROM NEW.org_id
         AND (a.valida_al IS NULL OR a.valida_al > now())) THEN
    RAISE EXCEPTION 'esiste già un''assegnazione valida di % per questo utente', NEW.ruolo
      USING ERRCODE = 'unique_violation';
  END IF;
  RETURN NEW;
END;
$$;

-- 2. Il codice di un'organizzazione si assegna una volta: lega l'organizzazione al suo schema.
CREATE FUNCTION codice_organizzazione_immutabile() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF OLD.codice IS NOT NULL AND NEW.codice IS DISTINCT FROM OLD.codice THEN
    RAISE EXCEPTION 'il codice dell''organizzazione non si cambia: è il nome del suo spazio';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER organizzazioni_codice_immutabile
  BEFORE UPDATE OF codice ON organizations
  FOR EACH ROW EXECUTE FUNCTION codice_organizzazione_immutabile();
