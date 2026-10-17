// API della pipeline dei documenti: mansionari, scomposizione, proposta degli abbinamenti, applicazione dei lotti
// (neartech.api.rotte.documenti).
import { org, richiesta } from './client'
import type { Lotto, StatoDocumento, Stima } from './tipi'

export interface Pipeline {
  prezzi: { parametro_id: string; versione: number; modello: string; ingresso_eur_mtok: number; uscita_eur_mtok: number } | null
  documenti: {
    caricamento_id: string
    nome_file: string
    ruolo: string
    caratteri: number
    caricato_il: string
    stato: StatoDocumento
    errore: string | null
    candidati: number
    stima: Stima | null
  }[]
  stima_da_avviare: Stima | null
  candidati_da_proporre: number
  proposta_in_coda: boolean
  lotti: Lotto[]
  lavori: { job_id: string; tipo: string; stato: StatoDocumento; tentativi: number; errore: string | null; creato_il: string }[]
}

export const documenti = {
  documenti: (codice: string) => richiesta<Pipeline>(`${org(codice)}/documenti`),
  caricaDocumento: (codice: string, nome_file: string, contenuto: string) =>
    richiesta<{ caricamento_id: string; nuovo: boolean; ruolo: string }>(`${org(codice)}/documenti`,
      { method: 'POST', body: JSON.stringify({ nome_file, contenuto }) }),
  avviaScomposizione: (codice: string, caricamenti: string[], motivazione: string) =>
    richiesta<{ atto: number } & Stima>(`${org(codice)}/documenti/scomposizione`,
      { method: 'POST', body: JSON.stringify({ caricamenti, motivazione }) }),
  proponiLotto: (codice: string, motivazione: string) =>
    richiesta<{ atto: number }>(`${org(codice)}/abbinamenti/proposta`, { method: 'POST', body: JSON.stringify({ motivazione }) }),
  applicaLotto: (codice: string, lotto: string, motivazione: string) =>
    richiesta<{ atto: number }>(`${org(codice)}/lotti/${encodeURIComponent(lotto)}/applicazione`,
      { method: 'POST', body: JSON.stringify({ motivazione }) }),
}
