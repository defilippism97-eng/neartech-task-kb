-- Migrazione 0009 dello spazio organizzazione: il livello di revisione di un lotto lo sceglie il revisore
-- (registro di metodo, sezione 17). Si applica dopo la 0032 di public.
-- La riga del lotto non porta più livello e quota: stanno in livelli_lotto, con l'atto del revisore.
-- In produzione non esistono ancora lotti: il vincolo nuovo vale subito.

SET LOCAL lock_timeout = '10s';

DO $$
BEGIN
  IF current_schema() = 'public' THEN
    RAISE EXCEPTION 'migrazione dello spazio organizzazione eseguita su public';
  END IF;
END;
$$;

ALTER TABLE lotti_abbinamento ALTER COLUMN livello_revisione DROP NOT NULL;
ALTER TABLE lotti_abbinamento ADD CONSTRAINT lotti_senza_livello
  CHECK (livello_revisione IS NULL AND parametro_quota_id IS NULL);

CREATE TABLE livelli_lotto (
  lotto_id uuid PRIMARY KEY REFERENCES lotti_abbinamento,
  livello_revisione text NOT NULL CHECK (livello_revisione IN ('campione', 'completa', 'nulla')),
  parametro_quota_id uuid REFERENCES public.parametri_governance,
  decisione_id bigint NOT NULL REFERENCES public.registro_decisioni,
  registrato_il timestamptz NOT NULL DEFAULT now(),
  CHECK ((livello_revisione = 'campione') = (parametro_quota_id IS NOT NULL))
);

CREATE TRIGGER livelli_lotto_append_only BEFORE UPDATE OR DELETE ON livelli_lotto
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER livelli_lotto_no_truncate BEFORE TRUNCATE ON livelli_lotto
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER livelli_lotto_controllo BEFORE INSERT ON livelli_lotto
  FOR EACH ROW EXECUTE FUNCTION public.abbinamento_controlla_livello();

CREATE OR REPLACE VIEW v_abbinamenti AS
SELECT c.candidato_id, c.titolo, c.granularita, c.ruolo_id, c.documento_id,
       p.proposta_id, p.lotto_id, p.task_id AS task_proposto, p.distanza, p.margine,
       l.modello_embedding, l.vicini AS n_vicini, v.livello_revisione, v.parametro_quota_id,
       d.esito, d.decisione_id AS atto_decisione,
       a.task_id AS task_applicato, a.task_nuovo, a.decisione_id AS atto_applicazione
FROM candidati c
LEFT JOIN proposte_abbinamento p USING (candidato_id)
LEFT JOIN lotti_abbinamento l USING (lotto_id)
LEFT JOIN livelli_lotto v USING (lotto_id)
LEFT JOIN decisioni_abbinamento d USING (proposta_id)
LEFT JOIN applicazioni_abbinamento a USING (proposta_id);

DO $$
BEGIN
  EXECUTE format('GRANT SELECT ON %1$I.livelli_lotto TO neartech_app, neartech_lettura', current_schema());
  EXECUTE format('GRANT INSERT ON %1$I.livelli_lotto TO neartech_app', current_schema());
END;
$$;
