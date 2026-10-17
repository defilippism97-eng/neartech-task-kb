import { createRouter, type AnyRoute, type RouterHistory } from '@tanstack/react-router'
import * as amministrazione from './amministrazione'
import * as ascolto from './ascolto'
import * as base from './base'
import * as conoscenza from './conoscenza'
import * as documenti from './documenti'
import * as flusso from './flusso'
import { app, genitori, pubblico, radice } from './genitori'
import * as governo from './governo'
import * as indirizzi from './indirizzi'
import * as lotti from './lotti'
import * as panoramica from './panoramica'
import * as questionari from './questionari'
import * as revisione from './revisione'
import * as revisione_lavoro from './revisione_lavoro'
import * as sito from './sito'
import type { VoceNav } from './tipi'

// Albero delle rotte, un file per area (docs/piani/fase-6-cantiere.md). Ogni area esporta `rotte(genitori)`, le
// sue rotte appese a `pubblico` (sito, senza accesso) o ad `app` (/app, con accesso), e `voci`, le sue voci nel
// guscio. Questo file elenca già tutte le aree, anche quelle ancora vuote delle corsie: nessuna corsia lo modifica.

const AREE = [
  base, panoramica, indirizzi, revisione, documenti, lotti,
  amministrazione, conoscenza, flusso, revisione_lavoro, questionari, ascolto, governo, sito,
] as const

const tutte = [
  ...base.rotte(genitori),
  ...panoramica.rotte(genitori),
  ...indirizzi.rotte(genitori),
  ...revisione.rotte(genitori),
  ...documenti.rotte(genitori),
  ...lotti.rotte(genitori),
  ...amministrazione.rotte(genitori),
  ...conoscenza.rotte(genitori),
  ...flusso.rotte(genitori),
  ...revisione_lavoro.rotte(genitori),
  ...questionari.rotte(genitori),
  ...ascolto.rotte(genitori),
  ...governo.rotte(genitori),
  ...sito.rotte(genitori),
] as const

type Rotte = typeof tutte

// Le rotte di tutte le aree con il genitore dato: ogni rotta dichiara il suo con getParentRoute, qui le si appende.
// Il tipo resta quello delle singole rotte, così i Link restano controllati da tsc.
const opzioni = (r: AnyRoute) => r.options as { getParentRoute: () => AnyRoute; path?: string; id?: string }
const genitoreDi = (r: AnyRoute) => opzioni(r).getParentRoute()

function figliDi<G extends AnyRoute>(genitore: G): Extract<Rotte[number], { parentRoute: G }>[] {
  return tutte.filter((r) => genitoreDi(r) === genitore) as Extract<Rotte[number], { parentRoute: G }>[]
}

// Una rotta appesa a un genitore diverso da pubblico e app resterebbe fuori dall'albero senza avvisi: meglio fermarsi.
const fuori = tutte.filter((r) => genitoreDi(r) !== pubblico && genitoreDi(r) !== app)
if (fuori.length > 0) {
  const nomi = fuori.map((r) => opzioni(r).path ?? opzioni(r).id).join(', ')
  throw new Error(`rotte senza un genitore noto (pubblico o app): ${nomi}`)
}

const albero = radice.addChildren([pubblico.addChildren(figliDi(pubblico)), app.addChildren(figliDi(app))])

// Voci del guscio, nell'ordine delle aree; il guscio le filtra per ruolo.
export const VOCI: VoceNav[] = AREE.flatMap((area) => area.voci)

// La cronologia si può passare: i test usano quella in memoria.
export const creaRouter = (history?: RouterHistory) =>
  createRouter({ routeTree: albero, history, context: { voci: VOCI } })
export const router = creaRouter()

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
