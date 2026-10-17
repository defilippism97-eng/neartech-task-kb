-- Migrazione 0006 dello spazio organizzazione: testi di governance (ADR 0004).
-- Motivazioni e dettagli testuali degli atti dell'organizzazione, testo degli indirizzi del comitato,
-- descrizioni dei parametri dell'organizzazione. Nel registro condiviso resta l'impronta del testo,
-- calcolata con la chiave di questo spazio: senza la chiave non si verifica un testo indovinato, e
-- all'uscita del cliente la chiave se ne va con lo spazio. Tabelle append-only, come il registro.
-- Si applica dopo la 0025 di public (funzione testo_della_propria_organizzazione).

DO $$
BEGIN
  IF current_schema() = 'public' THEN
    RAISE EXCEPTION 'migrazione dello spazio organizzazione eseguita su public';
  END IF;
END;
$$;

CREATE TABLE chiave_impronte (
  unica boolean PRIMARY KEY DEFAULT true CHECK (unica),
  chiave bytea NOT NULL CHECK (length(chiave) = 32)
);
-- 32 byte da due UUID casuali (gen_random_uuid usa il generatore crittografico di PostgreSQL).
INSERT INTO chiave_impronte (chiave) VALUES (uuid_send(gen_random_uuid()) || uuid_send(gen_random_uuid()));

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

CREATE TRIGGER chiave_impronte_append_only BEFORE UPDATE OR DELETE ON chiave_impronte
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER chiave_impronte_no_truncate BEFORE TRUNCATE ON chiave_impronte
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();
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

-- Ogni testo appartiene a un oggetto di questa organizzazione.
CREATE TRIGGER testi_atti_propria_organizzazione BEFORE INSERT ON testi_atti
  FOR EACH ROW EXECUTE FUNCTION public.testo_della_propria_organizzazione('atto');
CREATE TRIGGER testi_indirizzi_propria_organizzazione BEFORE INSERT ON testi_indirizzi
  FOR EACH ROW EXECUTE FUNCTION public.testo_della_propria_organizzazione('indirizzo');
CREATE TRIGGER testi_parametri_propria_organizzazione BEFORE INSERT ON testi_parametri
  FOR EACH ROW EXECUTE FUNCTION public.testo_della_propria_organizzazione('parametro');

DO $$
BEGIN
  EXECUTE format('GRANT SELECT ON %1$I.chiave_impronte, %1$I.testi_atti, %1$I.testi_indirizzi,
                  %1$I.testi_parametri TO neartech_app, neartech_lettura', current_schema());
  EXECUTE format('GRANT INSERT ON %1$I.testi_atti, %1$I.testi_indirizzi, %1$I.testi_parametri
                  TO neartech_app', current_schema());
END;
$$;
