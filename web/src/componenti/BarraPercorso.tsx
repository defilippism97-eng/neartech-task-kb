import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import type { CSSProperties, ReactNode } from 'react'
import { api, type Percorso } from '../api'
import {
  azione, chiAgisce, concluso, ETICHETTE_STATO_FASE, indiceCorrente, progressoFase, progressoOggi, provaFase,
  sigilloFase, statoMostrato, TITOLI_FASI, type Azione, type Sigillo,
} from '../azioni'

// Il percorso del pilota come tracciato a sigilli (docs/piattaforma/direzione-creativa.md, 2026-10-17): quattro tratte
// di lavoro calcolato dal motore (neartech.percorso), separate dai sigilli, gli atti delle persone che chiudono ogni
// fase. «Oggi» sta sul fronte della fase corrente; sotto, la banda dell'azione di chi guarda, con la tacca su «oggi».
// Uguale per tutti i ruoli; cambia solo la banda.

const SPUNTA = <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="m2.5 6.2 2.3 2.3 4.7-5" fill="none"
  stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>

function Sigilli({ sigilli }: { sigilli: Sigillo[] }) {
  return (
    <span className={`sigilli${sigilli.length > 1 ? ' sigilli-doppi' : ''}`} aria-hidden="true">
      {sigilli.map((s, i) => (
        <span key={i} className={`sigillo sigillo-${s.stato}`}>{s.etichetta || (s.stato === 'posto' ? SPUNTA : null)}</span>
      ))}
    </span>
  )
}

interface Props {
  percorso: Percorso
  ruolo: string
  codice: string
  /** Comando aggiuntivo nella banda (l'approvazione della restituzione per il comitato). */
  comando?: ReactNode
}

