-- Migrazione 0005 dello spazio organizzazione: l'applicazione può cancellare un'occorrenza doppia
-- quando il Canonicalizer fonde due task presenti nello stesso ruolo (neartech.occorrenze.sposta_occorrenze).

DO $$
BEGIN
  EXECUTE format('GRANT DELETE ON %I.occorrenze TO neartech_app', current_schema());
END;
$$;
