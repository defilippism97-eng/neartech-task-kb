-- Migrazione 0011: stato di validazione dei task del dataset condiviso.
-- Si applica dopo la 0010. Stati (docs/HANDOVER.md, sezione 3): validato (rivisto da
-- persone), stima_modello (provvisorio), da_integrare (non rivisto). Ogni cambio è una
-- riga legata a un atto nel registro delle decisioni; un task senza storia è da_integrare.
-- Non riguarda canonical_tasks.status, che indica se il task è attivo, fuso o ritirato.

CREATE TABLE stati_validazione_task (
  cambio_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  task_id uuid NOT NULL REFERENCES canonical_tasks,
  stato text NOT NULL CHECK (stato IN ('validato', 'stima_modello', 'da_integrare')),
  decisione_id bigint NOT NULL REFERENCES registro_decisioni,
  registrato_il timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX stati_validazione_task_id ON stati_validazione_task (task_id, cambio_id DESC);
CREATE TRIGGER stati_validazione_append_only
  BEFORE UPDATE OR DELETE ON stati_validazione_task
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();

CREATE VIEW stato_validazione_corrente AS
SELECT t.task_id, COALESCE(s.stato, 'da_integrare') AS stato, s.decisione_id
FROM canonical_tasks t
LEFT JOIN LATERAL (
  SELECT stato, decisione_id FROM stati_validazione_task v
  WHERE v.task_id = t.task_id ORDER BY cambio_id DESC LIMIT 1
) s ON true;
