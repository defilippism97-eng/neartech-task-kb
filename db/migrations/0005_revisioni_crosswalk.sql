-- Migrazione 0005: esiti della revisione umana sul campione del crosswalk.
-- Ogni esito è un record separato e non si sovrascrive: una nuova revisione è una nuova riga.
-- Si applica dopo la 0004.

CREATE TABLE revisioni_crosswalk (
  revisione_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL REFERENCES canonical_tasks,
  node_id uuid NOT NULL REFERENCES taxonomy_nodes,
  relazione_proposta text NOT NULL,
  esito text NOT NULL CHECK (esito IN ('ok', 'parziale', 'no')),
  nota text,
  revisore text NOT NULL,
  campione text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (task_id, node_id, campione)
);
