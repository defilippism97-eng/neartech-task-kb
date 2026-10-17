import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Rotte della corsia «revisione_lavoro» (docs/piani/fase-6-cantiere.md): lavoro del revisore: giudizi sulla
// rubrica, lotti, coda unificata, somiglianze, ritaratura. File della sola corsia revisione_lavoro: rotte e voci
// del guscio si aggiungono qui, index.tsx non cambia. Le pagine di un'organizzazione vanno sotto `app` con
// percorso 'org/$codice/<vista>', le pagine senza accesso sotto `pubblico`; i componenti stanno in
// web/src/viste/revisione_lavoro/.
//
// rotte() restituisce solo le rotte di primo livello, figlie di `app` o di `pubblico`: le figlie di una propria
// rotta (schede, dettagli) si appendono a quella con addChildren e non si restituiscono, altrimenti index.tsx si
// ferma all'avvio.
// La cartella delle viste non esiste ancora: la crea la corsia con il suo primo componente.
export function rotte(_genitori: Genitori) {
  return [] as const
}

export const voci: VoceNav[] = []
