-- Migrazione 0033: i risultati di N e D portano tutte le loro chiavi (fase 4; registro di metodo, sezione 17).
-- Si applica dopo la 0032. In produzione capability_snapshots e policy_estimates sono vuote (2026-10-17).
-- Ogni riga di policy_estimates è il risultato di un calcolo deterministico: stessi giudizi (impronta),
-- stesso profilo, snapshot, rubrica, versione del calcolo, seme ed estrazioni danno la stessa riga.
-- Un input nuovo è una riga nuova: i risultati non si modificano (append-only) e la vista legge l'ultimo.

SET LOCAL lock_timeout = '10s';

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM capability_snapshots) OR EXISTS (SELECT 1 FROM policy_estimates) THEN
    RAISE EXCEPTION 'la 0033 presuppone capability_snapshots e policy_estimates vuote';
  END IF;
END;
$$;

-- Capacità di test (misurata in condizioni controllate) o di riserva (scala di riserva della rubrica).
ALTER TABLE capability_snapshots
  ADD COLUMN tipo_capacita text NOT NULL CHECK (tipo_capacita IN ('test', 'riserva'));

-- Il risultato porta task e ruolo dell'occorrenza al momento del calcolo, e non dipende più dalla riga
-- dell'occorrenza: una fusione può spostarla o toglierla (neartech.occorrenze.sposta_occorrenze) senza
-- che i risultati, append-only, la blocchino. La vista mostra solo i risultati ancora coerenti.
ALTER TABLE policy_estimates DROP CONSTRAINT policy_estimates_occurrence_id_fkey;
ALTER TABLE policy_estimates ALTER COLUMN computed_at SET DEFAULT clock_timestamp();

ALTER TABLE policy_estimates
  ADD COLUMN task_id uuid NOT NULL REFERENCES canonical_tasks,
  ADD COLUMN role_id uuid NOT NULL REFERENCES roles,
  ADD COLUMN versione_calcolo text NOT NULL,
  ADD COLUMN seme bigint NOT NULL,
  ADD COLUMN estrazioni int NOT NULL CHECK (estrazioni > 0),
  ADD COLUMN tipo_capacita text CHECK (tipo_capacita IN ('test', 'riserva')),  -- vuoto se N non è calcolato
  ADD COLUMN componenti_d text[] NOT NULL,
  ADD COLUMN d_provvisorio boolean NOT NULL,
  ADD COLUMN impronta_input text NOT NULL CHECK (impronta_input ~ '^[0-9a-f]{64}$'),
  ADD COLUMN calcolata_da uuid NOT NULL REFERENCES utenti,
  ADD CONSTRAINT stime_n_completa CHECK ((n_mean IS NULL) = (tipo_capacita IS NULL) AND (n_mean IS NULL) = (n_sd IS NULL)),
  ADD CONSTRAINT stime_d_completa CHECK (
    (d_mean IS NULL) = (cardinality(componenti_d) = 0) AND (d_mean IS NULL) = (d_sd IS NULL)
    AND componenti_d <@ ARRAY['d1', 'd2', 'd3', 'd4']
    AND d_provvisorio = NOT (componenti_d @> ARRAY['d1', 'd2', 'd3', 'd4'])),
  ADD CONSTRAINT stime_intervalli CHECK (
    n_mean BETWEEN 0 AND 1 AND d_mean BETWEEN 0 AND 1 AND n_sd >= 0 AND d_sd >= 0
    AND p_q1 BETWEEN 0 AND 1 AND p_q2 BETWEEN 0 AND 1 AND p_q3 BETWEEN 0 AND 1 AND p_q4 BETWEEN 0 AND 1),
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
  ORDER BY pe.occurrence_id, pe.profile_id, pe.snapshot_id, pe.rubric_version, pe.computed_at DESC,
           pe.versione_calcolo DESC, pe.seme, pe.estrazioni, pe.impronta_input  -- scelta deterministica
),
cur AS (
  -- Solo l'ultimo risultato, se ha N e D e se l'occorrenza ha ancora lo stesso task e lo stesso ruolo.
  SELECT u.occurrence_id, u.profile_id, u.snapshot_id, u.rubric_version, u.n_mean, u.d_mean,
         u.p_q1, u.p_q2, u.p_q3, u.p_q4, o.role_id, o.time_share AS p
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

-- Approvazioni nel database, non solo nel codice (revisione del 2026-10-17).
-- 1. Snapshot: nascono proposti; si pubblicano solo con l'atto 'approvazione' nel registro; un'approvazione non
--    si cambia; un ritiro è definitivo. La copertura di uno snapshot si scrive solo mentre è proposto.
ALTER TABLE capability_snapshots ADD CONSTRAINT snapshot_approvato_se_pubblicato
  CHECK (status = 'proposed' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL));

