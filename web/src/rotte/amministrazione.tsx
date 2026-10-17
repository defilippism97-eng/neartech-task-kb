import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Rotte della corsia «amministrazione» (docs/piani/fase-6-cantiere.md): account, credenziali, utenti, ruoli,
// organizzazioni e console di amministrazione. File della sola corsia amministrazione: rotte e voci del guscio si
// aggiungono qui, index.tsx non cambia. Le pagine di un'organizzazione vanno sotto `app` con percorso
// 'org/$codice/<vista>', le pagine senza accesso sotto `pubblico`; i componenti stanno in
// web/src/viste/amministrazione/.
//
// rotte() restituisce solo le rotte di primo livello, figlie di `app` o di `pubblico`: le figlie di una propria
// rotta (schede, dettagli) si appendono a quella con addChildren e non si restituiscono, altrimenti index.tsx si
// ferma all'avvio.
// La cartella delle viste non esiste ancora: la crea la corsia con il suo primo componente.
export function rotte(_genitori: Genitori) {
  return [] as const
}

export const voci: VoceNav[] = []
