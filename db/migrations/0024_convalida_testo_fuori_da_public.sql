-- Migrazione 0024: convalida dei vincoli della 0023 su tutte le righe.
-- Si applica dopo la pulizia del testo di Società Dolce (neartech.occorrenze.togli_testo_da_public,
-- eseguita il 2026-10-17): da qui in poi nessuna riga di public contiene testo del cliente.

ALTER TABLE task_occurrences VALIDATE CONSTRAINT task_occurrences_senza_testo;
ALTER TABLE roles VALIDATE CONSTRAINT roles_nome_neutro;
ALTER TABLE sources VALIDATE CONSTRAINT sources_documento_neutro;
