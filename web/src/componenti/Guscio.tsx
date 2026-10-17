import { Link, rootRouteId, useRouteContext } from '@tanstack/react-router'
import { Fragment, type ReactNode } from 'react'
import { api } from '../api'
import { ETICHETTE_RUOLO } from '../azioni'
import { GRUPPO_LAVORO, type VoceNav } from '../rotte/tipi'
import { Icona } from './Icona'
import { Logo } from './Logo'

// Guscio dell'applicazione per i ruoli di un'organizzazione. Le voci arrivano dal registro delle aree
// (web/src/rotte, `voci` di ogni file), tramite il contesto del router: si vedono solo quelle del ruolo corrente,
// raggruppate per gruppo nell'ordine in cui compaiono.

interface Props {
  codice: string
  nomeOrganizzazione: string
  ruolo: string
  soggetto: string
  children: ReactNode
}

function perGruppo(voci: VoceNav[]): [string, VoceNav[]][] {
  const gruppi = new Map<string, VoceNav[]>()
  for (const voce of voci) {
    const gruppo = voce.gruppo ?? GRUPPO_LAVORO
    gruppi.set(gruppo, [...(gruppi.get(gruppo) ?? []), voce])
  }
  return [...gruppi.entries()]
}

export function Guscio({ codice, nomeOrganizzazione, ruolo, soggetto, children }: Props) {
  const registro = useRouteContext({ from: rootRouteId, select: (contesto) => contesto.voci })
  const esci = async () => {
    try {
      await api.esci()
    } finally {
      window.location.assign('/app')  // anche se la rete non risponde, si torna all'accesso
    }
  }
  const gruppi = perGruppo(registro.filter((voce) => voce.ruoli.includes(ruolo)))
  return (
    <div className="app">
      <aside className="side">
        <Logo variante="chiaro" />
        <div className="org"><b>{nomeOrganizzazione}</b><span>pilota · sperimentazione</span></div>
        <nav aria-label="Sezioni">
          {gruppi.map(([gruppo, voci]) => (
            <Fragment key={gruppo}>
              <span className="nav-gruppo">{gruppo}</span>
              <ul className="nav">
                {voci.map((voce) => (
                  <li key={voce.to}>
                    <Link to={voce.to} params={{ codice }} className="voce" activeProps={{ 'aria-current': 'page' }}>
                      <Icona nome={voce.icona} /> {voce.etichetta}
                    </Link>
                  </li>
                ))}
              </ul>
            </Fragment>
          ))}
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
