-- Migrazione 0004: ogni occorrenza estratta da una job description porta il modello e l'impronta
-- del prompt che l'hanno proposta, come le relazioni del crosswalk. Si applica dopo la 0003.
-- La tabella task_occurrences è vuota quando questa migrazione viene applicata.

ALTER TABLE task_occurrences
  ADD COLUMN model_name text NOT NULL,
  ADD COLUMN prompt_hash text NOT NULL;
