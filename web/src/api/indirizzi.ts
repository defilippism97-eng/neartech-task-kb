// API degli indirizzi: questionario, profilo di pesi proposto, approvazione e verifica (neartech.api.rotte.indirizzi).
import { richiesta } from './client'
import type { Quadrante } from './tipi'

export interface Domanda {
  codice: string
  voce: 'd1' | 'd2' | 'd3' | 'd4'
  verso: 1 | -1
  testo: string
}

export interface StatoIndirizzi {
  questionario: { versione: string; risposte: string[]; domande: Domanda[]; limiti: { min: number; max: number } } | null
  pesi_in_uso: { profilo: string; pesi: Record<string, number> }
  profilo: {
    profile_id: string
    attivo: boolean
    pesi: Record<string, number>
    approvato: number | null
    verificato: number | null
    controlli: { codice: string; esito: boolean; descrizione: string }[]
    effetto: { quadranti: Record<Quadrante, number>; cambiano_quadrante: number; occorrenze: number } | null
  } | null
}

export const indirizzi = {
  indirizzi: (codice: string) => richiesta<StatoIndirizzi>(`/api/organizzazioni/${encodeURIComponent(codice)}/indirizzi`),
  rispondi: (codice: string, risposte: Record<string, number>, nota: string) =>
    richiesta<{ profile_id: string }>(`/api/organizzazioni/${encodeURIComponent(codice)}/indirizzi/risposte`,
      { method: 'POST', body: JSON.stringify({ risposte, nota }) }),
  decidiProfilo: (codice: string, profilo: string, atto: 'approvazione' | 'verifica', motivazione: string) =>
    richiesta<{ atto: number }>(
      `/api/organizzazioni/${encodeURIComponent(codice)}/indirizzi/${encodeURIComponent(profilo)}/${atto}`,
      { method: 'POST', body: JSON.stringify({ motivazione }) }),
}
