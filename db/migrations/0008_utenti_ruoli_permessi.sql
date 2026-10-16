-- Migrazione 0008: utenti del sistema, ruoli, permessi e log di accesso.
-- Si applica dopo la 0007. Ruoli decisi dal responsabile il 2026-10-16
-- (docs/metodologia-estensioni.md, sezioni 7 e 8; ADR 0002).
-- Gli utenti sono identificati solo dall'identificativo opaco dell'SSO: nomi ed email
-- restano nel fornitore di identità. Nessun dato sui lavoratori valutati.

-- Funzione comune alle tabelle append-only: rifiuta modifiche e cancellazioni.
CREATE FUNCTION vieta_modifiche() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'la tabella % è append-only: % non ammesso', TG_TABLE_NAME, TG_OP;
END;
$$;

-- Codice breve dell'organizzazione, usato anche per il nome dello schema del suo spazio.
ALTER TABLE organizations
  ADD COLUMN codice text UNIQUE CHECK (codice ~ '^[a-z][a-z0-9_]{1,40}$'),
  ADD COLUMN creata_il timestamptz NOT NULL DEFAULT now();

CREATE TABLE utenti (
  utente_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  soggetto_sso text NOT NULL UNIQUE,
  creato_il timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ruoli (
  codice text PRIMARY KEY,
  ambito text NOT NULL CHECK (ambito IN ('globale', 'organizzazione')),
  descrizione text NOT NULL
);

INSERT INTO ruoli (codice, ambito, descrizione) VALUES
  ('amministratore_tecnico', 'globale', 'Super user e fornitore del servizio: utenti, parametri tecnici, budget AI, fonti e snapshot'),
  ('auditor', 'globale', 'Vede tutto, solo in lettura'),
  ('comitato_guida', 'organizzazione', 'Indirizzi di alto livello, parametri di governance, restituzioni finali'),
  ('revisore', 'organizzazione', 'Giudica la classificazione dei singoli task, abbinamenti e fusioni; segnala le ricadute anomale degli indirizzi'),
  ('rappresentante_lavoratori', 'organizzazione', 'Può bloccare un ribasso di D; il ruolo può restare vuoto');

CREATE TABLE assegnazioni_ruolo (
  assegnazione_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  utente_id uuid NOT NULL REFERENCES utenti,
  ruolo text NOT NULL REFERENCES ruoli,
  org_id uuid REFERENCES organizations,
  valida_dal timestamptz NOT NULL DEFAULT now(),
  valida_al timestamptz,
  assegnata_da uuid REFERENCES utenti,
  creata_il timestamptz NOT NULL DEFAULT now(),
  CHECK (valida_al IS NULL OR valida_al >= valida_dal)
);
CREATE INDEX assegnazioni_utente ON assegnazioni_ruolo (utente_id, ruolo);

-- Un ruolo di organizzazione richiede l'organizzazione; un ruolo globale non la ammette.
-- Un'assegnazione si può solo chiudere (valida_al da vuoto a valorizzato), mai riscrivere.
CREATE FUNCTION controlla_assegnazione() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE TRIGGER assegnazioni_controllo
  BEFORE INSERT OR UPDATE OR DELETE ON assegnazioni_ruolo
  FOR EACH ROW EXECUTE FUNCTION controlla_assegnazione();

-- Matrice ruolo-azione. Si modifica con una migrazione nuova, mai nel codice.
CREATE TABLE permessi_ruolo (
  ruolo text NOT NULL REFERENCES ruoli,
  azione text NOT NULL,
  PRIMARY KEY (ruolo, azione)
);

INSERT INTO permessi_ruolo (ruolo, azione) VALUES
  ('amministratore_tecnico', 'leggere'),
  ('amministratore_tecnico', 'gestire_utenti'),
  ('amministratore_tecnico', 'gestire_organizzazioni'),
  ('amministratore_tecnico', 'gestire_parametri_tecnici'),
  ('amministratore_tecnico', 'gestire_budget_ai'),
  ('amministratore_tecnico', 'approvare_fonti'),
  ('amministratore_tecnico', 'approvare_snapshot'),
  ('auditor', 'leggere'),
  ('auditor', 'leggere_audit'),
  ('comitato_guida', 'leggere'),
  ('comitato_guida', 'proporre_indirizzo'),
  ('comitato_guida', 'approvare_indirizzo'),
  ('comitato_guida', 'proporre_parametro'),
  ('comitato_guida', 'approvare_parametro'),
  ('comitato_guida', 'approvare_restituzione'),
  ('revisore', 'leggere'),
  ('revisore', 'giudicare_task'),
  ('revisore', 'approvare_abbinamenti'),
  ('revisore', 'approvare_fusioni'),
  ('revisore', 'segnalare'),
  ('rappresentante_lavoratori', 'leggere'),
  ('rappresentante_lavoratori', 'bloccare_ribasso');

CREATE TABLE log_accessi (
  accesso_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  utente_id uuid REFERENCES utenti,
  org_id uuid REFERENCES organizations,
  azione text NOT NULL,
  risorsa text,
  esito text NOT NULL CHECK (esito IN ('consentito', 'negato')),
  avvenuto_il timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX log_accessi_utente ON log_accessi (utente_id, avvenuto_il);
CREATE TRIGGER log_accessi_append_only
  BEFORE UPDATE OR DELETE ON log_accessi
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER log_accessi_no_truncate
  BEFORE TRUNCATE ON log_accessi
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
