// API dei lotti di abbinamento: elenco, dettaglio e azioni del revisore (neartech.api.rotte.lotti).
import { org, richiesta } from './client'
import type { Lotto } from './tipi'

export type EsitoCampione = 'corretto' | 'parziale' | 'errato'

export interface DettaglioLotto {
  lotto: Lotto
  campione: {
    istruzioni: string
    elementi: { posizione: number; candidato: string; task: string; proposta: string; mio_esito: EsitoCampione | null }[]
    misura: { n_elementi: number; n_corretti: number; n_parziali: number; n_errati: number; precisione: number; esito: string } | null
  } | null
  proposte: { proposta_id: string; candidato: string; task_id: string | null; task_proposto: string | null; distanza: number | null; margine: number | null }[] | null
}

export const lotti = {
  lotti: (codice: string) => richiesta<Lotto[]>(`${org(codice)}/lotti`),
  lotto: (codice: string, lotto: string) => richiesta<DettaglioLotto>(`${org(codice)}/lotti/${encodeURIComponent(lotto)}`),
  azioneLotto: (codice: string, lotto: string, azione: 'livello' | 'campione' | 'giudizi' | 'misura' | 'decisione', corpo: object = {}) =>
    richiesta<unknown>(`${org(codice)}/lotti/${encodeURIComponent(lotto)}/${azione}`, { method: 'POST', body: JSON.stringify(corpo) }),
}