CREATE FUNCTION snapshot_ciclo_di_vita() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.status <> 'proposed' OR NEW.approved_by IS NOT NULL OR NEW.approved_at IS NOT NULL THEN
      RAISE EXCEPTION 'uno snapshot nasce proposto e senza approvazione';
    END IF;
    RETURN NEW;
  END IF;
  IF NEW.snapshot_id <> OLD.snapshot_id OR NEW.as_of <> OLD.as_of OR NEW.method_version <> OLD.method_version
     OR NEW.half_life_days <> OLD.half_life_days OR NEW.tipo_capacita <> OLD.tipo_capacita THEN
    RAISE EXCEPTION 'uno snapshot non cambia contenuto';
  END IF;
  IF OLD.approved_by IS NOT NULL AND (NEW.approved_by IS DISTINCT FROM OLD.approved_by
                                      OR NEW.approved_at IS DISTINCT FROM OLD.approved_at) THEN
    RAISE EXCEPTION 'l''approvazione di uno snapshot non si cambia';
  END IF;
  IF NOT ((OLD.status = 'proposed' AND NEW.status IN ('published', 'retired'))
          OR (OLD.status = 'published' AND NEW.status = 'retired')
          OR OLD.status = NEW.status) THEN
    RAISE EXCEPTION 'passaggio di stato non ammesso per uno snapshot: % -> %', OLD.status, NEW.status;
  END IF;
  IF OLD.status = 'proposed' AND NEW.status = 'published' AND NOT EXISTS (
       SELECT 1 FROM registro_decisioni WHERE tipo_oggetto = 'snapshot_capacita'
         AND oggetto_id = NEW.snapshot_id::text AND atto = 'approvazione') THEN
    RAISE EXCEPTION 'lo snapshot % si pubblica solo con l''atto di approvazione nel registro', NEW.snapshot_id;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER snapshot_ciclo_di_vita BEFORE INSERT OR UPDATE ON capability_snapshots
  FOR EACH ROW EXECUTE FUNCTION snapshot_ciclo_di_vita();

CREATE FUNCTION copertura_solo_su_snapshot_proposto() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF (SELECT status FROM capability_snapshots WHERE snapshot_id = NEW.snapshot_id) IS DISTINCT FROM 'proposed' THEN
    RAISE EXCEPTION 'la copertura si scrive solo su uno snapshot proposto';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER task_capability_solo_proposto BEFORE INSERT ON task_capability
  FOR EACH ROW EXECUTE FUNCTION copertura_solo_su_snapshot_proposto();
CREATE TRIGGER task_capability_append_only BEFORE UPDATE OR DELETE ON task_capability
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER task_capability_no_truncate BEFORE TRUNCATE ON task_capability
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();

-- 2. Profili di pesi e rubriche: l'applicazione li registra solo come bozze; attivarli e approvarli è del
--    proprietario dello schema (procedura di governance), non del ruolo applicativo.
CREATE FUNCTION solo_bozze_dall_applicazione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  proprietario name;
BEGIN
  SELECT tableowner INTO proprietario FROM pg_tables WHERE schemaname = 'public' AND tablename = TG_TABLE_NAME;
  IF pg_has_role(current_user, proprietario, 'MEMBER') THEN
    RETURN NEW;
  END IF;
  -- Rami separati: PL/pgSQL risolve i campi di NEW solo nel ramo eseguito (is_active o is_current).
  IF NEW.approved_by IS NOT NULL OR NEW.approved_at IS NOT NULL THEN
    RAISE EXCEPTION 'l''applicazione registra solo bozze non approvate in %', TG_TABLE_NAME;
  END IF;
  IF TG_TABLE_NAME = 'weight_profiles' THEN
    IF NEW.is_active THEN
      RAISE EXCEPTION 'l''applicazione registra solo bozze non approvate in %', TG_TABLE_NAME;
    END IF;
  ELSIF NEW.is_current THEN
    RAISE EXCEPTION 'l''applicazione registra solo bozze non approvate in %', TG_TABLE_NAME;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER profili_solo_bozze BEFORE INSERT ON weight_profiles
  FOR EACH ROW EXECUTE FUNCTION solo_bozze_dall_applicazione();
