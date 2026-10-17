-- Migrazione 0036: risultati vigenti per occorrenza e approvazione della restituzione (fase 5; registro di
-- metodo, sezione 24). Si applica dopo la 0035.
-- 1. Ogni risultato nuovo registra i giudizi che ha usato: la restituzione ne ricava i modelli esatti.
-- 2. La scelta del risultato che vale per un'occorrenza stava dentro v_role_metrics; ora sta in una vista sua,
--    letta sia dalla lettura per ruolo sia dalla restituzione (neartech.restituzione), così le due letture non
--    possono divergere. v_role_metrics resta uguale: stesse colonne, stesso calcolo. Da qui v_role_metrics
--    dipende da v_risultati_vigenti: una migrazione futura che cambia le colonne della vista nuova (oltre ad
--    aggiungerne in fondo) deve ricreare entrambe.
-- 3. Una restituzione si approva una volta e riguarda sempre un'organizzazione.

SET LOCAL lock_timeout = '10s';

-- 1. Giudizi usati (identificativi di assessment_runs). Vuoto per i risultati calcolati prima di questa
--    migrazione: per quelli la restituzione deduce i modelli dai giudizi registrati prima del calcolo.
ALTER TABLE policy_estimates ADD COLUMN giudizi_usati uuid[];

-- La ricorsione sui task fusi (calcolo e restituzione) parte dal superstite.
CREATE INDEX canonical_tasks_fusi_in ON canonical_tasks (merged_into) WHERE merged_into IS NOT NULL;

-- 2. Per ogni occorrenza l'ultimo risultato con N e D, calcolato con la configurazione vigente (profilo attivo
--    dell'organizzazione o, se non ne ha, quello comune; snapshot pubblicato; rubrica corrente), se
--    l'occorrenza ha ancora lo stesso task e lo stesso ruolo.
CREATE VIEW v_risultati_vigenti AS
WITH ultime AS (
  SELECT DISTINCT ON (pe.occurrence_id, pe.profile_id, pe.snapshot_id, pe.rubric_version) pe.*
  FROM policy_estimates pe
  ORDER BY pe.occurrence_id, pe.profile_id, pe.snapshot_id, pe.rubric_version, pe.computed_at DESC,
           pe.versione_calcolo DESC, pe.seme, pe.estrazioni, pe.impronta_input  -- scelta deterministica
)
SELECT u.occurrence_id, u.task_id, o.role_id, r.org_id, u.profile_id, u.snapshot_id, u.rubric_version,
       u.versione_calcolo, u.seme, u.estrazioni, u.n_mean, u.n_sd, u.d_mean, u.d_sd,
       u.p_q1, u.p_q2, u.p_q3, u.p_q4, u.d_provvisorio, u.tipo_capacita, u.componenti_d, o.time_share,
       u.impronta_input, u.giudizi_usati, u.computed_at
FROM ultime u
JOIN task_occurrences o ON o.occurrence_id = u.occurrence_id AND o.task_id = u.task_id AND o.role_id = u.role_id
JOIN roles r ON r.role_id = o.role_id
JOIN weight_profiles w ON w.profile_id = u.profile_id AND w.is_active
  AND (w.org_id = r.org_id OR (w.org_id IS NULL AND NOT EXISTS (
    SELECT 1 FROM weight_profiles w2 WHERE w2.org_id = r.org_id AND w2.is_active)))
JOIN capability_snapshots s ON s.snapshot_id = u.snapshot_id AND s.status = 'published'
JOIN rubric_versions rv ON rv.version = u.rubric_version AND rv.is_current
WHERE u.n_mean IS NOT NULL AND u.d_mean IS NOT NULL;

CREATE OR REPLACE VIEW v_role_metrics AS
WITH cur AS (
  SELECT v.*,
         bool_and(v.time_share IS NOT NULL) OVER (PARTITION BY v.role_id) AS con_quote,
         CASE WHEN bool_and(v.time_share IS NOT NULL) OVER (PARTITION BY v.role_id) THEN v.time_share ELSE 1 END AS p
  FROM v_risultati_vigenti v
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

-- I privilegi predefiniti della 0022 valgono solo per gli oggetti creati dallo stesso ruolo: si concedono qui.
GRANT SELECT ON v_risultati_vigenti TO neartech_app, neartech_lettura;

-- 3. Approvazione della restituzione: l'oggetto dell'atto è l'impronta della restituzione.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM registro_decisioni WHERE tipo_oggetto = 'restituzione') THEN
    RAISE EXCEPTION 'esistono già atti sulle restituzioni: verificarli prima di applicare la 0036';
  END IF;
END;
$$;
ALTER TABLE registro_decisioni ADD CONSTRAINT restituzione_di_un_organizzazione
  CHECK (tipo_oggetto <> 'restituzione' OR org_id IS NOT NULL);
CREATE UNIQUE INDEX registro_una_approvazione_restituzione ON registro_decisioni (org_id, oggetto_id)
  WHERE tipo_oggetto = 'restituzione' AND atto = 'approvazione';
