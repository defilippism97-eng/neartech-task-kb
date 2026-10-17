import { createRoute, redirect } from '@tanstack/react-router'
import { Home } from '../viste/Radice'
import type { Genitori } from './genitori'
import type { VoceNav } from './tipi'

// Home dell'applicazione (/app): porta all'organizzazione dell'utente o fa scegliere fra più organizzazioni.
//
// Indirizzi di prima del cantiere: le pagine di un'organizzazione stavano in /org/$codice/<vista>. Segnalibri e
// collegamenti già condivisi portano alla stessa pagina sotto /app, con la stessa ricerca e lo stesso frammento
// (il percorso resta sempre interno: si aggiunge solo il prefisso). Il percorso /org del sito pubblico è riservato
// a questo reindirizzamento.
export function rotte({ app, pubblico }: Genitori) {
  return [
    createRoute({ getParentRoute: () => app, path: '/', component: Home }),
    createRoute({
      getParentRoute: () => pubblico,
      path: 'org/$',
      beforeLoad: ({ location }) => {
        throw redirect({ href: `/app${location.href}`, replace: true })
      },
    }),
  ] as const
}

export const voci: VoceNav[] = []
