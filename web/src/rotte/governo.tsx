import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Rotte della corsia «governo» (docs/piani/fase-6-cantiere.md): parametri, completamento degli indirizzi, home
// dell'auditor, registro, vista del rappresentante. File della sola corsia governo: rotte e voci del guscio si
// aggiungono qui, index.tsx non cambia. Le pagine di un'organizzazione vanno sotto `app` con percorso
// 'org/$codice/<vista>', le pagine senza accesso sotto `pubblico`; i componenti stanno in web/src/viste/governo/.
export function rotte(_genitori: Genitori) {
  return [] as const
}

export const voci: VoceNav[] = []
