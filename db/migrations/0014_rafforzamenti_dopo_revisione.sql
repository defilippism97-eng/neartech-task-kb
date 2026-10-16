-- Migrazione 0014: rafforzamenti dopo le revisioni di database e sicurezza (2026-10-16).
-- Si applica dopo la 0013. Non modifica le migrazioni precedenti.
-- Limite dichiarato: i trigger rendono le tabelle append-only per l'applicazione, non per
-- il proprietario delle tabelle o un superuser, che può disattivarli. La catena di hash
-- del registro, con un'ancora conservata fuori dal database, rende visibile la manomissione
-- ma non la impedisce. In produzione l'applicazione deve usare un ruolo senza proprietà.

-- 1. Funzioni con search_path fisso: non devono risolvere oggetti negli schemi org_<codice>.
ALTER FUNCTION vieta_modifiche() SET search_path = public, pg_temp;
ALTER FUNCTION registro_hash(registro_decisioni) SET search_path = public, pg_temp;
ALTER FUNCTION registro_concatena() SET search_path = public, pg_temp;

-- 2. TRUNCATE vietato su tutte le tabelle append-only; registro migrazioni, ruoli e
-- matrice dei permessi non si modificano (un cambio richiede una migrazione che, come
-- proprietaria, disattiva il trigger in modo esplicito e visibile nel file).
CREATE TRIGGER parametri_no_truncate BEFORE TRUNCATE ON parametri_governance
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER indirizzi_no_truncate BEFORE TRUNCATE ON indirizzi_comitato
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER stati_validazione_no_truncate BEFORE TRUNCATE ON stati_validazione_task
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER assegnazioni_no_truncate BEFORE TRUNCATE ON assegnazioni_ruolo
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER migrazioni_append_only BEFORE UPDATE OR DELETE ON migrazioni_applicate
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER migrazioni_no_truncate BEFORE TRUNCATE ON migrazioni_applicate
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER ruoli_append_only BEFORE UPDATE OR DELETE ON ruoli
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER ruoli_no_truncate BEFORE TRUNCATE ON ruoli
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER permessi_append_only BEFORE UPDATE OR DELETE ON permessi_ruolo
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER permessi_no_truncate BEFORE TRUNCATE ON permessi_ruolo
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();

-- 3. Assegnazioni di ruolo: chi chiude è registrato, la chiusura non si retrodata,
-- una sola assegnazione aperta per utente, ruolo e organizzazione.
ALTER TABLE assegnazioni_ruolo ADD COLUMN chiusa_da uuid REFERENCES utenti;
CREATE UNIQUE INDEX assegnazioni_una_aperta
  ON assegnazioni_ruolo (utente_id, ruolo, COALESCE(org_id, '00000000-0000-0000-0000-000000000000'::uuid))
  WHERE valida_al IS NULL;

CREATE OR REPLACE FUNCTION controlla_assegnazione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  ambito_ruolo text;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'le assegnazioni di ruolo non si cancellano: si chiudono con valida_al';
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF OLD.valida_al IS NOT NULL
       OR (NEW.assegnazione_id, NEW.utente_id, NEW.ruolo, NEW.org_id, NEW.valida_dal, NEW.assegnata_da, NEW.creata_il)
          IS DISTINCT FROM
          (OLD.assegnazione_id, OLD.utente_id, OLD.ruolo, OLD.org_id, OLD.valida_dal, OLD.assegnata_da, OLD.creata_il) THEN
      RAISE EXCEPTION 'un''assegnazione di ruolo si può solo chiudere, una volta';
    END IF;
    IF NEW.chiusa_da IS NULL OR NEW.valida_al IS NULL OR NEW.valida_al < now() THEN
      RAISE EXCEPTION 'la chiusura richiede chi chiude e una data non anteriore a oggi';
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
  RETURN NEW;
END;
$$;

-- 4. Registro: un solo atto decisivo (approvazione o rifiuto) e un solo ritiro per
-- parametro o indirizzo; un atto decisivo richiede che l'oggetto esista; un ritiro
-- richiede un'approvazione; una correzione riguarda lo stesso oggetto.
CREATE UNIQUE INDEX registro_una_decisione ON registro_decisioni (tipo_oggetto, oggetto_id)
  WHERE atto IN ('approvazione', 'rifiuto') AND tipo_oggetto IN ('parametro', 'indirizzo');
CREATE UNIQUE INDEX registro_un_ritiro ON registro_decisioni (tipo_oggetto, oggetto_id)
  WHERE atto = 'ritiro' AND tipo_oggetto IN ('parametro', 'indirizzo');
CREATE INDEX registro_atti_decisivi ON registro_decisioni (tipo_oggetto, oggetto_id, posizione DESC)
  WHERE atto IN ('approvazione', 'rifiuto', 'ritiro');

