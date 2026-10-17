import { createRoute } from '@tanstack/react-router'
import { Documenti } from '../viste/Documenti'
import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Pipeline dei documenti dell'amministratore tecnico.
export function rotte({ app }: Genitori) {
  return [createRoute({ getParentRoute: () => app, path: 'org/$codice/documenti', component: Documenti })] as const
}

export const voci: VoceNav[] = [
  { to: '/app/org/$codice/documenti', etichetta: 'Documenti', icona: 'documenti', ruoli: ['amministratore_tecnico'] },
]
