-- Migrazione 0006: giudizi per schema del crosswalk (anche "nessuna corrispondenza"),
-- proposte di fusione del Canonicalizer e vista con l'origine dei task.
-- Si applica dopo la 0005. Ogni giudizio è un record; non si sovrascrive.

CREATE TABLE crosswalk_giudizi (
  task_id uuid REFERENCES canonical_tasks,
  scheme text NOT NULL,
  esito text NOT NULL CHECK (esito IN ('relazioni', 'nessuna')),
  n_relazioni integer NOT NULL CHECK (n_relazioni >= 0),
  model_name text NOT NULL,
  prompt_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (task_id, scheme)
);

CREATE TABLE fusioni_proposte (
  proposal_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL REFERENCES canonical_tasks,
  altro_task_id uuid NOT NULL REFERENCES canonical_tasks,
  decisione text NOT NULL CHECK (decisione IN ('stessa_attivita', 'diversa')),
  motivazione text NOT NULL,
  model_name text NOT NULL,
  prompt_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (task_id, altro_task_id),
  CHECK (task_id <> altro_task_id)
);

-- Origine dei task: da quali fonti provengono e quante relazioni hanno con le tassonomie.
-- Un task con fonte "Job Società Dolce" e nessuna relazione è un'aggiunta alla KB non presente nelle tassonomie.
CREATE VIEW v_task_origine AS
SELECT t.task_id, t.title_it, t.granularity, t.status,
       COALESCE(array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL), '{}') AS fonti_origine,
       count(DISTINCT m.node_id) AS relazioni_tassonomie
FROM canonical_tasks t
LEFT JOIN task_occurrences o ON o.task_id = t.task_id
LEFT JOIN sources s ON s.source_id = o.source_id
LEFT JOIN task_mappings m ON m.task_id = t.task_id
GROUP BY t.task_id, t.title_it, t.granularity, t.status;
