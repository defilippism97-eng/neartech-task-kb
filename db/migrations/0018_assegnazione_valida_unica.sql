-- Migrazione 0018: un'unica definizione di assegnazione valida (santa-loop, giro 4, 2026-10-16).
-- Si applica dopo la 0017.
-- Un'assegnazione è valida se non è chiusa, è iniziata e non è scaduta, all'istante dell'istruzione.
-- La usano il trigger e neartech.permessi (puo, conteggio degli amministratori, chiusura).
-- La chiusura avviene all'istante: niente chiusure con data futura, che renderebbero
-- un'assegnazione "chiusa ma ancora in corso". Ultimo amministratore e bootstrap sono
-- protetti anche nel database, sotto lo stesso lock usato dal codice.

CREATE FUNCTION assegnazione_valida(a assegnazioni_ruolo) RETURNS boolean
LANGUAGE sql STABLE SET search_path = public, pg_temp AS $$
  SELECT a.chiusa_da IS NULL
     AND a.valida_dal <= statement_timestamp()
     AND (a.valida_al IS NULL OR a.valida_al > statement_timestamp())
$$;

ALTER TABLE assegnazioni_ruolo ALTER COLUMN valida_dal SET DEFAULT statement_timestamp();

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
    IF NOT assegnazione_valida(OLD)
       OR (NEW.assegnazione_id, NEW.utente_id, NEW.ruolo, NEW.org_id, NEW.valida_dal, NEW.assegnata_da, NEW.creata_il)
          IS DISTINCT FROM
          (OLD.assegnazione_id, OLD.utente_id, OLD.ruolo, OLD.org_id, OLD.valida_dal, OLD.assegnata_da, OLD.creata_il) THEN
      RAISE EXCEPTION 'un''assegnazione di ruolo si può solo chiudere, una volta, finché è valida';
    END IF;
    IF NEW.chiusa_da IS NULL OR NEW.valida_al IS DISTINCT FROM istante THEN
      RAISE EXCEPTION 'la chiusura richiede chi chiude e avviene adesso (valida_al = statement_timestamp())';
    END IF;
    IF OLD.ruolo = 'amministratore_tecnico' THEN
      PERFORM pg_advisory_xact_lock(hashtext('inizializza_amministratore'));
      IF NOT EXISTS (SELECT 1 FROM assegnazioni_ruolo a
                     WHERE a.ruolo = 'amministratore_tecnico' AND a.utente_id <> OLD.utente_id
                       AND assegnazione_valida(a)) THEN
        RAISE EXCEPTION 'serve almeno un altro amministratore tecnico attivo';
      END IF;
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
  IF NEW.ruolo = 'amministratore_tecnico' THEN
    IF NEW.valida_al IS NOT NULL THEN
      RAISE EXCEPTION 'l''amministratore tecnico non si assegna a termine: si chiude quando serve';
    END IF;
    IF NEW.assegnata_da IS NULL THEN
      -- Bootstrap: ammesso solo se non esiste un amministratore valido.
      PERFORM pg_advisory_xact_lock(hashtext('inizializza_amministratore'));
      IF EXISTS (SELECT 1 FROM assegnazioni_ruolo a
                 WHERE a.ruolo = 'amministratore_tecnico' AND assegnazione_valida(a)) THEN
        RAISE EXCEPTION 'esiste già un amministratore tecnico: il bootstrap non si ripete';
      END IF;
    END IF;
  END IF;
  PERFORM pg_advisory_xact_lock(hashtext(
    'assegnazione:' || NEW.utente_id::text || ':' || NEW.ruolo || ':' || COALESCE(NEW.org_id::text, '')));
  IF (NEW.valida_al IS NULL OR NEW.valida_al > istante) AND EXISTS (
       SELECT 1 FROM assegnazioni_ruolo a
       WHERE a.utente_id = NEW.utente_id AND a.ruolo = NEW.ruolo
         AND a.org_id IS NOT DISTINCT FROM NEW.org_id
         AND assegnazione_valida(a)) THEN
    RAISE EXCEPTION 'esiste già un''assegnazione valida di % per questo utente', NEW.ruolo
      USING ERRCODE = 'unique_violation';
  END IF;
  RETURN NEW;
END;
$$;
