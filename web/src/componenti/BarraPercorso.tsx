import type { Percorso } from '../api'
import { azione, SOTTOTITOLI_FASI, TITOLI_FASI } from '../azioni'

// Barra del percorso del pilota, uguale per tutti i ruoli: le quattro fasi calcolate dal motore
// (neartech.percorso) e, accanto, che cosa tocca a chi guarda.

const STATO = { fatta: 'fatta', in_corso: 'in corso', da_fare: 'da fare' } as const

export function BarraPercorso({ percorso, ruolo }: { percorso: Percorso; ruolo: string }) {
  const tocca = azione(ruolo, percorso)
  return (
    <section className="percorso" aria-labelledby="titolo-percorso">
      <h2 id="titolo-percorso" className="visually-hidden">Percorso del pilota</h2>
      <ol className="fasi">
        {percorso.fasi.map((f, i) => (
          <li key={f.codice} className={`fase fase-${f.stato}`}
            aria-current={percorso.fase_corrente === f.codice ? 'step' : undefined}>
            <span className="fase-segno" aria-hidden="true">{f.stato === 'fatta' ? '✓' : i + 1}</span>
            <span className="fase-testo">
              <b>{TITOLI_FASI[f.codice]}</b>
              <small>{SOTTOTITOLI_FASI[f.codice]}</small>
              <span className="fase-stato">{STATO[f.stato]}</span>
            </span>
          </li>
        ))}
      </ol>
      <div className={`tocca ${tocca.attesa ? 'tocca-attesa' : ''}`}>
        <span className="eyebrow">{tocca.attesa ? 'Per te, ora' : 'Tocca a te'}</span>
        <h3>{tocca.titolo}</h3>
        <p>{tocca.testo}</p>
        {!tocca.pronta && <span className="state nuovo">schermata in arrivo</span>}
      </div>
    </section>
  )
}
