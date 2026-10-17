-- Migrazione 0033: i risultati di N e D portano tutte le loro chiavi (fase 4; registro di metodo, sezione 17).
-- Si applica dopo la 0032. In produzione capability_snapshots e policy_estimates sono vuote (2026-10-17).
-- Ogni riga di policy_estimates è il risultato di un calcolo deterministico: stessi giudizi (impronta),
-- stesso profilo, snapshot, rubrica, versione del calcolo, seme ed estrazioni danno la stessa riga.
-- Un input nuovo è una riga nuova: i risultati non si modificano (append-only) e la vista legge l'ultimo.

SET LOCAL lock_timeout = '10s';

-- Capacità di test (misurata in condizioni controllate) o di riserva (scala di riserva della rubrica).
ALTER TABLE capability_snapshots
  ADD COLUMN tipo_capacita text NOT NULL CHECK (tipo_capacita IN ('test', 'riserva'));

ALTER TABLE policy_estimates
  ADD COLUMN versione_calcolo text NOT NULL,
  ADD COLUMN seme bigint NOT NULL,
  ADD COLUMN estrazioni int NOT NULL CHECK (estrazioni > 0),
  ADD COLUMN tipo_capacita text CHECK (tipo_capacita IN ('test', 'riserva')),  -- vuoto se N non è calcolato
  ADD COLUMN componenti_d text[] NOT NULL,
  ADD COLUMN d_provvisorio boolean NOT NULL,
  ADD COLUMN impronta_input text NOT NULL CHECK (impronta_input ~ '^[0-9a-f]{64}$'),
  ADD COLUMN calcolata_da uuid REFERENCES utenti,
  ADD CONSTRAINT stime_n_completa CHECK ((n_mean IS NULL) = (tipo_capacita IS NULL)),
  ADD CONSTRAINT stime_quadranti_con_n_e_d CHECK (
    (p_q1 IS NULL) = (n_mean IS NULL OR d_mean IS NULL)
    AND (p_q1 IS NULL) = (p_q2 IS NULL) AND (p_q2 IS NULL) = (p_q3 IS NULL) AND (p_q3 IS NULL) = (p_q4 IS NULL));

ALTER TABLE policy_estimates DROP CONSTRAINT policy_estimates_pkey;
ALTER TABLE policy_estimates ADD PRIMARY KEY
  (occurrence_id, profile_id, snapshot_id, rubric_version, impronta_input, versione_calcolo, seme, estrazioni);

CREATE TRIGGER stime_append_only BEFORE UPDATE OR DELETE ON policy_estimates
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER stime_no_truncate BEFORE TRUNCATE ON policy_estimates
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();

-- La vista dei ruoli legge, per ogni occorrenza e configurazione, il calcolo più recente con N e D.
CREATE OR REPLACE VIEW v_role_metrics AS
WITH ultime AS (
  SELECT DISTINCT ON (pe.occurrence_id, pe.profile_id, pe.snapshot_id, pe.rubric_version) pe.*
  FROM policy_estimates pe
  WHERE pe.n_mean IS NOT NULL AND pe.d_mean IS NOT NULL
  ORDER BY pe.occurrence_id, pe.profile_id, pe.snapshot_id, pe.rubric_version, pe.computed_at DESC,
           pe.impronta_input  -- a parità di istante, scelta deterministica
),
cur AS (
  SELECT u.*, o.role_id, o.time_share AS p
  FROM ultime u
  JOIN task_occurrences o USING (occurrence_id)
  JOIN roles r ON r.role_id = o.role_id
  JOIN weight_profiles w ON w.profile_id = u.profile_id AND w.is_active
    AND (w.org_id = r.org_id OR (w.org_id IS NULL AND NOT EXISTS (
      SELECT 1 FROM weight_profiles w2 WHERE w2.org_id = r.org_id AND w2.is_active)))
  JOIN capability_snapshots s ON s.snapshot_id = u.snapshot_id AND s.status = 'published'
  JOIN rubric_versions rv ON rv.version = u.rubric_version AND rv.is_current
),
bary AS (
  SELECT role_id, SUM(p * n_mean) / SUM(p) AS bn, SUM(p * d_mean) / SUM(p) AS bd, SUM(p) AS tw
  FROM cur GROUP BY role_id
)
SELECT b.role_id,
       round(b.bn, 3) AS barycenter_n,
       round(b.bd, 3) AS barycenter_d,
       round(sqrt(SUM(c.p * ((c.n_mean - b.bn)^2 + (c.d_mean - b.bd)^2)) / b.tw), 3) AS dispersion,
       round(SUM(c.p * GREATEST(c.p_q1, c.p_q2, c.p_q3, c.p_q4)) / b.tw, 3) AS stability,
       count(*) AS n_tasks
FROM bary b JOIN cur c USING (role_id)
GROUP BY b.role_id, b.bn, b.bd, b.tw;

-- La pubblicazione di uno snapshot (neartech.capacita.pubblica_snapshot) aggiorna stato e approvazione.
GRANT UPDATE (status, approved_by, approved_at) ON capability_snapshots TO neartech_app;