CREATE FUNCTION registro_controlla_oggetto() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF NEW.atto IN ('approvazione', 'rifiuto', 'ritiro') THEN
    IF NEW.tipo_oggetto = 'parametro'
       AND NOT EXISTS (SELECT 1 FROM parametri_governance WHERE parametro_id::text = NEW.oggetto_id) THEN
      RAISE EXCEPTION 'parametro % inesistente', NEW.oggetto_id;
    END IF;
    IF NEW.tipo_oggetto = 'indirizzo'
       AND NOT EXISTS (SELECT 1 FROM indirizzi_comitato WHERE indirizzo_id::text = NEW.oggetto_id) THEN
      RAISE EXCEPTION 'indirizzo % inesistente', NEW.oggetto_id;
    END IF;
    IF NEW.atto = 'ritiro' AND NEW.tipo_oggetto IN ('parametro', 'indirizzo')
       AND NOT EXISTS (SELECT 1 FROM registro_decisioni
                       WHERE tipo_oggetto = NEW.tipo_oggetto AND oggetto_id = NEW.oggetto_id
                         AND atto = 'approvazione') THEN
      RAISE EXCEPTION 'si ritira solo una versione approvata';
    END IF;
  END IF;
  IF NEW.corregge_id IS NOT NULL
     AND NOT EXISTS (SELECT 1 FROM registro_decisioni
                     WHERE decisione_id = NEW.corregge_id
                       AND tipo_oggetto = NEW.tipo_oggetto AND oggetto_id = NEW.oggetto_id) THEN
    RAISE EXCEPTION 'una correzione riguarda lo stesso oggetto dell''atto corretto';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER registro_controlla_oggetto
  BEFORE INSERT ON registro_decisioni
  FOR EACH ROW EXECUTE FUNCTION registro_controlla_oggetto();

-- La proposta indicata da un parametro o da un indirizzo è la sua (stesso oggetto, atto proposta).
-- TG_ARGV: tipo di oggetto nel registro, nome della colonna chiave.
CREATE FUNCTION controlla_proposta() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM registro_decisioni
                 WHERE decisione_id = NEW.proposta_id AND tipo_oggetto = TG_ARGV[0]
                   AND oggetto_id = to_jsonb(NEW) ->> TG_ARGV[1] AND atto = 'proposta') THEN
    RAISE EXCEPTION 'la proposta % non riguarda questo %', NEW.proposta_id, TG_ARGV[0];
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER parametri_controlla_proposta BEFORE INSERT ON parametri_governance
  FOR EACH ROW EXECUTE FUNCTION controlla_proposta('parametro', 'parametro_id');
CREATE TRIGGER indirizzi_controlla_proposta BEFORE INSERT ON indirizzi_comitato
  FOR EACH ROW EXECUTE FUNCTION controlla_proposta('indirizzo', 'indirizzo_id');

-- Un cambio di stato di validazione rimanda a una decisione sullo stesso task.
CREATE FUNCTION controlla_decisione_stato() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM registro_decisioni
                 WHERE decisione_id = NEW.decisione_id AND tipo_oggetto = 'stato_task'
                   AND oggetto_id = NEW.task_id::text) THEN
    RAISE EXCEPTION 'la decisione % non riguarda il task %', NEW.decisione_id, NEW.task_id;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER stati_validazione_controlla_decisione BEFORE INSERT ON stati_validazione_task
  FOR EACH ROW EXECUTE FUNCTION controlla_decisione_stato();

-- Stato corrente nell'ordine del registro, non nell'ordine di allocazione degli identificativi.
CREATE OR REPLACE VIEW stato_validazione_corrente AS
SELECT t.task_id, COALESCE(s.stato, 'da_integrare') AS stato, s.decisione_id
FROM canonical_tasks t
LEFT JOIN LATERAL (
  SELECT v.stato, v.decisione_id
  FROM stati_validazione_task v JOIN registro_decisioni r ON r.decisione_id = v.decisione_id
  WHERE v.task_id = t.task_id ORDER BY r.posizione DESC LIMIT 1
) s ON true;

-- 5. Coda dei job: dati esistenti coerenti, poi vincoli di stato; indice per l'ordine di presa.
UPDATE jobs SET preso_il = created_at WHERE status = 'running' AND preso_il IS NULL;
UPDATE jobs SET completato_il = created_at WHERE status = 'done' AND completato_il IS NULL;
UPDATE jobs SET tentativi_massimi = attempts WHERE attempts > tentativi_massimi;
ALTER TABLE jobs
  ADD CONSTRAINT jobs_in_corso_ha_presa CHECK (status <> 'running' OR preso_il IS NOT NULL),
  ADD CONSTRAINT jobs_completato_ha_data CHECK (status <> 'done' OR completato_il IS NOT NULL),
  ADD CONSTRAINT jobs_tentativi_entro_massimo CHECK (attempts <= tentativi_massimi);
DROP INDEX jobs_in_coda;
CREATE INDEX jobs_in_coda ON jobs (run_after, created_at) WHERE status = 'queued';

-- 6. Indici sulle chiavi esterne.
CREATE INDEX assegnazioni_org ON assegnazioni_ruolo (org_id);
CREATE INDEX assegnazioni_assegnata_da ON assegnazioni_ruolo (assegnata_da);
CREATE INDEX assegnazioni_chiusa_da ON assegnazioni_ruolo (chiusa_da);
CREATE INDEX log_accessi_org ON log_accessi (org_id);
CREATE INDEX registro_autore ON registro_decisioni (autore_id);
CREATE INDEX registro_corregge ON registro_decisioni (corregge_id);
CREATE INDEX parametri_org ON parametri_governance (org_id);
CREATE INDEX parametri_proposta ON parametri_governance (proposta_id);
CREATE INDEX indirizzi_proposta ON indirizzi_comitato (proposta_id);
CREATE INDEX stati_validazione_decisione ON stati_validazione_task (decisione_id);
CREATE INDEX jobs_org ON jobs (org_id);
