import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from '@tanstack/react-router'
import { useState } from 'react'
import { api, ErroreApi, type Revisione as DatiRevisione } from '../api'
import { Guscio } from '../componenti/Guscio'

// Revisore (fetta 4 della fase 6): coda dei task dal risultato meno certo e valutazione sulla rubrica corrente.
// Ogni livello scelto è un giudizio di persona con il suo atto: sostituisce la stima del modello al ricalcolo.

function messaggio(errore: unknown): string {
  const e = errore as ErroreApi
  if (e?.stato === 403) return 'Solo i revisori di questa organizzazione possono valutare i task.'
  return 'Giudizio non registrato. Controlla la connessione e riprova.'
}

function Task({ codice, dati, indice }: { codice: string; dati: DatiRevisione; indice: number }) {
  const t = dati.coda[indice]
  const [nota, setNota] = useState('')
  const client = useQueryClient()
  const giudica = useMutation({
    mutationFn: ({ voce, valore }: { voce: string; valore: number }) => api.giudica(codice, t.task_id, voce, valore, nota.trim()),
    onSuccess: () => void client.invalidateQueries({ queryKey: ['revisione', codice] }),
  })
  return (
    <section className="card" aria-labelledby="titolo-task">
      <span className="eyebrow">{t.ruoli ?? 'task'} · certezza {Math.round(t.certezza * 100)}%</span>
      <h2 id="titolo-task" style={{ margin: '6px 0 4px' }}>{t.task}</h2>
      <p style={{ fontSize: 13, marginBottom: 12 }}>Scegli il livello di ogni voce. La stima del modello è tratteggiata; il tuo
        giudizio la sostituisce al prossimo ricalcolo. Se cambi idea, scegli di nuovo: resta lo storico.</p>
      <label htmlFor="nota-giudizio" style={{ fontWeight: 600, fontSize: 13 }}>Nota per i prossimi giudizi (facoltativa)</label>
      <textarea id="nota-giudizio" className="nota-breve" maxLength={4000} value={nota} onChange={(e) => setNota(e.target.value)}
        placeholder="Es.: nel nostro contesto il colloquio è di routine" />
      {giudica.error && <p className="errore" role="alert">{messaggio(giudica.error)}</p>}
      {dati.rubrica.voci.map((v) => {
        const modello = t.stime_modello[v.codice]
        const mio = t.miei_giudizi[v.codice]
        return (
          <fieldset key={v.codice} className="voce-rubrica">
            <legend><span className="mono">{v.codice} · asse {v.asse}</span> {v.nome}</legend>
            <div className="livelli">
              {v.livelli.map((testo, livello) => (
                <button key={livello} type="button" aria-pressed={mio === livello}
                  className={`livello ${mio === livello ? 'scelto' : ''} ${modello !== undefined && Math.round(modello) === livello ? 'modello' : ''}`}
                  disabled={giudica.isPending} onClick={() => giudica.mutate({ voce: v.codice, valore: livello })}>
                  <b>{livello}</b><span>{testo}</span>
                </button>
              ))}
            </div>
            {modello !== undefined && <p className="mono stima-modello">stima del modello: {modello}</p>}
          </fieldset>
        )
      })}
    </section>
  )
}

export function Revisione() {
  const { codice } = useParams({ strict: false }) as { codice: string }
  const io = useQuery({ queryKey: ['io'], queryFn: api.io })
  const organizzazioni = useQuery({ queryKey: ['organizzazioni'], queryFn: api.organizzazioni })
  const dati = useQuery({ queryKey: ['revisione', codice], queryFn: () => api.revisione(codice) })
  const [indice, setIndice] = useState(0)
  if (dati.isPending || io.isPending || organizzazioni.isPending) return <p className="vuoto" aria-busy="true">Carico la coda…</p>
  if (dati.error || io.error || organizzazioni.error) {
    return (
      <div className="vuoto">
        <p className="errore" role="alert">{messaggio(dati.error ?? io.error ?? organizzazioni.error)}</p>
        <Link to="/app" className="btn btn-secondary" style={{ marginTop: 16 }}>Torna alle tue organizzazioni</Link>
      </div>
    )
  }
  const nome = organizzazioni.data.find((o) => o.codice === codice)?.nome ?? codice
  const coda = dati.data.coda
  const voci = dati.data.rubrica.voci.length
  return (
    <Guscio codice={codice} nomeOrganizzazione={nome} ruolo="revisore" soggetto={io.data.soggetto}>
      <div className="head">
        <div>
          <span className="eyebrow">{nome} · revisione · rubrica {dati.data.rubrica.versione}</span>
          <h1>{coda.length} task da valutare, dal meno certo</h1>
        </div>
        <Link to="/app/org/$codice/panoramica" params={{ codice }} className="btn btn-secondary">Torna alla mappa</Link>
      </div>
      {coda.length === 0 ? (
        <div className="card vuoto"><h2>Nessun task da valutare</h2>
          <p>La coda si riempie dopo il calcolo della mappa dell'organizzazione.</p></div>
      ) : (
        <div className="revisione">
          <ol className="coda" aria-label="Coda dei task">
            {coda.map((t, i) => (
              <li key={t.task_id}>
                <button type="button" aria-current={i === indice ? 'true' : undefined} onClick={() => setIndice(i)}>
                  <b>{t.task}</b>
                  <span className="mono">certezza {Math.round(t.certezza * 100)}% · {Object.keys(t.miei_giudizi).length}/{voci} tue voci</span>
                </button>
              </li>
            ))}
          </ol>
          <Task key={coda[indice].task_id} codice={codice} dati={dati.data} indice={indice} />
        </div>
      )}
    </Guscio>
  )
}
