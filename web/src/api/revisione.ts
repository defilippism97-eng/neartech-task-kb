// API della revisione: coda del revisore e giudizi sulla rubrica (neartech.api.rotte.revisione).
import { richiesta } from './client'

export interface VoceRubrica {
  codice: string
  nome: string
  asse: 'N' | 'D'
  livelli: string[]
}

export interface Revisione {
  rubrica: { versione: string; voci: VoceRubrica[] }
  coda: {
    task_id: string
    task: string
    ruoli: string | null
    certezza: number
    stime_modello: Record<string, number>
    miei_giudizi: Record<string, number>
    voci_con_giudizi_di_persona: string[]
  }[]
}

export const revisione = {
  revisione: (codice: string) => richiesta<Revisione>(`/api/organizzazioni/${encodeURIComponent(codice)}/revisione`),
  giudica: (codice: string, task_id: string, voce: string, valore: number, nota: string) =>
    richiesta<{ atto: number }>(`/api/organizzazioni/${encodeURIComponent(codice)}/revisione/giudizi`,
      { method: 'POST', body: JSON.stringify({ task_id, voce, valore, nota }) }),
}
