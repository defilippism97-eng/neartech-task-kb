-- Migrazione 0007: registro delle migrazioni applicate.
-- Si applica dopo la 0006. Lo scrive neartech.migrazioni (scripts/migra.py).
-- Ogni riga porta l'hash del file con fine riga normalizzate: una migrazione registrata
-- non si modifica, se ne scrive una nuova. Le migrazioni dello spazio organizzazione
-- (db/migrations_org) sono registrate con lo schema dell'organizzazione.

CREATE TABLE migrazioni_applicate (
  schema_destinazione text NOT NULL,
  nome text NOT NULL,
  hash_sha256 text NOT NULL,
  applicata_il timestamptz NOT NULL DEFAULT now(),
  applicata_da text NOT NULL DEFAULT current_user,
  PRIMARY KEY (schema_destinazione, nome)
);
