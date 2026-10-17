import { createRootRouteWithContext, createRoute } from '@tanstack/react-router'
import { LayoutPubblico } from '../sito/Layout'
import { Radice } from '../viste/Radice'
import type { VoceNav } from './tipi'

// Rotte genitrici, a cui le aree appendono le proprie (vedi index.tsx). Nessuna area le modifica.
//
// - pubblico: il sito pubblico, alla radice e negli altri percorsi pubblici; non chiede l'accesso (corsia sito, e
//   le pagine pubbliche per chi risponde ai questionari).
// - app: l'applicazione autenticata sotto /app; Radice verifica l'accesso e mostra la pagina di accesso a chi non
//   ha una sessione. Le pagine di un'organizzazione stanno in /app/org/$codice/<vista>.

// Il contesto del router porta le voci di navigazione di tutte le aree al guscio (componenti/Guscio.tsx).
export interface ContestoRotte {
  voci: VoceNav[]
}

export const radice = createRootRouteWithContext<ContestoRotte>()()

export const pubblico = createRoute({ getParentRoute: () => radice, id: 'pubblico', component: LayoutPubblico })

export const app = createRoute({ getParentRoute: () => radice, path: '/app', component: Radice })

export const genitori = { pubblico, app }
export type Genitori = typeof genitori
