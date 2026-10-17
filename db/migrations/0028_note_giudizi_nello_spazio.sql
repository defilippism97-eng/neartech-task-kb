-- Migrazione 0028: le note dei revisori stanno nello spazio dell'organizzazione (ADR 0004; seguito della
-- revisione del 2026-10-17). Si applica dopo la 0027, nello stesso giro di migra.py che porta gli spazi
-- alla 0007 (applicare con l'applicazione ferma: tra le due neartech.campioni non registra note).
-- giudizi_revisione.nota è testo libero del revisore: va in org_<codice>.note_giudizi, come le motivazioni
-- degli atti in testi_atti. In public resta hash_nota, l'impronta della nota con la chiave dello spazio
-- (stessa formula di neartech.registro.impronta). Il giudizio resta un record solo: esito, revisore e
-- versione della rubrica non cambiano.
-- Il vincolo giudizi_nota_nello_spazio è NOT VALID: vale subito per le righe nuove; le note già presenti
-- le sposta la migrazione 0007 degli spazi (sposta_note_giudizi). Una migrazione successiva lo convalida.

SET LOCAL lock_timeout = '10s';

ALTER TABLE giudizi_revisione
  ADD COLUMN hash_nota text CONSTRAINT giudizi_hash_nota_formato CHECK (hash_nota ~ '^[0-9a-f]{64}$');
ALTER TABLE giudizi_revisione
  ADD CONSTRAINT giudizi_nota_nello_spazio CHECK (nota IS NULL) NOT VALID;

-- Alla fine della transazione un giudizio con impronta ha la sua nota nello spazio.
CREATE FUNCTION giudizio_nota_presente() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  codice_org text;
  presente boolean;
BEGIN
  SELECT o.codice INTO codice_org
  FROM campioni_revisione c JOIN organizations o USING (org_id) WHERE c.campione_id = NEW.campione_id;
  IF codice_org IS NULL OR to_regclass(format('%I.note_giudizi', 'org_' || codice_org)) IS NULL THEN
    RAISE EXCEPTION 'l''organizzazione del giudizio % non ha uno spazio per le note', NEW.giudizio_id;
  END IF;
  EXECUTE format('SELECT EXISTS (SELECT 1 FROM %I.note_giudizi WHERE giudizio_id = $1)', 'org_' || codice_org)
    INTO presente USING NEW.giudizio_id;
  IF NOT presente THEN
    RAISE EXCEPTION 'giudizio % con impronta ma senza nota nello spazio dell''organizzazione', NEW.giudizio_id;
  END IF;
  RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER giudizi_nota_presente
  AFTER INSERT ON giudizi_revisione DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW WHEN (NEW.hash_nota IS NOT NULL)
  EXECUTE FUNCTION giudizio_nota_presente();

-- Trigger di org_<codice>.note_giudizi (migrazione 0007 degli spazi): la nota riguarda un giudizio di
-- questa organizzazione e corrisponde all'impronta registrata in public.
CREATE FUNCTION controlla_nota_giudizio() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  org_spazio uuid;
  org_giudizio uuid;
  impronta_registrata text;
  chiave bytea;
BEGIN
  SELECT org_id INTO org_spazio FROM organizations WHERE 'org_' || codice = TG_TABLE_SCHEMA;
  SELECT c.org_id, g.hash_nota INTO org_giudizio, impronta_registrata
  FROM giudizi_revisione g JOIN campioni_revisione c USING (campione_id)
  WHERE g.giudizio_id = NEW.giudizio_id;
  IF org_spazio IS NULL OR org_giudizio IS DISTINCT FROM org_spazio THEN
    RAISE EXCEPTION 'nota di un giudizio di un''altra organizzazione nello spazio %', TG_TABLE_SCHEMA;
  END IF;
  EXECUTE format('SELECT chiave FROM %I.chiave_impronte', TG_TABLE_SCHEMA) INTO chiave;
  IF impronta_registrata IS DISTINCT FROM encode(sha256(chiave || convert_to(NEW.nota, 'UTF8')), 'hex') THEN
    RAISE EXCEPTION 'la nota del giudizio % non corrisponde alla sua impronta in public', NEW.giudizio_id;
  END IF;
  RETURN NEW;
END;
$$;

-- Spostamento delle note già scritte in public, chiamato dalla migrazione 0007 di ogni spazio.
-- Solo il proprietario: disattiva per un istante il trigger append-only per togliere il testo e
-- scrivere l'impronta; esito, revisore e versione della rubrica non cambiano. Le note vuote si tolgono
-- senza impronta. Restituisce il numero di note spostate.
CREATE FUNCTION sposta_note_giudizi(spazio text) RETURNS integer
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  org uuid;
  chiave bytea;
  spostate integer;
BEGIN
  SELECT org_id INTO org FROM organizations WHERE 'org_' || codice = spazio;
  IF org IS NULL THEN
    RAISE EXCEPTION 'lo spazio % non appartiene a un''organizzazione', spazio;
  END IF;
  EXECUTE format('SELECT chiave FROM %I.chiave_impronte', spazio) INTO chiave;
  CREATE TEMP TABLE note_da_spostare ON COMMIT DROP AS
    SELECT g.giudizio_id, g.nota FROM giudizi_revisione g JOIN campioni_revisione c USING (campione_id)
    WHERE c.org_id = org AND g.nota IS NOT NULL;
  -- Spazio nuovo o già pulito: nessun lock sulla tabella dei giudizi.
  IF NOT EXISTS (SELECT 1 FROM note_da_spostare) THEN
    DROP TABLE note_da_spostare;
    RETURN 0;
  END IF;
  ALTER TABLE giudizi_revisione DISABLE TRIGGER giudizi_append_only;
  UPDATE giudizi_revisione g
     SET nota = NULL,
         hash_nota = CASE WHEN btrim(s.nota) <> ''
                          THEN encode(sha256(chiave || convert_to(s.nota, 'UTF8')), 'hex') END
    FROM note_da_spostare s WHERE g.giudizio_id = s.giudizio_id;
  ALTER TABLE giudizi_revisione ENABLE TRIGGER giudizi_append_only;
  EXECUTE format('INSERT INTO %I.note_giudizi (giudizio_id, nota)
                  SELECT giudizio_id, nota FROM note_da_spostare WHERE btrim(nota) <> %L', spazio, '');
  GET DIAGNOSTICS spostate = ROW_COUNT;
  DROP TABLE note_da_spostare;
  RETURN spostate;
END;
$$;
REVOKE EXECUTE ON FUNCTION sposta_note_giudizi(text) FROM PUBLIC;
