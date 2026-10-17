import { createRoute } from '@tanstack/react-router'
import { Indirizzi } from '../viste/Indirizzi'
import type { Genitori } from './genitori'
import { TUTTI_I_RUOLI, type VoceNav } from './tipi'

// Indirizzi del comitato: questionario, profilo di pesi, approvazione e verifica.
export function rotte({ app }: Genitori) {
  return [createRoute({ getParentRoute: () => app, path: 'org/$codice/indirizzi', component: Indirizzi })] as const
}

export const voci: VoceNav[] = [
  { to: '/app/org/$codice/indirizzi', etichetta: 'Indirizzi', icona: 'indirizzi', ruoli: TUTTI_I_RUOLI },
]
