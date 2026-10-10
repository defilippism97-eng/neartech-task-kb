-- Migrazione 0002: livelli dell'Atlante del Lavoro e embedding dei nodi di tassonomia.
-- Si applica dopo db/schema.sql. Non modifica lo schema originale in place.

-- L'Atlante ha tre livelli: ADA, risultati attesi e attività.
ALTER TABLE taxonomy_nodes DROP CONSTRAINT taxonomy_nodes_scheme_check;
ALTER TABLE taxonomy_nodes ADD CONSTRAINT taxonomy_nodes_scheme_check
  CHECK (scheme IN ('ONET_TASK','ONET_DWA','ONET_IWA','ESCO_OCC','ESCO_SKILL',
                    'ATLANTE_ADA','ATLANTE_RA','ATLANTE_ATTIVITA','ISCO08','CP2021'));

-- Embedding dei nodi di tassonomia, per modello. Servono per la ricerca dei candidati
-- del Crosswalk Mapper (i 20 nodi più vicini per ciascun task canonico).
CREATE TABLE taxonomy_embeddings (
  node_id uuid REFERENCES taxonomy_nodes ON DELETE CASCADE,
  model_name text NOT NULL,
  vec vector(1024) NOT NULL,
  PRIMARY KEY (node_id, model_name)
);
CREATE INDEX tax_emb_bge_m3 ON taxonomy_embeddings
  USING hnsw (vec vector_cosine_ops)
  WHERE model_name = 'BAAI/bge-m3';
