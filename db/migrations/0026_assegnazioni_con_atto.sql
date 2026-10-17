-- Migrazione 0026: ogni assegnazione di ruolo ha il suo atto nel registro, firmato da chi poteva farla
-- (seguito della revisione di sicurezza del 2026-10-17). Si applica dopo la 0025.
-- Il ruolo neartech_app inserisce in assegnazioni_ruolo e registro_decisioni: senza questo controllo
-- chi ha la credenziale applicativa potrebbe concedersi un ruolo senza traccia. Alla fine della
-- transazione ogni assegnazione nuova deve avere l'atto 'approvazione' con tipo_oggetto
-- 'assegnazione_ruolo' (neartech.permessi.assegna_ruolo), con autore chi assegna e stessa organizzazione,
-- e l'autore deve avere gestire_utenti da un'altra assegnazione valida, globale o della stessa
-- organizzazione. Il bootstrap (assegnata_da vuoto) vale solo per l'amministratore tecnico, che la 0018
-- ammette quando non ce n'è un altro, e lo firma il nuovo amministratore stesso.
-- Limite dichiarato: chi ha la credenziale applicativa può ancora scrivere un atto falso a nome di un
-- amministratore. La credenziale resta il confine di fiducia (ADR 0003); il controllo rende l'abuso
-- visibile nel registro, protetto dalla catena di hash, e impedisce l'auto-promozione senza traccia.
-- Le assegnazioni già presenti non si ricontrollano: il vincolo vale per gli inserimenti nuovi.

SET LOCAL lock_timeout = '10s';

CREATE FUNCTION controlla_atto_assegnazione() RETURNS trigger
LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
DECLARE
  autore uuid := coalesce(NEW.assegnata_da, NEW.utente_id);
BEGIN
  IF NEW.assegnata_da IS NULL AND NEW.ruolo <> 'amministratore_tecnico' THEN
    RAISE EXCEPTION 'l''assegnazione % non indica chi l''ha concessa', NEW.assegnazione_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM registro_decisioni r
                 WHERE r.tipo_oggetto = 'assegnazione_ruolo' AND r.oggetto_id = NEW.assegnazione_id::text
                   AND r.atto = 'approvazione' AND r.autore_id = autore
                   AND r.org_id IS NOT DISTINCT FROM NEW.org_id) THEN
    RAISE EXCEPTION 'l''assegnazione % non ha il suo atto nel registro, firmato da chi assegna',
      NEW.assegnazione_id;
  END IF;
  IF NEW.assegnata_da IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM assegnazioni_ruolo a
       JOIN ruoli ru ON ru.codice = a.ruolo
       JOIN permessi_ruolo p ON p.ruolo = a.ruolo AND p.azione = 'gestire_utenti'
       WHERE a.utente_id = autore AND a.assegnazione_id <> NEW.assegnazione_id
         AND assegnazione_valida(a)
         AND (ru.ambito = 'globale' OR a.org_id = NEW.org_id)) THEN
    RAISE EXCEPTION 'chi ha concesso l''assegnazione % non ha gestire_utenti', NEW.assegnazione_id;
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER assegnazioni_con_atto
  AFTER INSERT ON assegnazioni_ruolo DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION controlla_atto_assegnazione();