export function BarraPercorso({ percorso, ruolo, codice, comando }: Props) {
  const client = useQueryClient()
  const ricalcolo = useMutation({
    mutationFn: () => api.ricalcola(codice),
    onSettled: () => void client.invalidateQueries(),
  })
  const finito = concluso(percorso)
  const corrente = indiceCorrente(percorso)
  const tocca: Azione = finito
    ? { titolo: 'Restituzione approvata', testo: `Atto #${percorso.fasi[3].fatti.approvazione} nel registro. Il percorso del pilota è concluso.`,
        pronta: true, attesa: true }
    : azione(ruolo, percorso)
  const attesa = !!tocca.attesa
  const eyebrow = finito ? 'Percorso concluso'
    : attesa ? `In attesa · ora agisce ${chiAgisce(percorso)}`
      : ruolo === 'comitato_guida' ? 'Tocca a voi' : 'Tocca a te'
  const stile = { '--indice': corrente, '--progresso-oggi': progressoOggi(percorso) } as CSSProperties
  const dettaglio = percorso.fasi.map((_, i) => i).filter((i) => i === corrente || statoMostrato(percorso, i) === 'anticipo')

  return (
    <section className={`percorso${finito ? ' percorso-concluso' : ''}`} aria-labelledby="titolo-percorso" style={stile}>
      <header className="percorso-testa">
        <h2 id="titolo-percorso" className="eyebrow">Percorso del pilota</h2>
        <p className="percorso-dove mono">
          {finito ? `percorso concluso · atto #${percorso.fasi[3].fatti.approvazione}`
            : `fase ${corrente + 1} di 4 · ${TITOLI_FASI[percorso.fase_corrente]}`}
        </p>
      </header>

      <ol className="tracciato">
        {percorso.fasi.map((f, i) => {
          const stato = statoMostrato(percorso, i)
          const prova = provaFase(percorso, i)
          const sigillo = sigilloFase(percorso, i)
          const eCorrente = i === corrente && !finito
          return (
            <li key={f.codice} className={`tratta tratta-${f.stato}${stato === 'anticipo' ? ' tratta-anticipo' : ''}`}
              aria-current={eCorrente ? 'step' : undefined}
              style={{ '--progresso': progressoFase(percorso, i), '--ritardo': `${i * 60}ms` } as CSSProperties}>
              {eCorrente && <span className="oggi" aria-hidden="true">oggi</span>}
              <span className="tratta-linea" aria-hidden="true"><i /></span>
              <Sigilli sigilli={sigillo.sigilli} />
              <div className="tratta-testa" aria-hidden="true">
                <span className="tratta-numero mono">{i + 1}</span>
                <b>{TITOLI_FASI[f.codice]}</b>
                <span className={`chip-fase chip-fase-${stato}`}>{ETICHETTE_STATO_FASE[stato]}</span>
              </div>
              <p className="tratta-prova" aria-hidden="true">{prova}</p>
              <p className="tratta-sigillo" aria-hidden="true">{sigillo.testo}</p>
              <span className="visually-hidden">
                Fase {i + 1} di 4, {TITOLI_FASI[f.codice]}: {stato === 'anticipo' ? 'in corso in anticipo, risultati provvisori'
                  : ETICHETTE_STATO_FASE[stato]}. {prova}. {sigillo.testo.replace(/✓ /g, 'fatto: ')}.
              </span>
            </li>
          )
        })}
      </ol>

      {/* Sul telefono: prova e sigillo della fase corrente (e di quella in anticipo), già detti dalla frase nascosta. */}
      <div className="percorso-dettaglio" aria-hidden="true">
        {dettaglio.map((i) => (
          <p key={i}><b>{TITOLI_FASI[percorso.fasi[i].codice]}</b> · {provaFase(percorso, i)}<br />
            <span className="mono">{sigilloFase(percorso, i).testo}</span></p>
        ))}
      </div>

      <div className={`percorso-azione${attesa ? ' percorso-azione-attesa' : ''}`} role="group" aria-labelledby="titolo-azione">
        <div className="azione-testo">
          <span className="eyebrow">{eyebrow}</span>
          <h3 id="titolo-azione">{tocca.titolo}</h3>
          <p>{tocca.testo}</p>
        </div>
        <div className="azione-comando">
          {!tocca.pronta && <span className="state nuovo">schermata in arrivo</span>}
          {!tocca.attesa && tocca.rotta === 'indirizzi' && (
            <Link to="/org/$codice/indirizzi" params={{ codice }} className="btn btn-pill">Apri gli indirizzi</Link>
          )}
          {!tocca.attesa && tocca.rotta === 'revisione' && (
            <Link to="/org/$codice/revisione" params={{ codice }} className="btn btn-pill">Apri la coda</Link>
          )}
          {!tocca.attesa && tocca.rotta === 'documenti' && (
            <Link to="/org/$codice/documenti" params={{ codice }} className="btn btn-pill">Apri i documenti</Link>
          )}
          {!tocca.attesa && tocca.rotta === 'lotti' && (
            <Link to="/org/$codice/lotti" params={{ codice }} className="btn btn-pill">Apri i lotti</Link>
          )}
          {tocca.comando === 'ricalcolo' && (
            <button type="button" className="btn btn-pill" disabled={ricalcolo.isPending} aria-busy={ricalcolo.isPending}
              onClick={() => ricalcolo.mutate()}>
              {ricalcolo.isPending ? 'Ricalcolo la mappa…' : 'Ricalcola la mappa'}
            </button>
          )}
          {comando}
        </div>
        {ricalcolo.error && <p className="errore" role="alert">Ricalcolo non riuscito. Riprova tra qualche istante.</p>}
      </div>

      <details className="percorso-prove">
        <summary>Le prove di tutte le fasi</summary>
        <ul>
          {percorso.fasi.map((f, i) => (
            <li key={f.codice}><b>{TITOLI_FASI[f.codice]}</b> · {ETICHETTE_STATO_FASE[statoMostrato(percorso, i)]}<br />
              {provaFase(percorso, i)} · <span className="mono">{sigilloFase(percorso, i).testo}</span></li>
          ))}
        </ul>
      </details>
    </section>
  )
}
