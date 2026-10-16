-- Migrazione 0022: ruoli di database separati (ADR 0003; decisione del 2026-10-16).
-- Si applica dopo la 0021, con il ruolo proprietario.
-- Il proprietario esegue migrazioni e manutenzione (anche la creazione degli spazi delle organizzazioni).
-- neartech_app: l'applicazione. Non è proprietaria delle tabelle, quindi non può disattivare i trigger
--   append-only, svuotare tabelle o cambiare lo schema. Legge e inserisce; aggiorna e cancella solo dove
--   il codice lo richiede. Non tocca registro delle migrazioni, ruoli e matrice dei permessi.
-- neartech_lettura: sola lettura (auditor, controlli).
-- I due ruoli non hanno login: i login con password si creano fuori dal repo e ricevono il ruolo
-- (GRANT neartech_app TO <login>). Una migrazione futura che crea tabelle deve concedere i privilegi.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'neartech_app') THEN
    CREATE ROLE neartech_app NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'neartech_lettura') THEN
    CREATE ROLE neartech_lettura NOLOGIN;
  END IF;
END;
$$;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO neartech_app, neartech_lettura;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO neartech_app, neartech_lettura;
GRANT INSERT ON ALL TABLES IN SCHEMA public TO neartech_app;
REVOKE INSERT ON migrazioni_applicate, ruoli, permessi_ruolo FROM neartech_app;
GRANT UPDATE ON canonical_tasks, organizations, assegnazioni_ruolo, jobs, task_occurrences TO neartech_app;
-- Il Canonicalizer, alla fusione, sposta occorrenze e collegamenti del task fuso.
GRANT DELETE ON task_occurrences, task_mappings, crosswalk_giudizi TO neartech_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO neartech_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO neartech_app, neartech_lettura;
