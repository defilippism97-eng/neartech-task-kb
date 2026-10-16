-- Migrazione 0012: coda dei job con presa in carico esclusiva.
-- Si applica dopo la 0011. Estende la tabella jobs di schema.sql. Un lavoratore prende
-- un job con FOR UPDATE SKIP LOCKED (neartech.coda.prendi); un job fallito torna in coda
-- finché restano tentativi. preso_il permette di recuperare i job di un lavoratore caduto.

ALTER TABLE jobs
  ADD COLUMN org_id uuid REFERENCES organizations,
  ADD COLUMN tentativi_massimi int NOT NULL DEFAULT 1 CHECK (tentativi_massimi > 0),
  ADD COLUMN preso_da text,
  ADD COLUMN preso_il timestamptz,
  ADD COLUMN completato_il timestamptz,
  ADD COLUMN ultimo_errore text;

CREATE INDEX jobs_in_coda ON jobs (kind, run_after) WHERE status = 'queued';
CREATE INDEX jobs_in_corso ON jobs (preso_il) WHERE status = 'running';
