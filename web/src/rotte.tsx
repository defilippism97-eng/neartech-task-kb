import { createRootRoute, createRoute, createRouter, type RouterHistory } from '@tanstack/react-router'
import { Documenti } from './viste/Documenti'
import { Indirizzi } from './viste/Indirizzi'
import { Lotti } from './viste/Lotti'
import { Panoramica } from './viste/Panoramica'
import { Revisione } from './viste/Revisione'
import { Home, Radice } from './viste/Radice'

// Rotte per ruolo. Ogni fetta della fase 6 aggiunge le sue (docs/piani/fase-6-piattaforma.md).

const radice = createRootRoute({ component: Radice })
const home = createRoute({ getParentRoute: () => radice, path: '/', component: Home })
const panoramica = createRoute({ getParentRoute: () => radice, path: '/org/$codice/panoramica', component: Panoramica })
const indirizzi = createRoute({ getParentRoute: () => radice, path: '/org/$codice/indirizzi', component: Indirizzi })
const revisione = createRoute({ getParentRoute: () => radice, path: '/org/$codice/revisione', component: Revisione })
const documenti = createRoute({ getParentRoute: () => radice, path: '/org/$codice/documenti', component: Documenti })
const lotti = createRoute({ getParentRoute: () => radice, path: '/org/$codice/lotti', component: Lotti })
const albero = radice.addChildren([home, panoramica, indirizzi, revisione, documenti, lotti])

// La cronologia si può passare: i test usano quella in memoria.
export const creaRouter = (history?: RouterHistory) => createRouter({ routeTree: albero, history })
export const router = creaRouter()

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
