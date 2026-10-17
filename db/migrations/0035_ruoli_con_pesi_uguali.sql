-- Migrazione 0035: lettura per ruolo senza quote di tempo (registro di metodo, sezione 22).
-- Si applica dopo la 0034. Se tutte le occorrenze di un ruolo hanno la quota di tempo, il baricentro è pesato
-- con quelle; altrimenti ogni task del ruolo pesa uguale, e il ruolo lo dichiara (pesi_tempo = 'uguali').
-- Il ruolo è provvisorio se usa pesi uguali, capacità di riserva o un D provvisorio (senza d3 e d4).
-- Le colonne di prima restano uguali e nello stesso ordine; le nuove si aggiungono in fondo.

SET LOCAL lock_timeout = '10s';

CREATE OR REPLACE VIEW v_role_metrics AS
WITH ultime AS (
  SELECT DISTINCT ON (pe.occurrence_id, pe.profile_id, pe.snapshot_id, pe.rubric_version) pe.*
  FROM policy_estimates pe
  ORDER BY pe.occurrence_id, pe.profile_id, pe.snapshot_id, pe.rubric_version, pe.computed_at DESC,
           pe.versione_calcolo DESC, pe.seme, pe.estrazioni, pe.impronta_input  -- scelta deterministica
),
validi AS (
  -- Solo l'ultimo risultato, se ha N e D e se l'occorrenza ha ancora lo stesso task e lo stesso ruolo.
  SELECT u.occurrence_id, u.profile_id, u.snapshot_id, u.rubric_version, u.n_mean, u.d_mean,
         u.p_q1, u.p_q2, u.p_q3, u.p_q4, u.d_provvisorio, u.tipo_capacita, o.role_id, o.time_share
  FROM ultime u
  JOIN task_occurrences o ON o.occurrence_id = u.occurrence_id AND o.task_id = u.task_id AND o.role_id = u.role_id
  JOIN roles r ON r.role_id = o.role_id
  JOIN weight_profiles w ON w.profile_id = u.profile_id AND w.is_active
    AND (w.org_id = r.org_id OR (w.org_id IS NULL AND NOT EXISTS (
      SELECT 1 FROM weight_profiles w2 WHERE w2.org_id = r.org_id AND w2.is_active)))
  JOIN capability_snapshots s ON s.snapshot_id = u.snapshot_id AND s.status = 'published'
  JOIN rubric_versions rv ON rv.version = u.rubric_version AND rv.is_current
  WHERE u.n_mean IS NOT NULL AND u.d_mean IS NOT NULL
),
cur AS (
  SELECT v.*,
         bool_and(v.time_share IS NOT NULL) OVER (PARTITION BY v.role_id) AS con_quote,
         CASE WHEN bool_and(v.time_share IS NOT NULL) OVER (PARTITION BY v.role_id) THEN v.time_share ELSE 1 END AS p
  FROM validi v
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
       count(*) AS n_tasks,
       CASE WHEN bool_and(c.con_quote) THEN 'quote' ELSE 'uguali' END AS pesi_tempo,
       (NOT bool_and(c.con_quote) OR bool_or(c.d_provvisorio) OR bool_or(c.tipo_capacita = 'riserva')) AS provvisorio
FROM bary b JOIN cur c USING (role_id)
GROUP BY b.role_id, b.bn, b.bd, b.tw;
