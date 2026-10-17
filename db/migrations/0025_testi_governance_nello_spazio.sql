-- Migrazione 0025: testi di governance dell'organizzazione nel suo spazio (ADR 0004) e
-- parametri comuni esaminati dal comitato guida (metodologia, sezione 10, decisioni b e g).
-- Si applica dopo la 0024, nello stesso giro di migra.py che porta gli spazi alla 0006: tra le due
-- l'applicazione non scrive atti delle organizzazioni (applicare con l'applicazione ferma).
-- In produzione non ci sono indirizzi né parametri di organizzazioni e ogni organizzazione ha uno spazio:
-- i vincoli valgono subito (verificato in sola lettura il 2026-10-17).

SET LOCAL lock_timeout = '10s';

-- 1. Indirizzi: testo e ambito solo nello spazio; in public restano codice, versione e l'impronta nella
--    proposta. Le colonne restano, sempre vuote (tabella append-only).
ALTER TABLE indirizzi_comitato ALTER COLUMN testo DROP NOT NULL, ALTER COLUMN ambito DROP NOT NULL;
ALTER TABLE indirizzi_comitato ADD CONSTRAINT indirizzi_senza_testo CHECK (testo IS NULL AND ambito IS NULL);

-- 2. Parametri: la descrizione dei parametri comuni resta in public, quella dei parametri di
--    un'organizzazione sta nel suo spazio.
ALTER TABLE parametri_governance ALTER COLUMN descrizione DROP NOT NULL;
ALTER TABLE parametri_governance ADD CONSTRAINT parametri_descrizione_nello_spazio
  CHECK ((org_id IS NULL) = (descrizione IS NOT NULL));

-- 3. Completamento della 0023: famiglia dei ruoli e uri/versione dei documenti dell'organizzazione non
--    portano testo (la versione è l'inizio dell'impronta del file).
ALTER TABLE roles ADD CONSTRAINT roles_senza_famiglia CHECK (family IS NULL);
ALTER TABLE sources ADD CONSTRAINT sources_documento_senza_testo
  CHECK (kind <> 'org_document' OR (uri IS NULL AND version ~ '^[0-9a-f]{16}$'));

-- 4. Completamento della 0020: nessun identificativo nullo nel riferimento di un elemento di campione.
ALTER TABLE elementi_campione ADD CONSTRAINT elementi_riferimento_senza_nulli
  CHECK (NOT jsonb_path_exists(riferimento, '$.* ? (@ == null)'));

-- 5. Atti nuovi: adozione di un parametro comune e richiesta di ricalibrazione, del comitato guida.
ALTER TABLE registro_decisioni DROP CONSTRAINT registro_decisioni_atto_check;
ALTER TABLE registro_decisioni ADD CONSTRAINT registro_decisioni_atto_check CHECK (atto IN
  ('proposta', 'approvazione', 'rifiuto', 'ritiro', 'segnalazione', 'blocco', 'correzione',
   'adozione', 'richiesta_ricalibrazione'));
CREATE UNIQUE INDEX registro_una_adozione ON registro_decisioni (org_id, oggetto_id)
  WHERE atto = 'adozione';

-- 6. Atti di un'organizzazione: nel registro condiviso solo il marcatore, l'impronta del testo e dettagli
--    strutturali (numeri, valori logici, codici e identificativi senza spazi); il testo sta nello spazio
--    (neartech.registro.registra). Vale per ogni organizzazione: senza spazio non si registrano atti.
--    Adozione e ricalibrazione solo sulla versione comune vigente, da un'organizzazione.
--    Nota: i trigger BEFORE INSERT del registro scattano in ordine di nome; registro_concatena calcola
--    l'hash della riga, quindi un trigger successivo non deve modificare NEW.
CREATE FUNCTION registro_testo_nello_spazio() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF NEW.org_id IS NOT NULL THEN
    IF NEW.motivazione <> 'nello spazio dell''organizzazione'
       OR jsonb_typeof(NEW.dettagli) <> 'object'
       OR coalesce(NEW.dettagli ->> 'hash_testo', '') !~ '^[0-9a-f]{64}$' THEN
      RAISE EXCEPTION 'il testo degli atti di un''organizzazione sta nel suo spazio (ADR 0004)';
    END IF;
    -- Stesso formato di neartech.registro.FORMATO_CODICE.
    IF NEW.oggetto_id !~ '^[A-Za-z0-9_.:+@|-]{1,64}$'
       OR jsonb_path_exists(NEW.dettagli,
            '$.** ? (@.type() == "string" && !(@ like_regex "^[A-Za-z0-9_.:+@|-]{1,64}$"))') THEN
      RAISE EXCEPTION 'dettagli e oggetto di un atto di un''organizzazione: solo codici, numeri e identificativi';
    END IF;
  END IF;
  IF NEW.atto IN ('adozione', 'richiesta_ricalibrazione')
     AND (NEW.tipo_oggetto <> 'parametro' OR NEW.org_id IS NULL
          OR NOT EXISTS (SELECT 1 FROM parametri_vigenti
                         WHERE parametro_id::text = NEW.oggetto_id AND org_id IS NULL)) THEN
    RAISE EXCEPTION 'adozione e ricalibrazione riguardano la versione comune vigente, per un''organizzazione';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER registro_testo_nello_spazio
  BEFORE INSERT ON registro_decisioni
  FOR EACH ROW EXECUTE FUNCTION registro_testo_nello_spazio();

