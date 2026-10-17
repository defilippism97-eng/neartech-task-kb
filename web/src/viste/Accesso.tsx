import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api, ErroreApi } from '../api'

// Accesso: SSO aziendale; in sviluppo (solo da localhost) anche indicando un soggetto esistente.
export function Accesso() {
  const ambiente = useQuery({ queryKey: ['ambiente'], queryFn: api.ambiente })
  const [soggetto, setSoggetto] = useState('')
  const [errore, setErrore] = useState<string | null>(
    new URLSearchParams(window.location.search).get('accesso') === 'non-riuscito'
      ? 'Accesso non riuscito: il tuo account non è abilitato a Neartech o l\'accesso è stato annullato. Contatta l\'amministratore NEARTECH.'
      : null,
  )
  const entraInSviluppo = async (evento: React.FormEvent) => {
    evento.preventDefault()
    if (!soggetto.trim()) return
    try {
      await api.entraSviluppo(soggetto.trim())
      window.location.assign('/')
    } catch (e) {
      setErrore((e as ErroreApi).stato === 403 ? 'Soggetto non abilitato alla piattaforma.' : 'Accesso non riuscito. Riprova.')
    }
  }
  return (
    <div className="accesso">
      <div className="blob" aria-hidden="true" />
      <main className="card">
        <div className="brand" style={{ color: 'var(--navy)' }}><div className="mark" aria-hidden="true" />neartech</div>
        <h1>Accedi alla tua organizzazione</h1>
        <p>Usa l'account aziendale: Neartech riconosce il tuo ruolo e ti porta direttamente al lavoro che ti spetta.</p>
        {errore && <p className="errore" role="alert">{errore}</p>}
        {ambiente.data?.sso && (
          <a className="btn btn-pill" href="/accesso/entra" style={{ marginTop: 22, justifyContent: 'center', width: '100%' }}>
            Accedi con l'account aziendale
          </a>
        )}
        {ambiente.data?.accesso_sviluppo && (
          <form onSubmit={entraInSviluppo}>
            <label htmlFor="soggetto" className="mono" style={{ fontSize: 11, color: 'var(--stone-ink)' }}>
              SVILUPPO · SOGGETTO SSO DI PROVA
            </label>
            <input id="soggetto" name="soggetto" value={soggetto} onChange={(e) => setSoggetto(e.target.value)}
              placeholder="es. prova|comitato" autoComplete="off" />
            <button type="submit" className="btn btn-secondary">Entra in sviluppo</button>
          </form>
        )}
        <p className="mono" style={{ fontSize: 11, marginTop: 22 }}>Dati ospitati in UE · nessuna valutazione di singole persone</p>
      </main>
    </div>
  )
}
