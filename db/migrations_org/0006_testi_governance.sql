-- Migrazione 0006 dello spazio organizzazione: testi di governance (ADR 0004).
-- Motivazioni e dettagli testuali degli atti dell'organizzazione, testo degli indirizzi del comitato,
-- descrizioni dei parametri dell'organizzazione. Nel registro condiviso resta l'hash del testo.
-- Tabelle append-only, come il registro.

CREATE TABLE testi_atti (
  decisione_id bigint PRIMARY KEY REFERENCES public.registro_decisioni,
  motivazione text NOT NULL CHECK (length(btrim(motivazione)) > 0),
  dettagli jsonb NOT NULL DEFAULT '{}'::jsonb,
  registrato_il timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE testi_indirizzi (
  indirizzo_id uuid PRIMARY KEY REFERENCES public.indirizzi_comitato,
  testo text NOT NULL,
  ambito text NOT NULL
);

CREATE TABLE testi_parametri (
  parametro_id uuid PRIMARY KEY REFERENCES public.parametri_governance,
  descrizione text NOT NULL
);

CREATE TRIGGER testi_atti_append_only BEFORE UPDATE OR DELETE ON testi_atti
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER testi_atti_no_truncate BEFORE TRUNCATE ON testi_atti
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER testi_indirizzi_append_only BEFORE UPDATE OR DELETE ON testi_indirizzi
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER testi_indirizzi_no_truncate BEFORE TRUNCATE ON testi_indirizzi
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER testi_parametri_append_only BEFORE UPDATE OR DELETE ON testi_parametri
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER testi_parametri_no_truncate BEFORE TRUNCATE ON testi_parametri
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();

DO $$
BEGIN
  EXECUTE format('GRANT SELECT ON %1$I.testi_atti, %1$I.testi_indirizzi, %1$I.testi_parametri
                  TO neartech_app, neartech_lettura', current_schema());
  EXECUTE format('GRANT INSERT ON %1$I.testi_atti, %1$I.testi_indirizzi, %1$I.testi_parametri
                  TO neartech_app', current_schema());
END;
$$;
