import { createRootRoute, createRoute, createRouter, type RouterHistory } from '@tanstack/react-router'
import { Indirizzi } from './viste/Indirizzi'
import { Panoramica } from './viste/Panoramica'
import { Home, Radice } from './viste/Radice'

// Rotte per ruolo. Ogni fetta della fase 6 aggiunge le sue (docs/piani/fase-6-piattaforma.md).

const radice = createRootRoute({ component: Radice })
const home = createRoute({ getParentRoute: () => radice, path: '/', component: Home })
const panoramica = createRoute({ getParentRoute: () => radice, path: '/org/$codice/panoramica', component: Panoramica })
const indirizzi = createRoute({ getParentRoute: () => radice, path: '/org/$codice/indirizzi', component: Indirizzi })
const albero = radice.addChildren([home, panoramica, indirizzi])

// La cronologia si può passare: i test usano quella in memoria.
export const creaRouter = (history?: RouterHistory) => createRouter({ routeTree: albero, history })
export const router = creaRouter()

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
