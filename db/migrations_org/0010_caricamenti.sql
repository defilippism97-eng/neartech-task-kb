-- Migrazione 0010 dello spazio organizzazione: documenti caricati dalla piattaforma (fase 6, fetta 5).
-- L'amministratore carica i mansionari; il testo resta qui, nello spazio, finché il lavoratore della coda lo
-- scompone. Nel job in public va solo l'identificativo del caricamento (ADR 0001, neartech.coda).
-- L'avvio della scomposizione è un atto con la stima dei costi: una riga per caricamento, append-only.

SET LOCAL lock_timeout = '10s';

DO $$
BEGIN
  IF current_schema() = 'public' THEN
    RAISE EXCEPTION 'migrazione dello spazio organizzazione eseguita su public';
  END IF;
END;
$$;

-- Il documento è il suo contenuto: lo stesso file caricato due volte è lo stesso caricamento.
CREATE TABLE caricamenti (
  caricamento_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nome_file text NOT NULL CHECK (length(btrim(nome_file)) > 0),
  sha256 text NOT NULL UNIQUE CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  ruolo text NOT NULL CHECK (length(btrim(ruolo)) > 0),
  testo text NOT NULL CHECK (length(btrim(testo)) > 0),
  caricato_da uuid NOT NULL REFERENCES public.utenti,
  decisione_id bigint NOT NULL REFERENCES public.registro_decisioni,
  caricato_il timestamptz NOT NULL DEFAULT now()
);

-- Avvio della scomposizione: l'atto che ha confermato la stima e il job accodato. Un documento il cui job è
-- fallito si può riavviare con un atto nuovo: un avvio per job.
CREATE TABLE avvii_scomposizione (
  job_id uuid PRIMARY KEY REFERENCES public.jobs,
  caricamento_id uuid NOT NULL REFERENCES caricamenti,
  decisione_id bigint NOT NULL REFERENCES public.registro_decisioni,
  avviato_il timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX avvii_per_caricamento ON avvii_scomposizione (caricamento_id, avviato_il);

CREATE TRIGGER caricamenti_append_only BEFORE UPDATE OR DELETE ON caricamenti
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER caricamenti_no_truncate BEFORE TRUNCATE ON caricamenti
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER avvii_append_only BEFORE UPDATE OR DELETE ON avvii_scomposizione
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER avvii_no_truncate BEFORE TRUNCATE ON avvii_scomposizione
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();

DO $$
BEGIN
  EXECUTE format('GRANT SELECT ON %1$I.caricamenti, %1$I.avvii_scomposizione TO neartech_app, neartech_lettura',
                 current_schema());
  EXECUTE format('GRANT INSERT ON %1$I.caricamenti, %1$I.avvii_scomposizione TO neartech_app', current_schema());
END;
$$;
