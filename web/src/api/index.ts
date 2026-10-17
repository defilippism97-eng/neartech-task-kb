// Client dell'API della piattaforma, un modulo per area (docs/piani/fase-6-cantiere.md). Le viste importano da
// '../api': `api` riunisce le funzioni di tutti i moduli, e qui si riesportano i loro tipi.
//
// Il file elenca già tutti i moduli, anche quelli ancora vuoti delle corsie: una corsia aggiunge funzioni e tipi nel
// proprio modulo e non tocca questo file. Un nome doppio fra due moduli è un errore di tsc (tipi) e del test
// src/test/api.test.ts (funzioni).
import { amministrazione } from './amministrazione'
import { ascolto } from './ascolto'
import { base } from './base'
import { conoscenza } from './conoscenza'
import { documenti } from './documenti'
import { flusso } from './flusso'
import { governo } from './governo'
import { indirizzi } from './indirizzi'
import { lotti } from './lotti'
import { panoramica } from './panoramica'
import { questionari } from './questionari'
import { revisione } from './revisione'
import { revisione_lavoro } from './revisione_lavoro'
import { sito } from './sito'

export { ErroreApi, GIA_DECISA, riprova, SUPERATA } from './client'

export type * from './tipi'
export type * from './base'
export type * from './panoramica'
export type * from './indirizzi'
export type * from './revisione'
export type * from './documenti'
export type * from './lotti'
export type * from './amministrazione'
export type * from './conoscenza'
export type * from './flusso'
export type * from './revisione_lavoro'
export type * from './questionari'
export type * from './ascolto'
export type * from './governo'
export type * from './sito'

// Moduli in ordine fisso: gli stessi che compongono `api`, per i controlli dei test.
export const MODULI_API = {
  base, panoramica, indirizzi, revisione, documenti, lotti,
  amministrazione, conoscenza, flusso, revisione_lavoro, questionari, ascolto, governo, sito,
}

export const api = {
  ...base,
  ...panoramica,
  ...indirizzi,
  ...revisione,
  ...documenti,
  ...lotti,
  ...amministrazione,
  ...conoscenza,
  ...flusso,
  ...revisione_lavoro,
  ...questionari,
  ...ascolto,
  ...governo,
  ...sito,
}
