import { createRoute } from '@tanstack/react-router'
import { Panoramica } from '../viste/Panoramica'
import type { Genitori } from './genitori'
import { TUTTI_I_RUOLI, type VoceNav } from './tipi'

// Panoramica dell'organizzazione: mappa, percorso del pilota, approvazione della restituzione.
export function rotte({ app }: Genitori) {
  return [createRoute({ getParentRoute: () => app, path: 'org/$codice/panoramica', component: Panoramica })] as const
}

export const voci: VoceNav[] = [
  { to: '/app/org/$codice/panoramica', etichetta: 'Panoramica', icona: 'panoramica', ruoli: TUTTI_I_RUOLI },
]
