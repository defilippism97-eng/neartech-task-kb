-- Migrazione 0004 dello spazio organizzazione: privilegi dei ruoli di database (migrazione 0022).
-- Si applica a ogni schema org_<codice>; current_schema() è lo schema dell'organizzazione.
-- L'applicazione legge, inserisce e aggiorna (separazioni delle fusioni); non cancella né cambia lo schema.

DO $$
BEGIN
  EXECUTE format('GRANT USAGE ON SCHEMA %I TO neartech_app, neartech_lettura', current_schema());
  EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO neartech_app, neartech_lettura', current_schema());
  EXECUTE format('GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA %I TO neartech_app', current_schema());
END;
$$;