CREATE TRIGGER rubriche_solo_bozze BEFORE INSERT ON rubric_versions
  FOR EACH ROW EXECUTE FUNCTION solo_bozze_dall_applicazione();

-- 3. Un risultato cita una configurazione approvata, il tipo di capacità del suo snapshot e il task e il ruolo
--    attuali dell'occorrenza; il profilo è quello comune o dell'organizzazione del ruolo.
CREATE FUNCTION stima_coerente() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  s capability_snapshots;
  org_profilo uuid;
  org_ruolo uuid;
BEGIN
  SELECT * INTO s FROM capability_snapshots WHERE snapshot_id = NEW.snapshot_id;
  IF s.approved_by IS NULL OR s.status NOT IN ('published', 'retired') THEN
    RAISE EXCEPTION 'il risultato cita uno snapshot non approvato';
  END IF;
  IF NEW.tipo_capacita IS NOT NULL AND NEW.tipo_capacita <> s.tipo_capacita THEN
    RAISE EXCEPTION 'il risultato dichiara una capacità diversa da quella del suo snapshot';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM rubric_versions WHERE version = NEW.rubric_version AND approved_by IS NOT NULL) THEN
    RAISE EXCEPTION 'il risultato cita una rubrica non approvata';
  END IF;
  SELECT org_id INTO org_profilo FROM weight_profiles WHERE profile_id = NEW.profile_id AND approved_by IS NOT NULL;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'il risultato cita un profilo di pesi non approvato';
  END IF;
  SELECT r.org_id INTO org_ruolo FROM task_occurrences o JOIN roles r USING (role_id)
  WHERE o.occurrence_id = NEW.occurrence_id AND o.task_id = NEW.task_id AND o.role_id = NEW.role_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'il risultato non corrisponde a un''occorrenza attuale (task e ruolo)';
  END IF;
  IF org_profilo IS NOT NULL AND org_profilo <> org_ruolo THEN
    RAISE EXCEPTION 'il profilo di pesi è di un''altra organizzazione';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER stime_coerenti BEFORE INSERT ON policy_estimates
  FOR EACH ROW EXECUTE FUNCTION stima_coerente();

CREATE INDEX task_occurrences_per_ruolo ON task_occurrences (role_id);
CREATE INDEX stime_ultime ON policy_estimates (occurrence_id, profile_id, snapshot_id, rubric_version, computed_at DESC);

-- 4. Un profilo di pesi o una rubrica approvati non cambiano valori: un cambio è un profilo o una rubrica nuovi
--    (i risultati citano il loro identificativo). Si possono solo attivare, disattivare o rendere correnti.
ALTER TABLE weight_profiles ADD CONSTRAINT profili_non_negativi CHECK (
  w_k1 >= 0 AND w_k2 >= 0 AND w_k3 >= 0 AND w_d1 >= 0 AND w_d2 >= 0 AND w_d3 >= 0 AND w_d4 >= 0
  AND lambda_r >= 0 AND theta_n BETWEEN 0 AND 1 AND theta_d BETWEEN 0 AND 1);

CREATE FUNCTION approvati_immutabili() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF OLD.approved_by IS NOT NULL AND (
       (to_jsonb(NEW) - 'is_active' - 'is_current') IS DISTINCT FROM (to_jsonb(OLD) - 'is_active' - 'is_current')) THEN
    RAISE EXCEPTION '% approvato: i valori non cambiano, serve una versione nuova', TG_TABLE_NAME;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER profili_approvati_immutabili BEFORE UPDATE ON weight_profiles
  FOR EACH ROW EXECUTE FUNCTION approvati_immutabili();
CREATE TRIGGER rubriche_approvate_immutabili BEFORE UPDATE ON rubric_versions
  FOR EACH ROW EXECUTE FUNCTION approvati_immutabili();
