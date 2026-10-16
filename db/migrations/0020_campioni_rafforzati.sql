-- Migrazione 0020: rafforzamenti di campioni e misure dopo le revisioni della fase 2 (2026-10-16).
-- Si applica dopo la 0019. Le tabelle della 0019 sono vuote ovunque (nessuna è in produzione).

-- 1. Campioni: un censimento ('tutte') copre tutta la popolazione; per un campione importato la
-- popolazione è quella da cui era stato estratto in origine.
ALTER TABLE campioni_revisione
  ADD CONSTRAINT campioni_censimento_completo CHECK (criterio IN ('casuale', 'importato') OR dimensione = popolazione),
  ADD CONSTRAINT campioni_istruzioni_presenti CHECK (length(btrim(versione_istruzioni)) > 0),
  ADD CONSTRAINT campioni_filtro_oggetto CHECK (jsonb_typeof(filtro) = 'object');

CREATE FUNCTION controlla_decisione_campione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM registro_decisioni
                 WHERE decisione_id = NEW.decisione_id AND tipo_oggetto = 'campione_revisione'
                   AND oggetto_id = NEW.campione_id::text AND atto = 'approvazione'
                   AND org_id IS NOT DISTINCT FROM NEW.org_id) THEN
    RAISE EXCEPTION 'la decisione % non approva il campione %', NEW.decisione_id, NEW.campione_id;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER campioni_controlla_decisione BEFORE INSERT ON campioni_revisione
  FOR EACH ROW EXECUTE FUNCTION controlla_decisione_campione();

-- A fine transazione un campione ha esattamente `dimensione` elementi.
CREATE FUNCTION controlla_elementi_completi() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF (SELECT count(*) FROM elementi_campione WHERE campione_id = NEW.campione_id) <> NEW.dimensione THEN
    RAISE EXCEPTION 'il campione % non ha % elementi', NEW.campione_id, NEW.dimensione;
  END IF;
  RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER campioni_elementi_completi
  AFTER INSERT ON campioni_revisione DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION controlla_elementi_completi();

-- 2. Elementi: forma del riferimento per tipo di proposta, una proposta una volta sola,
-- fotografia di modello e prompt all'estrazione, nessuna aggiunta dopo i giudizi.
ALTER TABLE elementi_campione
  ADD COLUMN origine jsonb NOT NULL DEFAULT '{}'::jsonb,
  ADD CONSTRAINT elementi_riferimento_oggetto CHECK (jsonb_typeof(riferimento) = 'object');

CREATE FUNCTION controlla_elemento() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  tipo text;
  attese text[];
  chiavi text[];
  formato_uuid constant text := '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
BEGIN
  SELECT tipo_proposta INTO tipo FROM campioni_revisione WHERE campione_id = NEW.campione_id;
  attese := CASE tipo
              WHEN 'fusione' THEN ARRAY['proposal_id']
              WHEN 'crosswalk' THEN ARRAY['node_id', 'task_id']
            END;
  IF attese IS NULL THEN
    RAISE EXCEPTION 'tipo di proposta % non ancora gestito negli elementi', tipo;
  END IF;
  SELECT array_agg(k ORDER BY k) INTO chiavi FROM jsonb_object_keys(NEW.riferimento) AS k;
  IF chiavi IS DISTINCT FROM attese THEN
    RAISE EXCEPTION 'riferimento con chiavi % invece di %', chiavi, attese;
  END IF;
  IF EXISTS (SELECT 1 FROM jsonb_each_text(NEW.riferimento) AS v WHERE v.value !~ formato_uuid) THEN
    RAISE EXCEPTION 'riferimento con identificativi non canonici';
  END IF;
  IF EXISTS (SELECT 1 FROM giudizi_revisione WHERE campione_id = NEW.campione_id)
     OR EXISTS (SELECT 1 FROM misure_precisione WHERE campione_id = NEW.campione_id) THEN
    RAISE EXCEPTION 'il campione % ha già giudizi o misure: gli elementi non cambiano', NEW.campione_id;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER elementi_controllo BEFORE INSERT ON elementi_campione
  FOR EACH ROW EXECUTE FUNCTION controlla_elemento();

CREATE UNIQUE INDEX elementi_fusione_unica
  ON elementi_campione (campione_id, (riferimento ->> 'proposal_id')) WHERE riferimento ? 'proposal_id';
CREATE UNIQUE INDEX elementi_crosswalk_unico
  ON elementi_campione (campione_id, (riferimento ->> 'task_id'), (riferimento ->> 'node_id'))
  WHERE riferimento ? 'task_id';

-- 3. Giudizi: con la stessa versione delle istruzioni del campione.
ALTER TABLE giudizi_revisione
  ADD CONSTRAINT giudizi_istruzioni_presenti CHECK (length(btrim(versione_istruzioni)) > 0);

CREATE FUNCTION controlla_versione_giudizio() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF NEW.versione_istruzioni IS DISTINCT FROM
     (SELECT versione_istruzioni FROM campioni_revisione WHERE campione_id = NEW.campione_id) THEN
    RAISE EXCEPTION 'il giudizio usa istruzioni % diverse da quelle del campione', NEW.versione_istruzioni;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER giudizi_controlla_versione BEFORE INSERT ON giudizi_revisione
  FOR EACH ROW EXECUTE FUNCTION controlla_versione_giudizio();

-- 4. Misure: versione della rubrica, tipo di campione, posizione della soglia rispetto all'intervallo,
-- coerenza interna e codici dei parametri usati. Nessun valore di policy nei vincoli.
ALTER TABLE misure_precisione
  ADD COLUMN versione_istruzioni text NOT NULL,
  ADD COLUMN censimento boolean NOT NULL,
  ADD COLUMN soglia_nell_intervallo boolean NOT NULL,
  ADD CONSTRAINT misure_conteggi CHECK (
    n_corretti >= 0 AND n_parziali >= 0 AND n_errati >= 0
    AND n_corretti + n_parziali + n_errati = n_elementi),
  ADD CONSTRAINT misure_intervallo CHECK (intervallo_basso <= precisione AND precisione <= intervallo_alto),
  ADD CONSTRAINT misure_soglia CHECK (soglia BETWEEN 0 AND 1),
  ADD CONSTRAINT misure_livello CHECK (livello_confidenza > 0 AND livello_confidenza < 1),
  ADD CONSTRAINT misure_regola CHECK (regola_parziali IN ('errore', 'corretto', 'escluso')),
  ADD CONSTRAINT misure_esito_coerente CHECK ((esito = 'sopra_soglia') = (precisione >= soglia)),
  ADD CONSTRAINT misure_soglia_intervallo_coerente CHECK (
    soglia_nell_intervallo = (soglia BETWEEN intervallo_basso AND intervallo_alto));

CREATE FUNCTION controlla_parametri_misura() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF (SELECT codice FROM parametri_governance WHERE parametro_id = NEW.parametro_regola_id) <> 'regola_parziali'
     OR (SELECT codice FROM parametri_governance WHERE parametro_id = NEW.parametro_confidenza_id) <> 'livello_confidenza'
     OR (SELECT codice FROM parametri_governance WHERE parametro_id = NEW.parametro_soglia_id)
        <> 'soglia_precisione_abbinamento' THEN
    RAISE EXCEPTION 'i parametri indicati nella misura non sono quelli attesi';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER misure_controlla_parametri BEFORE INSERT ON misure_precisione
  FOR EACH ROW EXECUTE FUNCTION controlla_parametri_misura();
