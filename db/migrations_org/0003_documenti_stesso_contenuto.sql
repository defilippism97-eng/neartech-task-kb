-- Migrazione 0003 dello spazio organizzazione: due documenti possono avere lo stesso contenuto
-- (per esempio due versioni dello stesso file). L'identità è documento_id; sha256 resta indicizzato.

ALTER TABLE documenti DROP CONSTRAINT documenti_sha256_key;
CREATE INDEX documenti_sha256 ON documenti (sha256);
