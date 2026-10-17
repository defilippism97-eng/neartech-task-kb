import { useQuery } from '@tanstack/react-query'
import { Navigate, Outlet } from '@tanstack/react-router'
import { api, ErroreApi } from '../api'
import { Accesso } from './Accesso'

// Senza sessione si vede l'accesso; con la sessione, la home porta alla vista del proprio ruolo.

export function Radice() {
  const io = useQuery({ queryKey: ['io'], queryFn: api.io, retry: false })
  if (io.isPending) return <p className="vuoto" aria-busy="true">Verifico l'accesso…</p>
  if (io.error && (io.error as ErroreApi).stato === 401) return <Accesso />
  if (io.error) return <p className="vuoto errore" role="alert">Impossibile verificare l'accesso. Controlla la connessione e ricarica la pagina.</p>
  return <Outlet />
}

export function Home() {
  const io = useQuery({ queryKey: ['io'], queryFn: api.io })
  const comitato = io.data?.ruoli.find((r) => r.ruolo === 'comitato_guida' && r.codice)
  const destinazione = comitato ?? io.data?.ruoli.find((r) => r.codice)
  if (destinazione?.codice) {
    return <Navigate to="/org/$codice/panoramica" params={{ codice: destinazione.codice }} replace />
  }
  return (
    <div className="vuoto">
      <h2>La vista per il tuo ruolo non è ancora attiva</h2>
      <p>In questa fase della sperimentazione è attiva la mappa del comitato guida. Le viste del revisore e
        dell'auditor arrivano con i prossimi rilasci.</p>
    </div>
  )
}
