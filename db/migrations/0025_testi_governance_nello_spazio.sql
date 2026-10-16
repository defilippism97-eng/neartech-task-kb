-- Migrazione 0025: testi di governance dell'organizzazione nel suo spazio (ADR 0004) e
-- parametri comuni esaminati dal comitato guida (metodologia, sezione 10, decisioni b e g).
-- Si applica dopo la 0024 e prima della migrazione 0006 degli spazi (stesso giro di migra.py).
-- In produzione non ci sono indirizzi né parametri di organizzazioni: i vincoli valgono subito.

-- 1. Indirizzi: testo e ambito solo nello spazio; in public restano codice, versione e l'hash nella proposta.
ALTER TABLE indirizzi_comitato ALTER COLUMN testo DROP NOT NULL, ALTER COLUMN ambito DROP NOT NULL;
ALTER TABLE indirizzi_comitato ADD CONSTRAINT indirizzi_senza_testo CHECK (testo IS NULL AND ambito IS NULL);

-- 2. Parametri: la descrizione dei parametri comuni resta in public, quella dei parametri di
--    un'organizzazione sta nel suo spazio.
ALTER TABLE parametri_governance ALTER COLUMN descrizione DROP NOT NULL;
ALTER TABLE parametri_governance ADD CONSTRAINT parametri_descrizione_nello_spazio
  CHECK ((org_id IS NULL) = (descrizione IS NOT NULL));

-- 3. Atti nuovi: adozione di un parametro comune e richiesta di ricalibrazione, del comitato guida.
ALTER TABLE registro_decisioni DROP CONSTRAINT registro_decisioni_atto_check;
ALTER TABLE registro_decisioni ADD CONSTRAINT registro_decisioni_atto_check CHECK (atto IN
  ('proposta', 'approvazione', 'rifiuto', 'ritiro', 'segnalazione', 'blocco', 'correzione',
   'adozione', 'richiesta_ricalibrazione'));
CREATE UNIQUE INDEX registro_una_adozione ON registro_decisioni (org_id, oggetto_id)
  WHERE atto = 'adozione';

-- 4. Atti di un'organizzazione con spazio: motivazione sostituita dal marcatore, hash del testo nei dettagli
--    (neartech.registro.registra). Adozione e ricalibrazione solo su parametri comuni, da un'organizzazione.
CREATE FUNCTION registro_testo_nello_spazio() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF NEW.org_id IS NOT NULL
     AND EXISTS (SELECT 1 FROM organizations WHERE org_id = NEW.org_id AND codice IS NOT NULL)
     AND (NEW.motivazione <> 'nello spazio dell''organizzazione' OR NOT NEW.dettagli ? 'hash_testo') THEN
    RAISE EXCEPTION 'il testo degli atti di un''organizzazione sta nel suo spazio (ADR 0004)';
  END IF;
  IF NEW.atto IN ('adozione', 'richiesta_ricalibrazione')
     AND (NEW.tipo_oggetto <> 'parametro' OR NEW.org_id IS NULL
          OR NOT EXISTS (SELECT 1 FROM parametri_governance
                         WHERE parametro_id::text = NEW.oggetto_id AND org_id IS NULL)) THEN
    RAISE EXCEPTION 'adozione e ricalibrazione riguardano un parametro comune, per un''organizzazione';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER registro_testo_nello_spazio
  BEFORE INSERT ON registro_decisioni
  FOR EACH ROW EXECUTE FUNCTION registro_testo_nello_spazio();

-- 5. Permessi del comitato guida.
ALTER TABLE permessi_ruolo DISABLE TRIGGER permessi_no_insert;
INSERT INTO permessi_ruolo (ruolo, azione) VALUES
  ('comitato_guida', 'adottare_parametro_comune'),
  ('comitato_guida', 'chiedere_ricalibrazione');
ALTER TABLE permessi_ruolo ENABLE TRIGGER permessi_no_insert;
