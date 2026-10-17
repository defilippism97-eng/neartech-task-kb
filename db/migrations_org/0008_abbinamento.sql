-- Migrazione 0008 dello spazio organizzazione: abbinamento al dataset consolidato (fase 3, ADR 0006).
-- Candidati estratti dai documenti, lotti di proposte, proposte, decisioni del revisore e applicazioni.
-- Titoli, estratti e note dei candidati sono dati dell'organizzazione: nel dataset entra solo il titolo
-- rielaborato di un candidato che diventa task nuovo. Tutte le tabelle sono append-only.
-- Si applica dopo la 0031 di public.

DO $$
BEGIN
  IF current_schema() = 'public' THEN
    RAISE EXCEPTION 'migrazione dello spazio organizzazione eseguita su public';
  END IF;
END;
$$;

-- Attività estratte da un documento, non ancora nel dataset. Granularità 3 (aree di responsabilità) esclusa:
-- non sono task (registro di metodo, sezione 2).
CREATE TABLE candidati (
  candidato_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  documento_id uuid NOT NULL REFERENCES documenti,
  ruolo_id uuid NOT NULL REFERENCES ruoli_organizzativi,
  titolo text NOT NULL CHECK (length(btrim(titolo)) > 0 AND titolo !~ '[\r\n\t]'),
  granularita smallint NOT NULL CHECK (granularita IN (1, 2)),
  estratto text NOT NULL CHECK (length(btrim(estratto)) > 0),
  nota_contesto text,
  model_name text NOT NULL,
  prompt_hash text NOT NULL,
  creato_il timestamptz NOT NULL DEFAULT now(),
  UNIQUE (documento_id, ruolo_id, titolo)
);

-- Un lotto per esecuzione delle proposte, con le sue chiavi: modello di embedding, vicini, livello di
-- revisione dichiarato e, se a campione, il parametro della quota vigente.
CREATE TABLE lotti_abbinamento (
  lotto_id uuid PRIMARY KEY,
  decisione_id bigint NOT NULL REFERENCES public.registro_decisioni,
  modello_embedding text NOT NULL,
  vicini int NOT NULL CHECK (vicini > 0),
  livello_revisione text NOT NULL CHECK (livello_revisione IN ('campione', 'completa', 'nulla')),
  parametro_quota_id uuid REFERENCES public.parametri_governance,
  creato_il timestamptz NOT NULL DEFAULT now(),
  CHECK ((livello_revisione = 'campione') = (parametro_quota_id IS NOT NULL))
);

-- La proposta è il task attivo più vicino; senza task nel dataset resta vuota (il candidato sarà un task nuovo).
CREATE TABLE proposte_abbinamento (
  proposta_id uuid PRIMARY KEY,
  lotto_id uuid NOT NULL REFERENCES lotti_abbinamento,
  candidato_id uuid NOT NULL UNIQUE REFERENCES candidati,
  task_id uuid REFERENCES public.canonical_tasks,
  distanza double precision CHECK (distanza >= 0),
  margine double precision CHECK (margine >= 0),
  vicini jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(vicini) = 'array'),
  CHECK ((task_id IS NULL) = (distanza IS NULL))
);
CREATE INDEX proposte_per_lotto ON proposte_abbinamento (lotto_id);

-- Una decisione per proposta, legata all'atto del registro che decide il lotto.
CREATE TABLE decisioni_abbinamento (
  proposta_id uuid PRIMARY KEY REFERENCES proposte_abbinamento,
  esito text NOT NULL CHECK (esito IN ('approvata', 'rifiutata')),
  decisione_id bigint NOT NULL REFERENCES public.registro_decisioni,
  registrata_il timestamptz NOT NULL DEFAULT now()
);

-- Esito dell'applicazione: il task del dataset a cui il candidato è ora collegato.
CREATE TABLE applicazioni_abbinamento (
  proposta_id uuid PRIMARY KEY REFERENCES decisioni_abbinamento,
  task_id uuid NOT NULL REFERENCES public.canonical_tasks,
  task_nuovo boolean NOT NULL,
  occorrenza_id uuid,  -- vuota se il ruolo aveva già il task
  decisione_id bigint NOT NULL REFERENCES public.registro_decisioni,
  applicata_il timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER candidati_append_only BEFORE UPDATE OR DELETE ON candidati
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER candidati_no_truncate BEFORE TRUNCATE ON candidati
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER lotti_abbinamento_append_only BEFORE UPDATE OR DELETE ON lotti_abbinamento
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER lotti_abbinamento_no_truncate BEFORE TRUNCATE ON lotti_abbinamento
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER proposte_abbinamento_append_only BEFORE UPDATE OR DELETE ON proposte_abbinamento
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER proposte_abbinamento_no_truncate BEFORE TRUNCATE ON proposte_abbinamento
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER decisioni_abbinamento_append_only BEFORE UPDATE OR DELETE ON decisioni_abbinamento
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER decisioni_abbinamento_no_truncate BEFORE TRUNCATE ON decisioni_abbinamento
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER applicazioni_abbinamento_append_only BEFORE UPDATE OR DELETE ON applicazioni_abbinamento
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER applicazioni_abbinamento_no_truncate BEFORE TRUNCATE ON applicazioni_abbinamento
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();

-- Stato di ogni candidato, con le chiavi del suo lotto: per la coda, il report di audit e i risultati.
CREATE VIEW v_abbinamenti AS
SELECT c.candidato_id, c.titolo, c.granularita, c.ruolo_id, c.documento_id,
       p.proposta_id, p.lotto_id, p.task_id AS task_proposto, p.distanza, p.margine,
       l.modello_embedding, l.vicini AS n_vicini, l.livello_revisione, l.parametro_quota_id,
       d.esito, d.decisione_id AS atto_decisione,
       a.task_id AS task_applicato, a.task_nuovo, a.decisione_id AS atto_applicazione
FROM candidati c
LEFT JOIN proposte_abbinamento p USING (candidato_id)
LEFT JOIN lotti_abbinamento l USING (lotto_id)
LEFT JOIN decisioni_abbinamento d USING (proposta_id)
LEFT JOIN applicazioni_abbinamento a USING (proposta_id);

DO $$
BEGIN
  EXECUTE format('GRANT SELECT ON %1$I.candidati, %1$I.lotti_abbinamento, %1$I.proposte_abbinamento,
                  %1$I.decisioni_abbinamento, %1$I.applicazioni_abbinamento, %1$I.v_abbinamenti
                  TO neartech_app, neartech_lettura', current_schema());
  EXECUTE format('GRANT INSERT ON %1$I.candidati, %1$I.lotti_abbinamento, %1$I.proposte_abbinamento,
                  %1$I.decisioni_abbinamento, %1$I.applicazioni_abbinamento TO neartech_app', current_schema());
END;
$$;
