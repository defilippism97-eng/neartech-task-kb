import { useQuery } from '@tanstack/react-query'
import { Link, Navigate, Outlet } from '@tanstack/react-router'
import { api, ErroreApi } from '../api'
import { Logo } from '../componenti/Logo'
import { Accesso } from './Accesso'

// Senza sessione si vede l'accesso; con la sessione, la home porta all'organizzazione dell'utente (o fa scegliere
// fra più organizzazioni, per esempio all'amministratore tecnico), dove ogni ruolo vede il percorso del pilota.

export function Radice() {
  const io = useQuery({ queryKey: ['io'], queryFn: api.io, retry: false })
  if (io.isPending) return <p className="vuoto" aria-busy="true">Verifico l'accesso…</p>
  if (io.error && (io.error as ErroreApi).stato === 401) return <Accesso />
  if (io.error) return <p className="vuoto errore" role="alert">Impossibile verificare l'accesso. Controlla la connessione e ricarica la pagina.</p>
  return <Outlet />
}

export function Home() {
  const organizzazioni = useQuery({ queryKey: ['organizzazioni'], queryFn: api.organizzazioni })
  if (organizzazioni.isPending) return <p className="vuoto" aria-busy="true">Carico le tue organizzazioni…</p>
  if (organizzazioni.error) return <p className="vuoto errore" role="alert">Impossibile caricare le organizzazioni. Ricarica la pagina.</p>
  const elenco = organizzazioni.data
  if (elenco.length === 1) {
    return <Navigate to="/org/$codice/panoramica" params={{ codice: elenco[0].codice }} replace />
  }
  return (
    <main className="scelta">
      <Logo variante="chiaro" dimensione={34} />
      {elenco.length === 0 ? (
        <>
          <h1>Nessuna organizzazione per te, per ora</h1>
          <p>Il tuo accesso funziona, ma non hai ancora un ruolo in un'organizzazione pilota. Chiedilo all'amministratore NEARTECH.</p>
        </>
      ) : (
        <>
          <h1>Scegli l'organizzazione</h1>
          <ul>
            {elenco.map((o) => (
              <li key={o.codice}>
                <Link to="/org/$codice/panoramica" params={{ codice: o.codice }} className="card scelta-voce">
                  <b>{o.nome}</b><span className="mono">{o.codice}</span>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </main>
  )
}
