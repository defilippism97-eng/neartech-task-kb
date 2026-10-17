import { scaleLinear } from 'd3-scale'
import { useState } from 'react'
import type { Occorrenza, Quadrante } from '../api'

// Mappa delle occorrenze su N (orizzontale) e D (verticale). Le soglie dei quadranti vengono dal profilo di pesi
// approvato (chiavi.soglie_quadranti), mai dal codice. Il riempimento verde cresce con le voci giudicate da
// persone (su 8); il punto vuoto ambra è solo stima del modello; l'anello tratteggiato segna un risultato incerto.
// Al passaggio o al tocco: task, ruolo, valori e l'ellisse di una deviazione standard. Sotto la mappa, la stessa
// informazione in tabella, per tastiera e lettori di schermo.

const ETICHETTE: Record<Quadrante, string> = {
  q1: 'Q1 · persona necessaria e desiderata',
  q2: 'Q2 · necessaria, poco desiderata',
  q3: 'Q3 · scelta di valore',
  q4: 'Q4 · automazione possibile',
}
const QUADRANTI: Quadrante[] = ['q1', 'q2', 'q3', 'q4']
export const VOCI_TOTALI = 8

interface Props {
  occorrenze: Occorrenza[]
  thetaN: number
  thetaD: number
  /** Voci con giudizi di persona per occorrenza (assenti = nessuna). */
  giudicate: Record<string, number>
  larghezza?: number
  altezza?: number
}

