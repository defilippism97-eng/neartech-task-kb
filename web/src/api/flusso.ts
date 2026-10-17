// API della corsia «flusso» (docs/piani/fase-6-cantiere.md): lavori di ricalcolo, fase di verifica, storico e
// stampa delle restituzioni, reversibilità della pipeline dei documenti. Modulo della sola corsia flusso, sopra
// neartech.api.rotte.flusso. Le funzioni aggiunte a questo oggetto compaiono in `api` senza toccare index.ts, e i
// tipi esportati da qui si importano da '../api'. Si usano richiesta e org di './client' e i tipi comuni di
// './tipi'; i nomi delle funzioni e dei tipi devono essere unici fra tutti i moduli (un doppione si vede nei test
// e in tsc).
export const flusso = {}
