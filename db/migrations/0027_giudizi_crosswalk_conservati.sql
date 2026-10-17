-- Migrazione 0027: i giudizi del crosswalk non si cancellano (CLAUDE.md, un record per ogni giudizio;
-- seguito della revisione del 2026-10-17). Si applica dopo la 0026.
-- Prima la fusione del Canonicalizer cancellava i giudizi del task fuso. Ora restano, e la vista
-- v_crosswalk_giudizi dice se riguardano un task fuso e in quale task è confluito. Il marcatore si
-- ricava da canonical_tasks, senza modificare il giudizio: se una scissione riattiva il task
-- (neartech.scissione), i suoi giudizi tornano validi così come sono.

SET LOCAL lock_timeout = '10s';

REVOKE DELETE ON crosswalk_giudizi FROM neartech_app;

CREATE TRIGGER crosswalk_giudizi_append_only BEFORE UPDATE OR DELETE ON crosswalk_giudizi
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER crosswalk_giudizi_no_truncate BEFORE TRUNCATE ON crosswalk_giudizi
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();

CREATE VIEW v_crosswalk_giudizi AS
SELECT g.task_id, g.scheme, g.esito, g.n_relazioni, g.model_name, g.prompt_hash, g.created_at,
       t.status = 'merged' AS task_fuso,
       t.merged_into AS fuso_in
FROM crosswalk_giudizi g
JOIN canonical_tasks t USING (task_id);

GRANT SELECT ON v_crosswalk_giudizi TO neartech_app, neartech_lettura;
