-- Migrazione 0001 dello spazio organizzazione (ADR 0001).
-- Si applica a ogni schema org_<codice> con search_path = org_<codice>, public
-- (neartech.migrazioni.applica). I nomi senza schema finiscono nello spazio
-- dell'organizzazione; i riferimenti al dataset condiviso usano public esplicitamente.
-- Qui sta il testo del cliente: estratti e note dei documenti, ruoli dell'organizzazione.
-- Nel dataset condiviso entra solo la rielaborazione (public.canonical_tasks).

CREATE TABLE ruoli_organizzativi (
  ruolo_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nome text NOT NULL UNIQUE,
  famiglia text,
  creato_il timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE documenti (
  documento_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nome_file text NOT NULL,
  sha256 text NOT NULL UNIQUE,
  tipo text NOT NULL,
  caricato_il timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE occorrenze (
  occorrenza_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL REFERENCES public.canonical_tasks,
  ruolo_id uuid NOT NULL REFERENCES ruoli_organizzativi,
  documento_id uuid REFERENCES documenti,
  estratto text NOT NULL,
  nota_contesto text,
  quota_tempo numeric(5,4) CHECK (quota_tempo BETWEEN 0 AND 1),
  model_name text,
  prompt_hash text,
  creata_il timestamptz NOT NULL DEFAULT now(),
  UNIQUE (task_id, ruolo_id)
);
