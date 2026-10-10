-- Schema F0 della KB Neartech (PostgreSQL 16 + pgvector).
-- Estratto dall'appendice di docs/piano-sviluppo-v2.md. Le regole di progetto restano:
-- tabelle separate, nessuna soglia o peso nel codice, un record per ogni giudizio.

CREATE EXTENSION IF NOT EXISTS vector;
-- Fonti e tassonomie

CREATE TABLE sources (
source_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
kind text NOT NULL, -- taxonomy | evidence | org_document | survey | panel
name text NOT NULL,
version text NOT NULL,
uri text,
license text,
content_hash text NOT NULL,
retrieved_at timestamptz NOT NULL DEFAULT now(),
UNIQUE (name, version)
);

CREATE TABLE taxonomy_nodes (
node_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
scheme text NOT NULL CHECK (scheme IN ('ONET_TASK','ONET_DWA','ONET_IWA','ESCO_OCC','ESCO_SKILL','ATLANTE_ADA','ISCO08','CP2021')),
code text NOT NULL,
label text NOT NULL,
lang text NOT NULL,
parent_id uuid REFERENCES taxonomy_nodes,
source_id uuid NOT NULL REFERENCES sources,
UNIQUE (scheme, code, lang, source_id)
);
-- Task canonici, organizzazioni, occorrenze

