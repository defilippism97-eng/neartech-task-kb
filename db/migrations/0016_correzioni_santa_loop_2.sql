-- Migrazione 0016: correzioni dalla revisione incrociata (santa-loop, giro 2, 2026-10-16).
-- Si applica dopo la 0015.

-- 1. Assegnazioni di ruolo: il controllo dei duplicati è serializzato per utente, ruolo e
-- organizzazione (due transazioni contemporanee non creano due assegnazioni valide);
-- l'amministratore tecnico non si assegna a termine, così la protezione dell'ultimo
-- amministratore non viene aggirata da una scadenza.
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
  IF NEW.ruolo = 'amministratore_tecnico' AND NEW.valida_al IS NOT NULL THEN
    RAISE EXCEPTION 'l''amministratore tecnico non si assegna a termine: si chiude quando serve';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtext(
    'assegnazione:' || NEW.utente_id::text || ':' || NEW.ruolo || ':' || COALESCE(NEW.org_id::text, '')));
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

-- 2. Log di accesso senza chiavi esterne: scritto su una connessione dedicata, deve poter
-- registrare utenti e organizzazioni non ancora confermati e non prendere lock sulle tabelle
-- che la transazione di chi chiama sta modificando. Gli identificativi restano come dati.
ALTER TABLE log_accessi DROP CONSTRAINT IF EXISTS log_accessi_utente_id_fkey;
ALTER TABLE log_accessi DROP CONSTRAINT IF EXISTS log_accessi_org_id_fkey;

-- 3. Ruoli e matrice dei permessi: anche un'aggiunta richiede una migrazione, che disattiva
-- il trigger in modo esplicito.
CREATE TRIGGER ruoli_no_insert BEFORE INSERT ON ruoli
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER permessi_no_insert BEFORE INSERT ON permessi_ruolo
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();

-- 4. Un cambio di stato di validazione rimanda a un'approvazione sullo stesso task.
CREATE OR REPLACE FUNCTION controlla_decisione_stato() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM registro_decisioni
                 WHERE decisione_id = NEW.decisione_id AND tipo_oggetto = 'stato_task'
                   AND oggetto_id = NEW.task_id::text AND atto = 'approvazione') THEN
    RAISE EXCEPTION 'la decisione % non è un''approvazione sul task %', NEW.decisione_id, NEW.task_id;
  END IF;
  RETURN NEW;
END;
$$;

-- 5. Job in coda già tentati: un tentativo in più disponibile, altrimenti non sarebbero mai presi.
UPDATE jobs SET tentativi_massimi = attempts + 1 WHERE status = 'queued' AND attempts >= tentativi_massimi;
