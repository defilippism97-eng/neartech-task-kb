import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from '@tanstack/react-router'
import { useRef, useState } from 'react'
import { api, ErroreApi, GIA_DECISA, SUPERATA, type Io, type Panoramica as DatiPanoramica, type Quadrante } from '../api'
import { Avanzamento } from '../componenti/Avanzamento'
import { BarraPercorso } from '../componenti/BarraPercorso'
import { Guscio } from '../componenti/Guscio'
import { ETICHETTE_RUOLO } from '../azioni'
import { MappaQuadranti, VOCI_TOTALI } from '../componenti/MappaQuadranti'
import { inviti } from '../inviti'

// Panoramica del comitato guida (fetta 1 della fase 6): mappa dei task, avanzamento della sperimentazione,
// inviti all'azione, ruoli e approvazione della restituzione con la sua impronta.
// Testi: docs/piattaforma/voce-e-testi.md.

const COLORI: Record<Quadrante, string> = { q1: '#00B4B4', q2: '#521983', q3: '#F59E0B', q4: '#1B499F' }
const QUADRANTI: Quadrante[] = ['q1', 'q2', 'q3', 'q4']
const MOTIVAZIONE_MASSIMA = 4000

const ruoli = (n: number) => (n === 1 ? '1 ruolo' : `${n} ruoli`)

// Errori che dicono come rimediare (docs/piattaforma/voce-e-testi.md).
function messaggioErrore(errore: ErroreApi): string {
  if (errore.stato === 403) return 'Non hai il permesso per questa operazione in questa organizzazione. Chiedilo all\'amministratore NEARTECH.'
  if (errore.stato === 409 && errore.message === GIA_DECISA) return 'Un altro membro del comitato ha già approvato questa restituzione.'
  if (errore.stato === 409 && errore.message === SUPERATA) return 'I risultati sono cambiati mentre li leggevi: la mappa è stata aggiornata, rileggila prima di approvare.'
  if (errore.stato === 503) return 'È in corso un calcolo. Riprova tra qualche istante.'
  if (errore.stato === 401) return 'La sessione è scaduta. Accedi di nuovo.'
  if (errore.stato === 422) return 'Controlla la motivazione: da 3 a 4.000 caratteri.'
  return 'Impossibile completare l\'operazione. Controlla la connessione e riprova.'
}

function Approvazione({ codice, dati, puoApprovare }: { codice: string; dati: DatiPanoramica; puoApprovare: boolean }) {
  const finestra = useRef<HTMLDialogElement>(null)
  const [motivazione, setMotivazione] = useState('')
  const client = useQueryClient()
  const r = dati.restituzione
  const aggiorna = () => void client.invalidateQueries({ queryKey: ['panoramica', codice] })
  const approva = useMutation({
    mutationFn: () => api.approva(codice, r.impronta, motivazione.trim()),
    onSuccess: () => {
      finestra.current?.close()
      setMotivazione('')
      aggiorna()
    },
    onError: aggiorna,  // dopo un conflitto la mappa mostra lo stato vero
  })
  if (r.approvazione !== null) {
    return <span className="state persone">Restituzione approvata · atto #{r.approvazione}</span>
  }
  if (!puoApprovare) return null
  return (
    <>
      <button type="button" className="btn btn-primary" onClick={() => finestra.current?.showModal()}
        disabled={r.riepilogo.con_risultato === 0}>
        Approva la restituzione
      </button>
      <dialog ref={finestra} aria-labelledby="titolo-approvazione" onClose={() => approva.reset()}>
        <span className="eyebrow">Atto del comitato guida</span>
        <h2 id="titolo-approvazione" style={{ margin: '8px 0 6px' }}>Approvare la restituzione?</h2>
        <p style={{ fontSize: 14 }}>
          Il comitato fa propri i risultati di oggi: {r.riepilogo.con_risultato} task in {ruoli(r.ruoli.length)}.
          L'atto resta nel registro con l'impronta <span className="mono">{r.impronta.slice(0, 12)}…</span>; se un
          calcolo cambia i risultati prima della conferma, la restituzione va riletta.
        </p>
        <label htmlFor="motivazione" style={{ display: 'block', marginTop: 14, fontWeight: 600, fontSize: 14 }}>
          Motivazione dell'atto
        </label>
        <textarea id="motivazione" aria-describedby="nota-motivazione" placeholder="Es.: discussa nella seduta del 20 ottobre"
          maxLength={MOTIVAZIONE_MASSIMA} value={motivazione} onChange={(e) => setMotivazione(e.target.value)} />
        <p id="nota-motivazione" className="mono" style={{ fontSize: 11, marginTop: -6, marginBottom: 12 }}>
          Resta nello spazio della vostra organizzazione, non nel dataset condiviso.
        </p>
        {approva.error && <p className="errore" role="alert">{messaggioErrore(approva.error as ErroreApi)}</p>}
        <div className="azioni">
          <button type="button" className="btn btn-secondary" onClick={() => finestra.current?.close()}>Torna alla mappa</button>
          <button type="button" className="btn btn-primary" disabled={motivazione.trim().length < 3 || approva.isPending}
            onClick={() => approva.mutate()}>
            {approva.isPending ? 'Registro l\'atto…' : 'Approva la restituzione'}
          </button>
        </div>
      </dialog>
    </>
  )
}

