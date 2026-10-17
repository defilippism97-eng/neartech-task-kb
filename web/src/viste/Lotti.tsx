import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from '@tanstack/react-router'
import { useState } from 'react'
import { api, ErroreApi, type DettaglioLotto, type EsitoCampione, type Lotto } from '../api'
import { Guscio } from '../componenti/Guscio'
import { STATI_LOTTO } from '../azioni'
import { Atto } from './Documenti'

// Revisore (fetta 5 della fase 6): lotti di abbinamento dal livello di revisione alla decisione.
// Revisione cieca: finché la precisione non è calcolata si vedono solo le coppie del campione, senza distanze.

const LIVELLI = [
  { codice: 'campione', nome: 'A campione', testo: 'Giudichi un campione casuale con la quota approvata; la precisione misurata entra nell\'atto.' },
  { codice: 'completa', nome: 'Completa', testo: 'Giudichi tutte le proposte con un task vicino.' },
  { codice: 'nulla', nome: 'Nessuna', testo: 'Decidi senza campione. L\'atto lo registra.' },
] as const

const ESITI: { codice: EsitoCampione; nome: string }[] = [
  { codice: 'corretto', nome: 'Stesso task' }, { codice: 'parziale', nome: 'In parte' }, { codice: 'errato', nome: 'Task diverso' },
]

function messaggio(errore: unknown): string {
  const e = errore as ErroreApi
  if (e?.stato === 403) return 'Solo i revisori di questa organizzazione decidono i lotti.'
  if (e?.stato === 409) return e.message === 'decisione già presa' ? 'Un altro revisore ha già deciso questo passo: ricarico il lotto.'
    : 'Il passo non è ancora possibile: completa prima quello precedente.'
  return 'Operazione non riuscita. Controlla la connessione e riprova.'
}

const percento = (x: number) => `${Math.round(x * 100)}%`