CREATE TABLE canonical_tasks (
task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
title_it text NOT NULL UNIQUE,
granularity smallint NOT NULL CHECK (granularity BETWEEN 1 AND 3),
status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','merged','retired')),
merged_into uuid REFERENCES canonical_tasks,
created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE task_mappings (
task_id uuid REFERENCES canonical_tasks,
node_id uuid REFERENCES taxonomy_nodes,
relation text NOT NULL CHECK (relation IN ('exact','broad','narrow','related')),
confidence numeric(3,2) NOT NULL,
rationale text NOT NULL,
validated boolean NOT NULL DEFAULT false,
PRIMARY KEY (task_id, node_id)
);

CREATE TABLE organizations (
org_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
name text NOT NULL,
sector text
);

CREATE TABLE roles (
role_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
org_id uuid NOT NULL REFERENCES organizations,
name text NOT NULL,
family text,
UNIQUE (org_id, name)
);

CREATE TABLE task_occurrences (
occurrence_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
task_id uuid NOT NULL REFERENCES canonical_tasks,
role_id uuid NOT NULL REFERENCES roles,
context_note text,
raw_snippet text NOT NULL,
time_share numeric(5,4) CHECK (time_share BETWEEN 0 AND 1),
source_id uuid NOT NULL REFERENCES sources,
UNIQUE (task_id, role_id)
);
-- Embedding per modello, con indice parziale a dimensione fissa

CREATE TABLE task_embeddings (
task_id uuid REFERENCES canonical_tasks,
model_name text,
vec vector NOT NULL,
PRIMARY KEY (task_id, model_name)
);
CREATE INDEX task_emb_bge_m3 ON task_embeddings
USING hnsw ((vec::vector(1024)) vector_cosine_ops)
WHERE model_name = 'BAAI/bge-m3';
-- Evidenze e snapshot di copertura

CREATE TABLE evidence_items (
evidence_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
source_id uuid NOT NULL REFERENCES sources,
evidence_type text NOT NULL CHECK (evidence_type IN ('benchmark','usage_success','usage','internal_pilot','expert','llm_prior')),
node_id uuid REFERENCES taxonomy_nodes,
task_id uuid REFERENCES canonical_tasks,
dimension text NOT NULL CHECK (dimension IN ('k1','k2','k3','any')),
raw_value numeric NOT NULL,
score_0_4 numeric(3,2) NOT NULL CHECK (score_0_4 BETWEEN 0 AND 4),
quality numeric(3,2) NOT NULL,
observed_at date NOT NULL,
CHECK (node_id IS NOT NULL OR task_id IS NOT NULL)
);

CREATE TABLE capability_snapshots (
snapshot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
as_of date NOT NULL,
method_version text NOT NULL,
half_life_days int NOT NULL,
status text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed','published','retired')),
approved_by text,
approved_at timestamptz
);
CREATE UNIQUE INDEX one_published_snapshot ON capability_snapshots (status) WHERE status = 'published';

CREATE TABLE task_capability (
snapshot_id uuid REFERENCES capability_snapshots,
task_id uuid REFERENCES canonical_tasks,
dimension text CHECK (dimension IN ('k1','k2','k3')),
c_mean numeric(3,2) NOT NULL,
c_low numeric(3,2) NOT NULL,
c_high numeric(3,2) NOT NULL,
n_evidence int NOT NULL,
PRIMARY KEY (snapshot_id, task_id, dimension)
);
-- Versioni della rubrica (una sola corrente)

CREATE TABLE rubric_versions (
version text PRIMARY KEY,
is_current boolean NOT NULL DEFAULT false,
approved_by text,
approved_at timestamptz
);
CREATE UNIQUE INDEX one_current_rubric ON rubric_versions (is_current) WHERE is_current;
-- Valutazioni: un record per ogni singolo giudizio (campione di modello o persona)

CREATE TABLE assessment_runs (
run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
target_kind text NOT NULL CHECK (target_kind IN ('task','occurrence')),
target_id uuid NOT NULL,
item text NOT NULL CHECK (item IN ('k1','k2','k3','r','d1','d2','d3','d4')),
value smallint NOT NULL CHECK (value BETWEEN 0 AND 4),
rater_kind text NOT NULL CHECK (rater_kind IN ('llm','expert','worker','beneficiary')),
rater_ref text NOT NULL, -- id pseudonimo o identificativo del modello
rubric_version text NOT NULL REFERENCES rubric_versions,
prompt_hash text,
rationale text,
campaign_id text,
created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ar_target ON assessment_runs (target_kind, target_id, item, rubric_version);
-- Governance: profili di peso per organizzazione (org_id NULL = profilo di default)

CREATE TABLE weight_profiles (
profile_id text PRIMARY KEY,
org_id uuid REFERENCES organizations,
w_k1 numeric(4,3) NOT NULL, w_k2 numeric(4,3) NOT NULL, w_k3 numeric(4,3) NOT NULL,
lambda_r numeric(4,3) NOT NULL DEFAULT 0.5,
w_d1 numeric(4,3) NOT NULL, w_d2 numeric(4,3) NOT NULL, w_d3 numeric(4,3) NOT NULL, w_d4 numeric(4,3) NOT NULL,
theta_n numeric(3,2) NOT NULL DEFAULT 0.50,
theta_d numeric(3,2) NOT NULL DEFAULT 0.50,
is_active boolean NOT NULL DEFAULT false,
approved_by text,
approved_at timestamptz,
CHECK (abs(w_k1 + w_k2 + w_k3 - 1) < 0.001),
CHECK (abs(w_d1 + w_d2 + w_d3 + w_d4 - 1) < 0.001)
);
CREATE UNIQUE INDEX one_active_profile_per_org
ON weight_profiles (COALESCE(org_id, '00000000-0000-0000-0000-000000000000'::uuid)) WHERE is_active;
-- Risultati materializzati dal job di calcolo (simulazione Monte Carlo)

CREATE TABLE policy_estimates (
occurrence_id uuid REFERENCES task_occurrences,
profile_id text REFERENCES weight_profiles,
snapshot_id uuid REFERENCES capability_snapshots,
rubric_version text REFERENCES rubric_versions,
n_mean numeric(4,3), n_sd numeric(4,3),
d_mean numeric(4,3), d_sd numeric(4,3),
p_q1 numeric(4,3), p_q2 numeric(4,3), p_q3 numeric(4,3), p_q4 numeric(4,3),
d_source_mix jsonb NOT NULL, -- quota di D da panel, survey, stima preliminare
computed_at timestamptz NOT NULL DEFAULT now(),
PRIMARY KEY (occurrence_id, profile_id, snapshot_id, rubric_version)
);
-- Indirizzi forniti dagli utenti agli agenti

CREATE TABLE steering_directives (
directive_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
scope text NOT NULL, -- es. family:servizi_persona, source:AEI
instruction text NOT NULL,
priority smallint NOT NULL DEFAULT 2,
expires_at date,
created_by text NOT NULL
);
-- Esecuzione: coda di lavoro e registro degli agenti

CREATE TABLE jobs (
job_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
kind text NOT NULL,
payload jsonb NOT NULL,
status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','done','failed')),
attempts int NOT NULL DEFAULT 0,
run_after timestamptz NOT NULL DEFAULT now(),
created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE agent_runs (
agent_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
job_id uuid REFERENCES jobs,
component text NOT NULL,
model_id text,
prompt_hash text,
duration_ms int,
cost_usd numeric(10,4),
started_at timestamptz NOT NULL DEFAULT now()
);

CREATE VIEW v_role_metrics AS
WITH cur AS (
SELECT pe.*, o.role_id, o.time_share AS p
FROM policy_estimates pe
JOIN task_occurrences o USING (occurrence_id)
JOIN roles r ON r.role_id = o.role_id
JOIN weight_profiles w ON w.profile_id = pe.profile_id AND w.is_active
AND (w.org_id = r.org_id OR (w.org_id IS NULL AND NOT EXISTS (
SELECT 1 FROM weight_profiles w2 WHERE w2.org_id = r.org_id AND w2.is_active)))
JOIN capability_snapshots s ON s.snapshot_id = pe.snapshot_id AND s.status = 'published'
JOIN rubric_versions rv ON rv.version = pe.rubric_version AND rv.is_current
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
