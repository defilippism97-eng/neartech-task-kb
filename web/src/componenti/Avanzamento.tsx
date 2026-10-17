import type { Avanzamento as DatiAvanzamento } from '../api'

// Avanzamento della sperimentazione: quanta parte dei giudizi viene già dalle persone, voce per voce.
// Mostrato come progresso e invito all'azione, mai come blocco (registro di metodo, sezione 27).
// Compatto, nella colonna accanto alla mappa che spiega (docs/piattaforma/direzione-creativa.md).

export function Avanzamento({ dati }: { dati: DatiAvanzamento }) {
  const VOCI = Object.keys(dati.voci)  // l'ordine della rubrica, dall'API (neartech.sperimentazione.VOCI)
  const percentuale = Math.round(dati.quota * 100)
  const raggio = 26
  const circonferenza = 2 * Math.PI * raggio
  const mancanti = VOCI.filter((v) => (dati.voci[v]?.persone ?? 0) === 0)
  return (
    <section className="exp" aria-labelledby="titolo-avanzamento">
      <div className="exp-testa">
        <svg width={64} height={64} viewBox="0 0 64 64" aria-hidden="true">
          <circle cx={32} cy={32} r={raggio} fill="none" stroke="#EEF2F9" strokeWidth={8} />
          <circle cx={32} cy={32} r={raggio} fill="none" stroke="#007272" strokeWidth={8} strokeLinecap="round"
            strokeDasharray={`${(circonferenza * percentuale) / 100} ${circonferenza}`} transform="rotate(-90 32 32)" />
          <text x={32} y={37} textAnchor="middle" fill="#0B2559" fontFamily="var(--f-mono)" fontSize={14} fontWeight={600}>
            {percentuale}%
          </text>
        </svg>
        <div>
          <span className="eyebrow">Sperimentazione</span>
          <h3 id="titolo-avanzamento">
            {percentuale === 0 ? 'Tutti i giudizi sono ancora stime del modello'
              : `${percentuale} giudizi su 100 vengono dalle vostre persone`}
          </h3>
        </div>
      </div>
      <ul className="items" aria-label="Giudizi di persona per voce della rubrica">
        {VOCI.map((v) => {
          const voce = dati.voci[v] ?? { persone: 0, totale: 0 }
          const quota = voce.totale ? voce.persone / voce.totale : 0
          return (
            <li className="item" key={v}>
              <div className="bar" title={`${v}: ${voce.persone} di ${voce.totale}`}>
                <i style={{ height: `${Math.max(quota * 100, 6)}%`, background: quota === 0 ? 'rgba(245,158,11,.55)' : undefined }} />
              </div>
              <span>{v}</span>
              <span className="visually-hidden">{voce.persone} occorrenze su {voce.totale} con giudizi di persona</span>
            </li>
          )
        })}
      </ul>
      {mancanti.length > 0 && <p className="exp-mancanti">Ancora senza giudizi di persona: {mancanti.join(', ')}.</p>}
      <details className="exp-come">
        <summary>Come si aggiorna</summary>
        <p>Ogni giudizio dei revisori e ogni risposta ai questionari sostituisce una stima del modello; la mappa si
          aggiorna al calcolo successivo.</p>
      </details>
    </section>
  )
}