export function MappaQuadranti({ occorrenze, thetaN, thetaD, giudicate, larghezza = 640, altezza = 430 }: Props) {
  const [attivo, setAttivo] = useState<Occorrenza | null>(null)
  const [fissato, setFissato] = useState<Occorrenza | null>(null)
  const mostrato = fissato ?? attivo
  const margine = 36
  const x = scaleLinear().domain([0, 1]).range([margine, larghezza - margine])
  const y = scaleLinear().domain([0, 1]).range([altezza - margine, margine])
  const unita = x(1) - x(0)
  const zone: [Quadrante, number, number, number, number, string][] = [
    ['q3', 0, thetaD, thetaN, 1, 'var(--q3)'],
    ['q1', thetaN, thetaD, 1, 1, 'var(--q1)'],
    ['q4', 0, 0, thetaN, thetaD, 'var(--q4)'],
    ['q2', thetaN, 0, 1, thetaD, 'var(--q2)'],
  ]
  const conteggi: Record<string, number> = {}
  for (const o of occorrenze) conteggi[o.quadrante] = (conteggi[o.quadrante] ?? 0) + 1
  const descrizione = `Mappa di ${occorrenze.length} occorrenze: ` +
    QUADRANTI.map((q) => `${ETICHETTE[q]} ${conteggi[q] ?? 0}`).join('; ') + '. Dettaglio nella tabella sotto la mappa.'

  return (
    <div className="mappa">
      <svg viewBox={`0 0 ${larghezza} ${altezza}`} role="img" aria-label={descrizione} onClick={() => setFissato(null)}>
        <defs>
          {/* Rilievo leggero delle zone: un'ombra navy morbida, come le superfici della piattaforma. */}
          <filter id="rilievo-zona" x="-10%" y="-10%" width="120%" height="125%">
            <feDropShadow dx="0" dy="3" stdDeviation="4" floodColor="#0B2559" floodOpacity="0.10" />
          </filter>
        </defs>
        {zone.map(([q, x0, y0, x1, y1, colore]) => {
          const scarto = 3  // le zone si staccano tra loro: quattro tessere, non una griglia piatta
          const sx = x(x0) + scarto, sy = y(y1) + scarto
          const larga = x(x1) - x(x0) - 2 * scarto, alta = y(y0) - y(y1) - 2 * scarto
          return (
            <g key={q}>
              <rect x={sx} y={sy} width={larga} height={alta} fill={colore} rx={14} stroke="#fff" strokeWidth={1.5}
                filter="url(#rilievo-zona)" />
              <text x={sx + 12} y={sy + 22} fontFamily="var(--f-mono)" fontSize={10.5} fontWeight={600} fill="#526175">
                {ETICHETTE[q]}
              </text>
              <text x={sx + larga - 12} y={sy + 26} textAnchor="end" fontFamily="var(--f-ui)" fontSize={20} fontWeight={600}
                fill="#0B2559" fillOpacity={0.8} aria-hidden="true">{conteggi[q] ?? 0}</text>
            </g>
          )
        })}
        <line x1={x(thetaN)} y1={y(0)} x2={x(thetaN)} y2={y(1)} stroke="#0B2559" strokeDasharray="4 4" strokeOpacity={0.35} />
        <line x1={x(0)} y1={y(thetaD)} x2={x(1)} y2={y(thetaD)} stroke="#0B2559" strokeDasharray="4 4" strokeOpacity={0.35} />
        <text x={x(1)} y={altezza - 8} textAnchor="end" fontFamily="var(--f-mono)" fontSize={11} fill="#526175">N necessità →</text>
        <text x={12} y={margine - 12} fontFamily="var(--f-mono)" fontSize={11} fill="#526175">↑ D desiderabilità</text>
        {mostrato && (
          <ellipse cx={x(mostrato.n)} cy={y(mostrato.d)} rx={Math.max(4, mostrato.n_dev * unita)} ry={Math.max(4, mostrato.d_dev * unita)}
            fill="#1B499F" fillOpacity={0.12} stroke="#1B499F" strokeOpacity={0.4} />
        )}
        {occorrenze.filter((o) => o.instabile).map((o) => (
          <circle key={`i-${o.occorrenza_id}`} cx={x(o.n)} cy={y(o.d)} r={9} fill="none" stroke="#92400E"
            strokeWidth={1.2} strokeDasharray="2 2" />
        ))}
        {occorrenze.map((o) => {
          const voci = giudicate[o.occorrenza_id] ?? 0
          return (
            <circle key={o.occorrenza_id} className="punto" cx={x(o.n)} cy={y(o.d)} r={mostrato === o ? 6 : 4.5}
              fill={voci > 0 ? '#10B981' : '#fff'} fillOpacity={voci > 0 ? 0.25 + (0.75 * voci) / VOCI_TOTALI : 1}
              stroke={voci > 0 ? '#065F46' : '#F59E0B'} strokeWidth={voci > 0 ? 1 : 1.8}
              onPointerEnter={() => setAttivo(o)} onPointerLeave={() => setAttivo(null)}
              onClick={(e) => { e.stopPropagation(); setFissato(fissato === o ? null : o) }} />
          )
        })}
      </svg>
      {mostrato && (
        <div className="suggerimento" style={{ left: `${(x(mostrato.n) / larghezza) * 100}%`, top: `${(y(mostrato.d) / altezza) * 100}%` }}>
          <b>{mostrato.task}</b>
          {mostrato.ruolo}
          <br />
          <span>
            N {mostrato.n.toFixed(2)} · D {mostrato.d.toFixed(2)} · {mostrato.quadrante.toUpperCase()} {Math.round(mostrato.probabilita * 100)}%
            <br />giudizi di persona: {giudicate[mostrato.occorrenza_id] ?? 0}/{VOCI_TOTALI} voci
          </span>
        </div>
      )}
      <details className="tabella-mappa">
        <summary>Vedi i task in tabella</summary>
        <div className="ruoli-tabella">
          <table>
            <thead><tr><th>Task</th><th>Ruolo</th><th>Quadrante</th><th>Probabilità</th><th>N</th><th>D</th><th>Giudizi di persona</th></tr></thead>
            <tbody>
              {occorrenze.map((o) => (
                <tr key={o.occorrenza_id}>
                  <td>{o.task}</td><td>{o.ruolo}</td><td className="mono">{o.quadrante.toUpperCase()}{o.instabile ? ' · incerto' : ''}</td>
                  <td className="mono">{Math.round(o.probabilita * 100)}%</td>
                  <td className="mono">{o.n.toFixed(2)}</td><td className="mono">{o.d.toFixed(2)}</td>
                  <td className="mono">{giudicate[o.occorrenza_id] ?? 0}/{VOCI_TOTALI}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  )
}
