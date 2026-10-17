// API della corsia «ascolto» (docs/piani/fase-6-cantiere.md): ascolto del comitato: materiali, interviste, schede
// di scenario, stima dei pesi. Modulo della sola corsia ascolto, sopra neartech.api.rotte.ascolto. Le funzioni
// aggiunte a questo oggetto compaiono in `api` senza toccare index.ts, e i tipi esportati da qui si importano da
// '../api'. Si usano richiesta e org di './client' e i tipi comuni di './tipi'; i nomi delle funzioni e dei tipi
// devono essere unici fra tutti i moduli (un doppione si vede nei test e in tsc).
export const ascolto = {}