-- Alla fine della transazione ogni atto di un'organizzazione ha il suo testo nello spazio.
CREATE FUNCTION registro_testo_presente() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  codice_org text;
  presente boolean;
BEGIN
  SELECT codice INTO codice_org FROM organizations WHERE org_id = NEW.org_id;
  IF codice_org IS NULL OR to_regclass(format('%I.testi_atti', 'org_' || codice_org)) IS NULL THEN
    RAISE EXCEPTION 'l''organizzazione % non ha uno spazio per i testi', NEW.org_id;
  END IF;
  EXECUTE format('SELECT EXISTS (SELECT 1 FROM %I.testi_atti WHERE decisione_id = $1)', 'org_' || codice_org)
    INTO presente USING NEW.decisione_id;
  IF NOT presente THEN
    RAISE EXCEPTION 'atto % senza testo nello spazio dell''organizzazione', NEW.decisione_id;
  END IF;
  RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER registro_testo_presente
  AFTER INSERT ON registro_decisioni DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW WHEN (NEW.org_id IS NOT NULL)
  EXECUTE FUNCTION registro_testo_presente();

-- 7. I testi nello spazio di un'organizzazione riguardano solo atti, indirizzi e parametri suoi
--    (trigger delle tabelle testi_* nella migrazione 0006 degli spazi). TG_ARGV[0]: atto, indirizzo, parametro.
CREATE FUNCTION testo_della_propria_organizzazione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  org_testo uuid;
  org_spazio uuid;
BEGIN
  SELECT org_id INTO org_spazio FROM organizations WHERE 'org_' || codice = TG_TABLE_SCHEMA;
  -- Rami separati: PL/pgSQL risolve i campi di NEW solo nel ramo eseguito.
  IF TG_ARGV[0] = 'atto' THEN
    SELECT org_id INTO org_testo FROM registro_decisioni WHERE decisione_id = NEW.decisione_id;
  ELSIF TG_ARGV[0] = 'indirizzo' THEN
    SELECT org_id INTO org_testo FROM indirizzi_comitato WHERE indirizzo_id = NEW.indirizzo_id;
  ELSIF TG_ARGV[0] = 'parametro' THEN
    SELECT org_id INTO org_testo FROM parametri_governance WHERE parametro_id = NEW.parametro_id;
  END IF;
  IF org_spazio IS NULL OR org_testo IS DISTINCT FROM org_spazio THEN
    RAISE EXCEPTION 'testo di un''altra organizzazione nello spazio %', TG_TABLE_SCHEMA;
  END IF;
  RETURN NEW;
END;
$$;

-- 8. Permessi del comitato guida.
ALTER TABLE permessi_ruolo DISABLE TRIGGER permessi_no_insert;
INSERT INTO permessi_ruolo (ruolo, azione) VALUES
  ('comitato_guida', 'adottare_parametro_comune'),
  ('comitato_guida', 'chiedere_ricalibrazione');
ALTER TABLE permessi_ruolo ENABLE TRIGGER permessi_no_insert;

-- 9. Le sequenze future di public sono utilizzabili dall'applicazione (gli INSERT si concedono
--    comunque tabella per tabella).
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO neartech_app;
