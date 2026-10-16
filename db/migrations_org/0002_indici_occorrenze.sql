-- Migrazione 0002 dello spazio organizzazione: indici sulle chiavi esterne delle occorrenze.
-- Si applica dopo la 0001 a ogni schema org_<codice>. UNIQUE (task_id, ruolo_id) copre già task_id.

CREATE INDEX occorrenze_ruolo ON occorrenze (ruolo_id);
CREATE INDEX occorrenze_documento ON occorrenze (documento_id);
