import { createRoute } from '@tanstack/react-router'
import { Home } from '../sito/Home'
import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Rotte della corsia «sito» (docs/piani/fase-6-cantiere.md): sito pubblico e candidature ai piloti. File della sola
// corsia sito. Le pagine stanno sotto `pubblico` (nessun accesso richiesto) e i loro componenti in web/src/sito/.
export function rotte({ pubblico }: Genitori) {
  return [createRoute({ getParentRoute: () => pubblico, path: '/', component: Home })] as const
}

// Il sito pubblico non ha voci nel guscio dell'applicazione.
export const voci: VoceNav[] = []
