import type { Avanzamento as DatiAvanzamento } from '../api'

// Avanzamento della sperimentazione: quanta parte dei giudizi viene già dalle persone, voce per voce.
// Mostrato come progresso e invito all'azione, mai come blocco (registro di metodo, sezione 27).

export function Avanzamento({ dati }: { dati: DatiAvanzamento }) {
  const VOCI = Object.keys(dati.voci)  // l'ordine della rubrica, dall'API (neartech.sperimentazione.VOCI)
  const percentuale = Math.round(dati.quota * 100)
  const circonferenza = 2 * Math.PI * 38
  const mancanti = VOCI.filter((v) => (dati.voci[v]?.persone ?? 0) === 0)
  return (
    <section className="exp" aria-labelledby="titolo-avanzamento">
      <svg width={92} height={92} viewBox="0 0 92 92" aria-hidden="true">
        <circle cx={46} cy={46} r={38} fill="none" stroke="rgba(255,255,255,.15)" strokeWidth={10} />
        <circle cx={46} cy={46} r={38} fill="none" stroke="#00B4B4" strokeWidth={10} strokeLinecap="round"
          strokeDasharray={`${(circonferenza * percentuale) / 100} ${circonferenza}`} transform="rotate(-90 46 46)" />
        <text x={46} y={51} textAnchor="middle" fill="#fff" fontFamily="var(--f-mono)" fontSize={17} fontWeight={600}>
          {percentuale}%
        </text>
      </svg>
      <div>
        <span className="eyebrow">Sperimentazione</span>
        <h2 id="titolo-avanzamento">
          {percentuale === 0 ? 'Tutti i giudizi sono ancora stime del modello'
            : `${percentuale} giudizi su 100 vengono dalle vostre persone`}
        </h2>
        <p>
          Ogni giudizio dei revisori e ogni risposta ai questionari sostituisce una stima del modello; la mappa si
          aggiorna al calcolo successivo.
          {mancanti.length > 0 && ` Ancora senza giudizi di persona: ${mancanti.join(', ')}.`}
        </p>
      </div>
      <ul className="items" aria-label="Giudizi di persona per voce della rubrica">
        {VOCI.map((v) => {
          const voce = dati.voci[v] ?? { persone: 0, totale: 0 }
          const quota = voce.totale ? voce.persone / voce.totale : 0
          return (
            <li className="item" key={v}>
              <div className="bar" title={`${v}: ${voce.persone} di ${voce.totale}`}>
                <i style={{ height: `${Math.max(quota * 100, 4)}%`, background: quota === 0 ? 'rgba(245,158,11,.55)' : undefined }} />
              </div>
              <span>{v}</span>
              <span className="visually-hidden">{voce.persone} occorrenze su {voce.totale} con giudizi di persona</span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
