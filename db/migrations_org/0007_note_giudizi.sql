-- Migrazione 0007 dello spazio organizzazione: note dei revisori sui giudizi (ADR 0004).
-- Il testo libero del revisore sta qui; in public.giudizi_revisione resta l'impronta (hash_nota),
-- calcolata con la chiave di questo spazio. Tabella append-only, come il giudizio.
-- Si applica dopo la 0028 di public (funzioni controlla_nota_giudizio e sposta_note_giudizi).

DO $$
BEGIN
  IF current_schema() = 'public' THEN
    RAISE EXCEPTION 'migrazione dello spazio organizzazione eseguita su public';
  END IF;
END;
$$;

CREATE TABLE note_giudizi (
  giudizio_id bigint PRIMARY KEY REFERENCES public.giudizi_revisione,
  nota text NOT NULL CHECK (length(btrim(nota)) > 0),
  registrata_il timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER note_giudizi_append_only BEFORE UPDATE OR DELETE ON note_giudizi
  FOR EACH ROW EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER note_giudizi_no_truncate BEFORE TRUNCATE ON note_giudizi
  FOR EACH STATEMENT EXECUTE FUNCTION public.vieta_modifiche();
CREATE TRIGGER note_giudizi_controllo BEFORE INSERT ON note_giudizi
  FOR EACH ROW EXECUTE FUNCTION public.controlla_nota_giudizio();

-- Le note che i revisori di questa organizzazione hanno già scritto in public vengono qui.
SELECT public.sposta_note_giudizi(current_schema());

DO $$
BEGIN
  EXECUTE format('GRANT SELECT ON %1$I.note_giudizi TO neartech_app, neartech_lettura', current_schema());
  EXECUTE format('GRANT INSERT ON %1$I.note_giudizi TO neartech_app', current_schema());
END;
$$;