function Campione({ codice, d }: { codice: string; d: DettaglioLotto }) {
  const client = useQueryClient()
  const giudica = useMutation({
    mutationFn: ({ posizione, esito }: { posizione: number; esito: EsitoCampione }) =>
      api.azioneLotto(codice, d.lotto.lotto_id, 'giudizi', { posizione, esito }),
    onSettled: () => void client.invalidateQueries({ queryKey: ['lotti', codice] }),
  })
  const c = d.campione!
  return (
    <div>
      <p style={{ fontSize: 13, margin: '4px 0 12px' }}>Per ogni coppia: il task del mansionario è lo stesso task del dataset?
        Istruzioni <span className="mono">{c.istruzioni}</span>. Se cambi idea, scegli di nuovo: resta lo storico.</p>
      {giudica.error && <p className="errore" role="alert">{messaggio(giudica.error)}</p>}
      <ol className="coppie">
        {c.elementi.map((e) => (
          <li key={e.posizione} className="coppia">
            <div className="coppia-testi">
              <span className="mono">#{e.posizione}</span>
              <div><small>Task del mansionario</small><b>{e.candidato}</b></div>
              <div><small>Task del dataset</small><b>{e.task}</b></div>
            </div>
            <div className="esiti-coppia" role="group" aria-label={`Giudizio sulla coppia ${e.posizione}`}>
              {ESITI.map((x) => (
                <button key={x.codice} type="button" aria-pressed={e.mio_esito === x.codice}
                  className={`livello ${e.mio_esito === x.codice ? 'scelto' : ''}`} disabled={giudica.isPending}
                  onClick={() => giudica.mutate({ posizione: e.posizione, esito: x.codice })}>{x.nome}</button>
              ))}
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}

function Decisione({ codice, d }: { codice: string; d: DettaglioLotto }) {
  const [escluse, setEscluse] = useState<Set<string>>(new Set())
  const proposte = d.proposte ?? []
  const alterna = (id: string) => setEscluse((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n })
  const nuovi = proposte.filter((p) => p.task_id === null || escluse.has(p.proposta_id)).length
  return (
    <div>
      {d.campione?.misura && (
        <dl className="stima-costi">
          <div><dt>Precisione del campione</dt><dd>{percento(d.campione.misura.precisione)}</dd></div>
          <div><dt>Esito</dt><dd>{d.campione.misura.esito.replaceAll('_', ' ')}</dd></div>
          <div><dt>Coppie giudicate</dt><dd className="mono">{d.campione.misura.n_elementi}</dd></div>
          <div><dt>Errate o parziali</dt><dd className="mono">{d.campione.misura.n_errati + d.campione.misura.n_parziali}</dd></div>
        </dl>
      )}
      <p style={{ fontSize: 13, margin: '10px 0' }}>Proposte dalla più ambigua. Escludi quelle sbagliate: diventano task nuovi del dataset.
        Le altre si collegano al task proposto.</p>
      <ul className="proposte">
        {proposte.map((p) => (
          <li key={p.proposta_id}>
            <label>
              <input type="checkbox" checked={p.task_id === null || escluse.has(p.proposta_id)} disabled={p.task_id === null}
                onChange={() => alterna(p.proposta_id)} />
              <span><b>{p.candidato}</b> → {p.task_proposto ?? <em>nessun task vicino: sarà un task nuovo</em>}</span>
            </label>
            {p.distanza !== null && <span className="mono">distanza {p.distanza.toFixed(2)}{p.margine !== null ? ` · margine ${p.margine.toFixed(2)}` : ''}</span>}
          </li>
        ))}
      </ul>
      <p className="mono nota-stima">{proposte.length - nuovi} collegate · {nuovi} task nuovi</p>
      <Atto id="motivazione-decisione" etichetta="Decisione del lotto" pulsante="Decidi il lotto" attesa="Registro l'atto…" errore={messaggio}
        esegui={(m) => api.azioneLotto(codice, d.lotto.lotto_id, 'decisione', {
          rifiutate: proposte.filter((p) => p.task_id !== null && escluse.has(p.proposta_id)).map((p) => p.proposta_id), motivazione: m,
        })} />
    </div>
  )
}

function Livello({ codice, lotto }: { codice: string; lotto: Lotto }) {
  const [scelto, setScelto] = useState<string>('campione')
  return (
    <div>
      <fieldset className="scelte-livello">
        <legend>Livello di revisione</legend>
        {LIVELLI.map((l) => (
          <label key={l.codice} className={scelto === l.codice ? 'scelta-attiva' : ''}>
            <input type="radio" name="livello" value={l.codice} checked={scelto === l.codice} onChange={() => setScelto(l.codice)} />
            <b>{l.nome}</b><span>{l.testo}</span>
          </label>
        ))}
      </fieldset>
      <Atto id="motivazione-livello" etichetta="Motivazione del livello" pulsante="Registra il livello" attesa="Registro l'atto…" errore={messaggio}
        esegui={(m) => api.azioneLotto(codice, lotto.lotto_id, 'livello', { livello: scelto, motivazione: m })} />
    </div>
  )
}

function Passo({ codice, lotto }: { codice: string; lotto: Lotto }) {
  const client = useQueryClient()
  const dettaglio = useQuery({ queryKey: ['lotti', codice, lotto.lotto_id], queryFn: () => api.lotto(codice, lotto.lotto_id) })
  const esegui = useMutation({
    mutationFn: (azione: 'campione' | 'misura') =>
      api.azioneLotto(codice, lotto.lotto_id, azione, azione === 'campione' ? { motivazione: 'estrazione del campione del lotto' } : {}),
    onSettled: () => void client.invalidateQueries({ queryKey: ['lotti', codice] }),
  })
  const d = dettaglio.data
  return (
    <section className="card" aria-labelledby="titolo-lotto">
      <span className="eyebrow">Lotto {lotto.lotto_id.slice(0, 8)} · {lotto.proposte} proposte · {STATI_LOTTO[lotto.stato]}</span>
      <h2 id="titolo-lotto" style={{ margin: '6px 0 8px' }}>{TITOLI[lotto.stato](lotto)}</h2>
      {dettaglio.isPending && <p aria-busy="true">Carico il lotto…</p>}
      {dettaglio.error && <p className="errore" role="alert">{messaggio(dettaglio.error)}</p>}
      {esegui.error && <p className="errore" role="alert">{messaggio(esegui.error)}</p>}
      {d && lotto.stato === 'da_impostare' && <Livello codice={codice} lotto={lotto} />}
      {d && lotto.stato === 'da_campionare' && (
        <button type="button" className="btn btn-primary" disabled={esegui.isPending} onClick={() => esegui.mutate('campione')}>
          {esegui.isPending ? 'Estraggo…' : 'Estrai il campione'}</button>
      )}
      {d && (lotto.stato === 'da_giudicare' || lotto.stato === 'da_misurare') && d.campione && <Campione codice={codice} d={d} />}
      {d && lotto.stato === 'da_misurare' && (
        <button type="button" className="btn btn-primary" style={{ marginTop: 14 }} disabled={esegui.isPending}
          onClick={() => esegui.mutate('misura')}>{esegui.isPending ? 'Calcolo…' : 'Calcola la precisione'}</button>
      )}
      {d && lotto.stato === 'da_decidere' && <Decisione codice={codice} d={d} />}
      {d && ['deciso', 'in_applicazione', 'applicato'].includes(lotto.stato) && (
        <p style={{ fontSize: 14 }}>{lotto.stato === 'applicato' ? 'I task sono collegati al dataset ed entrano nel prossimo calcolo.'
          : 'Hai deciso il lotto. L\'amministratore tecnico lo applica al dataset.'}</p>
      )}
    </section>
  )
}

const TITOLI: Record<Lotto['stato'], (l: Lotto) => string> = {
  da_impostare: () => 'Scegli quanto rivedere',
  da_campionare: () => 'Estrai il campione da giudicare',
  da_giudicare: (l) => `${l.giudicati} di ${l.dimensione_campione} coppie giudicate`,
  da_misurare: () => 'Campione giudicato: calcola la precisione',
  da_decidere: () => 'Decidi il lotto',
  deciso: () => 'Lotto deciso',
  in_applicazione: () => 'Lotto in applicazione',
  applicato: () => 'Lotto applicato',
}

export function Lotti() {
  const { codice } = useParams({ strict: false }) as { codice: string }
  const io = useQuery({ queryKey: ['io'], queryFn: api.io })
  const organizzazioni = useQuery({ queryKey: ['organizzazioni'], queryFn: api.organizzazioni })
  const lotti = useQuery({ queryKey: ['lotti', codice], queryFn: () => api.lotti(codice) })
  const [scelto, setScelto] = useState<string | null>(null)
  if (lotti.isPending || io.isPending || organizzazioni.isPending) return <p className="vuoto" aria-busy="true">Carico i lotti…</p>
  if (lotti.error || io.error || organizzazioni.error) {
    return (
      <div className="vuoto">
        <p className="errore" role="alert">{messaggio(lotti.error ?? io.error ?? organizzazioni.error)}</p>
        <Link to="/" className="btn btn-secondary" style={{ marginTop: 16 }}>Torna alle tue organizzazioni</Link>
      </div>
    )
  }
  const nome = organizzazioni.data.find((o) => o.codice === codice)?.nome ?? codice
  const aperti = lotti.data.filter((l) => !['deciso', 'in_applicazione', 'applicato'].includes(l.stato))
  const attuale = lotti.data.find((l) => l.lotto_id === scelto) ?? aperti[0] ?? lotti.data[0]
  return (
    <Guscio codice={codice} nomeOrganizzazione={nome} ruolo="revisore" soggetto={io.data.soggetto}>
      <div className="head">
        <div>
          <span className="eyebrow">{nome} · lotti di abbinamento</span>
          <h1>{aperti.length === 0 ? 'Nessun lotto da decidere' : aperti.length === 1 ? '1 lotto da decidere' : `${aperti.length} lotti da decidere`}</h1>
        </div>
        <Link to="/org/$codice/panoramica" params={{ codice }} className="btn btn-secondary">Torna alla mappa</Link>
      </div>
      {lotti.data.length === 0 ? (
        <div className="card vuoto"><h2>Ancora nessun lotto</h2>
          <p>Un lotto nasce quando l'amministratore tecnico propone l'abbinamento dei task estratti dai mansionari.</p></div>
      ) : (
        <div className="revisione">
          <ol className="coda" aria-label="Lotti">
            {lotti.data.map((l) => (
              <li key={l.lotto_id}>
                <button type="button" aria-current={l.lotto_id === attuale.lotto_id ? 'true' : undefined} onClick={() => setScelto(l.lotto_id)}>
                  <b>Lotto {l.lotto_id.slice(0, 8)} · {l.proposte} proposte</b>
                  <span className="mono">{new Date(l.creato_il).toLocaleDateString('it-IT')} · {STATI_LOTTO[l.stato]}</span>
                </button>
              </li>
            ))}
          </ol>
          <Passo key={attuale.lotto_id + attuale.stato} codice={codice} lotto={attuale} />
        </div>
      )}
    </Guscio>
  )
}
