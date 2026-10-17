import { createRoute } from '@tanstack/react-router'
import { Revisione } from '../viste/Revisione'
import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Coda del revisore sulla rubrica.
export function rotte({ app }: Genitori) {
  return [createRoute({ getParentRoute: () => app, path: 'org/$codice/revisione', component: Revisione })] as const
}

export const voci: VoceNav[] = [
  { to: '/app/org/$codice/revisione', etichetta: 'Revisione', icona: 'revisione', ruoli: ['revisore'] },
]