export function Panoramica() {
  const { codice } = useParams({ strict: false }) as { codice: string }
  const io = useQuery({ queryKey: ['io'], queryFn: api.io })
  const dati = useQuery({ queryKey: ['panoramica', codice], queryFn: () => api.panoramica(codice) })

  if (dati.isPending || io.isPending) return <p className="vuoto" aria-busy="true">Carico la mappa…</p>
  if (dati.error || io.error) {
    return (
      <div className="vuoto">
        <p className="errore" role="alert">{messaggioErrore((dati.error ?? io.error) as ErroreApi)}</p>
        <Link to="/" className="btn btn-secondary" style={{ marginTop: 16 }}>Torna alle tue organizzazioni</Link>
      </div>
    )
  }
  const r = dati.data.restituzione
  const soglie = r.chiavi.soglie_quadranti[0]
  const giudicate = Object.fromEntries(Object.entries(dati.data.avanzamento.occorrenze).map(([k, v]) => [k, v.length]))
  const stabili = r.riepilogo.instabili === null ? null : r.riepilogo.con_risultato - r.riepilogo.instabili
  const ruolo = ruoloInOrganizzazione(io.data, codice)

  const percorso = dati.data.percorso
  const provvisoria = percorso.fase_corrente !== 'esito'

  return (
    <Guscio codice={codice} nomeOrganizzazione={r.organizzazione.nome} ruolo={ruolo} soggetto={io.data.soggetto}>
      <div className="head">
        <div>
          <span className="eyebrow">{r.organizzazione.nome} · {ETICHETTE_RUOLO[ruolo] ?? 'percorso del pilota'}</span>
          <h1>{r.riepilogo.con_risultato} task in {ruoli(r.ruoli.length)}: dove sta ciascuno</h1>
        </div>
        <Approvazione codice={codice} dati={dati.data}
          puoApprovare={ruolo === 'comitato_guida' && percorso.fase_corrente === 'esito'} />
      </div>
      <BarraPercorso percorso={percorso} ruolo={ruolo} codice={codice} />
      <Avanzamento dati={dati.data.avanzamento} />
      {r.riepilogo.con_risultato === 0 ? (
        <div className="card vuoto">
          <h2>La mappa si riempie dopo il primo calcolo</h2>
          <p>Servono i mansionari scomposti in task e abbinati al dataset NEARTECH. Il calcolo lo avvia
            l'amministratore NEARTECH: appena finisce, qui vedete ogni task e il suo quadrante.</p>
        </div>
      ) : (
        <div className="grid g-12">
          <section className="card s7" aria-labelledby="titolo-mappa">
            <h2 id="titolo-mappa">Ogni task, tra necessità e desiderabilità della persona</h2>
            {provvisoria && (
              <p className="nota-mappa">
                <span className="state stima">mappa provvisoria</span>{' '}
                {percorso.fasi[1].stato === 'fatta'
                  ? 'Calcolata con il vostro profilo di pesi; diventa definitiva con l\'approvazione della restituzione.'
                  : 'Calcolata con i pesi di default NEARTECH: cambierà con gli indirizzi del comitato.'}
              </p>
            )}
            {soglie && <MappaQuadranti occorrenze={r.occorrenze} thetaN={soglie.theta_n} thetaD={soglie.theta_d} giudicate={giudicate} />}
            <div className="legend">
              <span><i style={{ background: 'var(--emerald)' }} />verde più pieno: più voci giudicate da persone (su {VOCI_TOTALI})</span>
              <span><i style={{ background: '#fff', border: '2px solid var(--amber)' }} />solo stime del modello</span>
              <span><i style={{ background: '#fff', border: '1.5px dashed var(--amber-ink)' }} />risultato incerto</span>
            </div>
          </section>
          <div className="s5 grid" style={{ alignContent: 'start' }}>
            <div className="grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
              <div className="soft kpi"><b>{r.riepilogo.quadranti.q4}</b><span>task dove l'automazione è possibile</span></div>
              <div className="soft kpi">
                <b>{stabili ?? '—'}</b>
                <span>{stabili === null ? 'risultati solidi: serve la soglia' : `risultati solidi su ${r.riepilogo.con_risultato}`}</span>
              </div>
            </div>
            {inviti(dati.data).map((invito) => (
              <div className="cta" key={invito.titolo}>
                <div className="ic" style={{ background: invito.colore[0], color: invito.colore[1] }} aria-hidden="true">{invito.icona}</div>
                <div><h3>{invito.titolo}</h3><p>{invito.testo}</p></div>
              </div>
            ))}
          </div>
          <section className="card s12" aria-labelledby="titolo-ruoli">
            <h2 id="titolo-ruoli" style={{ marginBottom: 8 }}>Ruoli</h2>
            <div className="ruoli-tabella">
              <table>
                <thead><tr><th>Ruolo</th><th>Task</th><th>N</th><th>D</th><th>Quadranti</th><th>Stabilità</th><th>Pesi</th></tr></thead>
                <tbody>
                  {r.ruoli.map((x) => (
                    <tr key={x.ruolo_id}>
                      <td><b style={{ color: 'var(--navy)', fontWeight: 600 }}>{x.ruolo}</b></td>
                      <td className="mono">{x.occorrenze}</td>
                      <td className="mono">{x.baricentro_n.toFixed(2)}</td>
                      <td className="mono">{x.baricentro_d.toFixed(2)}</td>
                      <td>
                        <div className="mini" role="img" aria-label={QUADRANTI.map((q) => `${q.toUpperCase()} ${x.quadranti[q]}`).join(', ')}>
                          {QUADRANTI.map((q) => (
                            <i key={q} style={{ width: `${(x.quadranti[q] / x.occorrenze) * 100}%`, background: COLORI[q] }} />
                          ))}
                        </div>
                      </td>
                      <td className="mono">{Math.round(x.stabilita * 100)}%</td>
                      <td>{x.pesi_tempo === 'uguali' ? <span className="state stima">uguali</span> : <span className="state persone">quote</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </Guscio>
  )
}

function ruoloInOrganizzazione(io: Io, codice: string): string {
  const diOrganizzazione = io.ruoli.filter((x) => x.codice === codice).map((x) => x.ruolo)
  if (diOrganizzazione.includes('comitato_guida')) return 'comitato_guida'
  return diOrganizzazione[0] ?? io.ruoli.find((x) => x.org_id === null)?.ruolo ?? ''
}
