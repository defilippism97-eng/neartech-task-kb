import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'
import { api } from '../api'
import { ETICHETTE_RUOLO } from '../azioni'
import { Icona, type NomeIcona } from './Icona'
import { Logo } from './Logo'

// Guscio dell'applicazione per i ruoli di un'organizzazione. Le voci non ancora costruite si vedono come
// "in arrivo": la piattaforma cresce a fette (docs/piani/fase-6-piattaforma.md).

type Rotta = '/org/$codice/panoramica' | '/org/$codice/indirizzi' | '/org/$codice/revisione' | '/org/$codice/lotti'
  | '/org/$codice/documenti'

const PER_RUOLO: Record<string, [Rotta, string, NomeIcona][]> = {
  revisore: [['/org/$codice/revisione', 'Revisione', 'revisione'], ['/org/$codice/lotti', 'Lotti', 'lotti']],
  amministratore_tecnico: [['/org/$codice/documenti', 'Documenti', 'documenti']],
}

const IN_ARRIVO: [string, NomeIcona][] = [
  ['Ruoli e task', 'ruoli'], ['Questionari', 'questionari'], ['Parametri e soglie', 'parametri'], ['Registro', 'registro'],
]

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
  const voci: [Rotta, string, NomeIcona][] = [
    ['/org/$codice/panoramica', 'Panoramica', 'panoramica'], ['/org/$codice/indirizzi', 'Indirizzi', 'indirizzi'],
    ...(PER_RUOLO[ruolo] ?? []),
  ]
  return (
    <div className="app">
      <aside className="side">
        <Logo variante="chiaro" />
        <div className="org"><b>{nomeOrganizzazione}</b><span>pilota · sperimentazione</span></div>
        <nav aria-label="Sezioni">
          <span className="nav-gruppo">Lavoro</span>
          <ul className="nav">
            {voci.map(([to, etichetta, icona]) => (
              <li key={to}>
                <Link to={to} params={{ codice }} className="voce" activeProps={{ 'aria-current': 'page' }}>
                  <Icona nome={icona} /> {etichetta}
                </Link>
              </li>
            ))}
          </ul>
          <span className="nav-gruppo">In arrivo</span>
          <ul className="nav">
            {IN_ARRIVO.map(([voce, icona]) => (
              <li key={voce}><span className="voce voce-off" aria-disabled="true"><Icona nome={icona} /> {voce}</span></li>
            ))}
          </ul>
        </nav>
        <div className="who">
          <span className="who-iniziale" aria-hidden="true">{(ETICHETTE_RUOLO[ruolo] ?? ruolo).charAt(0)}</span>
          <span className="who-testo">
            <b>{ETICHETTE_RUOLO[ruolo] ?? ruolo}</b>
            <span className="mono">{soggetto}</span>
          </span>
          <button type="button" onClick={esci} aria-label="Esci"><Icona nome="esci" /></button>
        </div>
      </aside>
      <main className="main" id="contenuto"><div className="main-contenuto">{children}</div></main>
    </div>
  )
}
