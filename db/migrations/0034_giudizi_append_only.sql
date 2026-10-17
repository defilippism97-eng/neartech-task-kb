-- Migrazione 0034: le valutazioni sono giudizi, un record ciascuno (CLAUDE.md): non si modificano né si
-- cancellano. L'ora di ogni giudizio è quella della sua scrittura, non dell'inizio della transazione: due
-- giudizi della stessa persona nella stessa transazione restano in ordine (neartech.calcolo usa l'ultimo).
-- Si applica dopo la 0033. Le righe esistenti non cambiano.

SET LOCAL lock_timeout = '10s';

ALTER TABLE assessment_runs ALTER COLUMN created_at SET DEFAULT clock_timestamp();

CREATE TRIGGER valutazioni_append_only BEFORE UPDATE OR DELETE ON assessment_runs
  FOR EACH ROW EXECUTE FUNCTION vieta_modifiche();
CREATE TRIGGER valutazioni_no_truncate BEFORE TRUNCATE ON assessment_runs
  FOR EACH STATEMENT EXECUTE FUNCTION vieta_modifiche();
