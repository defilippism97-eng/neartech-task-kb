-- Migrazione 0003: ogni relazione del Crosswalk Mapper porta il modello e l'impronta del prompt
-- che l'hanno prodotta, come ogni altro giudizio del modello. Si applica dopo la 0002.
-- La tabella task_mappings è vuota quando questa migrazione viene applicata.

ALTER TABLE task_mappings
  ADD COLUMN model_name text NOT NULL,
  ADD COLUMN prompt_hash text NOT NULL;
