import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '@fontsource/jetbrains-mono/500.css'
import '@fontsource/jetbrains-mono/600.css'
import './stile.css'
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from '@tanstack/react-router'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ErroreApi, riprova } from './api'
import { router } from './rotte'

// Caratteri serviti dalla piattaforma stessa: nessuna richiesta a servizi esterni (CSP 'self').
// Una sessione scaduta (401) su qualunque altra richiesta rifà la verifica dell'accesso, che riporta alla pagina
// di accesso. Una 401 della verifica stessa non la ripete: sarebbe un ciclo.
const tornaAllAccesso = (errore: unknown) => {
  if (errore instanceof ErroreApi && errore.stato === 401) void client.resetQueries({ queryKey: ['io'] })
}
const client: QueryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (errore, interrogazione) => { if (interrogazione.queryKey[0] !== 'io') tornaAllAccesso(errore) },
  }),
  mutationCache: new MutationCache({ onError: tornaAllAccesso }),
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false, retry: riprova } },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
)
