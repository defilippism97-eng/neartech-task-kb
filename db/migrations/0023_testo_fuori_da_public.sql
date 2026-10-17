-- Migrazione 0023: il testo del cliente non sta in public (ADR 0001, ADR 0005).
-- Si applica dopo la 0022. In public restano legami con gli stessi identificativi dello spazio
-- dell'organizzazione e nomi neutri; il testo sta in org_<codice>.
-- I vincoli sono NOT VALID: valgono subito per righe nuove e modificate. Il testo già presente
-- (Società Dolce) si toglie con neartech.occorrenze.togli_testo_da_public; la 0024 li convalida.

ALTER TABLE task_occurrences ALTER COLUMN raw_snippet DROP NOT NULL;

ALTER TABLE task_occurrences
  ADD CONSTRAINT task_occurrences_senza_testo CHECK (raw_snippet IS NULL AND context_note IS NULL) NOT VALID;
ALTER TABLE roles
  ADD CONSTRAINT roles_nome_neutro CHECK (name = 'ruolo ' || role_id::text) NOT VALID;
ALTER TABLE sources
  ADD CONSTRAINT sources_documento_neutro CHECK (kind <> 'org_document' OR name = 'documento ' || source_id::text) NOT VALID;
