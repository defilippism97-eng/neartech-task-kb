-- Migrazione 0029: nessun elemento si aggiunge a un campione già creato (seguito della revisione del
-- 2026-10-17). Si applica dopo la 0028.
-- La 0020 controlla il numero di elementi solo alla fine della transazione che crea il campione, e
-- rifiuta gli elementi nuovi solo dopo il primo giudizio. Un elemento aggiunto più tardi, prima dei
-- giudizi, cambiava il campione senza un atto. Ora anche ogni elemento nuovo richiede che, a fine
-- transazione, il campione abbia esattamente `dimensione` elementi: in una transazione successiva alla
-- creazione il conteggio supera la dimensione e l'inserimento è rifiutato.

SET LOCAL lock_timeout = '10s';

CREATE FUNCTION controlla_elementi_del_campione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  IF (SELECT count(*) FROM elementi_campione WHERE campione_id = NEW.campione_id)
     <> (SELECT dimensione FROM campioni_revisione WHERE campione_id = NEW.campione_id) THEN
    RAISE EXCEPTION 'il campione % non ha il numero di elementi della sua dimensione', NEW.campione_id;
  END IF;
  RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER elementi_campione_completi
  AFTER INSERT ON elementi_campione DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION controlla_elementi_del_campione();
