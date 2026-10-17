-- Migrazione 0021: l'amministratore tecnico interviene sul dataset centrale (decisione d, 2026-10-16;
-- docs/metodologia-estensioni.md, sezione 10): stato di validazione dei task condivisi e separazione
-- delle fusioni del Canonicalizer giudicate sbagliate.

ALTER TABLE permessi_ruolo DISABLE TRIGGER permessi_no_insert;
INSERT INTO permessi_ruolo (ruolo, azione) VALUES ('amministratore_tecnico', 'gestire_dataset_centrale');
ALTER TABLE permessi_ruolo ENABLE TRIGGER permessi_no_insert;
