import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Rotte della corsia «flusso» (docs/piani/fase-6-cantiere.md): lavori di ricalcolo, fase di verifica, storico e
// stampa delle restituzioni, reversibilità della pipeline dei documenti. File della sola corsia flusso: rotte e
// voci del guscio si aggiungono qui, index.tsx non cambia. Le pagine di un'organizzazione vanno sotto `app` con
// percorso 'org/$codice/<vista>', le pagine senza accesso sotto `pubblico`; i componenti stanno in
// web/src/viste/flusso/.
export function rotte(_genitori: Genitori) {
  return [] as const
}

export const voci: VoceNav[] = []
