import { createRoute } from '@tanstack/react-router'
import { Home } from '../sito/Home'
import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Rotte della corsia «sito» (docs/piani/fase-6-cantiere.md): sito pubblico e candidature ai piloti. File della sola
// corsia sito. Le pagine stanno sotto `pubblico` (nessun accesso richiesto) e i loro componenti in web/src/sito/.
//
// rotte() restituisce solo le rotte di primo livello, figlie di `app` o di `pubblico`: le figlie di una propria
// rotta (schede, dettagli) si appendono a quella con addChildren e non si restituiscono, altrimenti index.tsx si
// ferma all'avvio.
// Il percorso /org è riservato: porta i vecchi indirizzi dell'applicazione sotto /app (rotte/base.tsx).
export function rotte({ pubblico }: Genitori) {
  return [createRoute({ getParentRoute: () => pubblico, path: '/', component: Home })] as const
}

// Il sito pubblico non ha voci nel guscio dell'applicazione.
export const voci: VoceNav[] = []
