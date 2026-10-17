// API della panoramica: restituzione e percorso, approvazione del comitato, ricalcolo (neartech.api.rotte.panoramica).
import { richiesta } from './client'
import type { Panoramica } from './tipi'

export const panoramica = {
  panoramica: (codice: string) => richiesta<Panoramica>(`/api/organizzazioni/${encodeURIComponent(codice)}/panoramica`),
  approva: (codice: string, impronta: string, motivazione: string) =>
    richiesta<{ atto: number; impronta: string }>(
      `/api/organizzazioni/${encodeURIComponent(codice)}/restituzione/approvazione`,
      { method: 'POST', body: JSON.stringify({ impronta, motivazione }) },
    ),
  ricalcola: (codice: string) =>
    richiesta<{ nuove: number }>(`/api/organizzazioni/${encodeURIComponent(codice)}/calcolo`, { method: 'POST' }),
}
