import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { api, type Percorso } from '../api'
import { azione, SOTTOTITOLI_FASI, TITOLI_FASI } from '../azioni'

// Barra del percorso del pilota, uguale per tutti i ruoli: le quattro fasi calcolate dal motore
// (neartech.percorso) e, accanto, che cosa tocca a chi guarda, con il collegamento all'azione.

const STATO = { fatta: 'fatta', in_corso: 'in corso', da_fare: 'da fare' } as const

export function BarraPercorso({ percorso, ruolo, codice }: { percorso: Percorso; ruolo: string; codice: string }) {
  const tocca = azione(ruolo, percorso)
  const client = useQueryClient()
  const ricalcolo = useMutation({
    mutationFn: () => api.ricalcola(codice),
    onSettled: () => void client.invalidateQueries(),
  })
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
        {tocca.rotta === 'indirizzi' && !tocca.attesa && (
          <Link to="/org/$codice/indirizzi" params={{ codice }} className="btn btn-pill">Apri gli indirizzi</Link>
        )}
        {tocca.rotta === 'revisione' && !tocca.attesa && (
          <Link to="/org/$codice/revisione" params={{ codice }} className="btn btn-pill">Apri la coda</Link>
        )}
        {tocca.comando === 'ricalcolo' && (
          <button type="button" className="btn btn-pill" disabled={ricalcolo.isPending} onClick={() => ricalcolo.mutate()}>
            {ricalcolo.isPending ? 'Ricalcolo la mappa…' : 'Ricalcola la mappa'}
          </button>
        )}
        {ricalcolo.error && <p className="errore" role="alert">Ricalcolo non riuscito. Riprova tra qualche istante.</p>}
      </div>
    </section>
  )
}
