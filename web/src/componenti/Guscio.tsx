import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'
import { api } from '../api'
import { Logo } from './Logo'

// Guscio dell'applicazione per i ruoli di un'organizzazione. Le voci non ancora costruite si vedono come
// "in arrivo": la piattaforma cresce a fette (docs/piani/fase-6-piattaforma.md).

const ETICHETTE_RUOLO: Record<string, string> = {
  comitato_guida: 'Comitato guida',
  revisore: 'Revisore',
  auditor: 'Auditor',
  amministratore_tecnico: 'Amministratore tecnico',
  rappresentante_lavoratori: 'Rappresentante dei lavoratori',
}

interface Props {
  codice: string
  nomeOrganizzazione: string
  ruolo: string
  soggetto: string
  children: ReactNode
}

export function Guscio({ codice, nomeOrganizzazione, ruolo, soggetto, children }: Props) {
  const esci = async () => {
    try {
      await api.esci()
    } finally {
      window.location.assign('/')  // anche se la rete non risponde, si torna all'accesso
    }
  }
  return (
    <div className="app">
      <aside className="side">
        <Logo variante="navy" />
        <div className="org"><b>{nomeOrganizzazione}</b><span>pilota · sperimentazione</span></div>
        <nav aria-label="Sezioni">
          <ul className="nav">
            <li><Link to="/org/$codice/panoramica" params={{ codice }} activeProps={{ 'aria-current': 'page' }}>Panoramica</Link></li>
            {['Indirizzi', 'Ruoli e task', 'Questionari', 'Parametri e soglie', 'Registro'].map((voce) => (
              <li key={voce}><span aria-disabled="true">{voce} <small>in arrivo</small></span></li>
            ))}
          </ul>
        </nav>
        <div className="who">
          <b>{ETICHETTE_RUOLO[ruolo] ?? ruolo}</b>
          <span className="mono">{soggetto}</span>
          <br />
          <button type="button" onClick={esci}>Esci</button>
        </div>
      </aside>
      <main className="main" id="contenuto">{children}</main>
    </div>
  )
}
