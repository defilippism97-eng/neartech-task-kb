import { createRoute } from '@tanstack/react-router'
import { Lotti } from '../viste/Lotti'
import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Lotti di abbinamento del revisore.
export function rotte({ app }: Genitori) {
  return [createRoute({ getParentRoute: () => app, path: 'org/$codice/lotti', component: Lotti })] as const
}

export const voci: VoceNav[] = [
  { to: '/app/org/$codice/lotti', etichetta: 'Lotti', icona: 'lotti', ruoli: ['revisore'] },
]
