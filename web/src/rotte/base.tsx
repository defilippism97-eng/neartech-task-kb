import { createRoute } from '@tanstack/react-router'
import { Home } from '../viste/Radice'
import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Home dell'applicazione (/app): porta all'organizzazione dell'utente o fa scegliere fra più organizzazioni.
export function rotte({ app }: Genitori) {
  return [createRoute({ getParentRoute: () => app, path: '/', component: Home })] as const
}

export const voci: VoceNav[] = []
