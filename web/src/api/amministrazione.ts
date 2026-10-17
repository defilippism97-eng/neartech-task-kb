// API della corsia «amministrazione» (docs/piani/fase-6-cantiere.md): account, credenziali, utenti, ruoli,
// organizzazioni e console di amministrazione. Modulo della sola corsia amministrazione, sopra
// neartech.api.rotte.amministrazione. Le funzioni aggiunte a questo oggetto compaiono in `api` senza toccare
// index.ts, e i tipi esportati da qui si importano da '../api'. Si usano richiesta e org di './client' e i tipi
// comuni di './tipi'; i nomi delle funzioni e dei tipi devono essere unici fra tutti i moduli (un doppione si vede
// nei test e in tsc).
export const amministrazione = {}
