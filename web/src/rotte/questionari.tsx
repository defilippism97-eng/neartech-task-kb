import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Rotte della corsia «questionari» (docs/piani/fase-6-cantiere.md): questionari d3/d4 e pagine pubbliche per chi
// risponde. File della sola corsia questionari: rotte e voci del guscio si aggiungono qui, index.tsx non cambia.
// Le pagine di un'organizzazione vanno sotto `app` con percorso 'org/$codice/<vista>', le pagine senza accesso
// sotto `pubblico`; i componenti stanno in web/src/viste/questionari/.
export function rotte(_genitori: Genitori) {
  return [] as const
}

export const voci: VoceNav[] = []
