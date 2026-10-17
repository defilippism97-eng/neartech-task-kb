import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from '@tanstack/react-router'
import { useState } from 'react'
import { api, ErroreApi, type StatoIndirizzi } from '../api'
import { Guscio } from '../componenti/Guscio'

// Indirizzi del comitato (fetta 3 della fase 6): questionario sulla visione dell'innovazione, profilo di pesi di D
// che ne deriva, effetto sui task, approvazione del comitato e verifica dell'auditor. Ogni passo è un atto.

const VOCI: Record<string, string> = {
  d1: 'Relazione e fiducia', d2: 'Responsabilità', d3: 'Senso del lavoro', d4: 'Valore per chi riceve il servizio',
}

function messaggio(errore: unknown): string {
  const e = errore as ErroreApi
  if (e?.stato === 403) return 'Non hai il permesso per questo atto in questa organizzazione.'
  if (e?.stato === 409) return 'Questo passo è già stato registrato, o va fatto prima un altro: ricarica la pagina.'
  if (e?.stato === 422) return 'Controlla i dati: servono una risposta per ogni domanda e una motivazione di almeno 3 caratteri.'
  return 'Impossibile completare l\'operazione. Controlla la connessione e riprova.'
}

function Questionario({ codice, dati }: { codice: string; dati: StatoIndirizzi }) {
  const q = dati.questionario!
  const [risposte, setRisposte] = useState<Record<string, number>>({})
  const [nota, setNota] = useState('')
  const client = useQueryClient()
  const invia = useMutation({
    mutationFn: () => api.rispondi(codice, risposte, nota.trim()),
    onSuccess: () => void client.invalidateQueries(),
  })
  const complete = q.domande.every((d) => risposte[d.codice] !== undefined)
  return (
    <form className="card questionario" onSubmit={(e) => { e.preventDefault(); invia.mutate() }}>
      <span className="eyebrow">Questionario degli indirizzi · {q.versione}</span>
      <h2 style={{ margin: '6px 0 4px' }}>Otto domande sulla vostra visione</h2>
      <p style={{ fontSize: 14, marginBottom: 16 }}>Le risposte spostano il peso delle quattro componenti di D. Nessuna risposta
        può portare un peso sotto il {q.limiti.min} o sopra il {q.limiti.max}.</p>
      {q.domande.map((d, i) => (
        <fieldset key={d.codice} className="domanda">
          <legend><span className="mono">{i + 1}/{q.domande.length} · {VOCI[d.voce]}</span>{d.testo}</legend>
          <div className="scala">
            {q.risposte.map((etichetta, valore) => (
              <label key={valore} className={risposte[d.codice] === valore ? 'scelta-attiva' : ''}>
                <input type="radio" name={d.codice} value={valore} checked={risposte[d.codice] === valore}
                  onChange={() => setRisposte({ ...risposte, [d.codice]: valore })} />
                {etichetta}
              </label>
            ))}
          </div>
        </fieldset>
      ))}
      <label htmlFor="nota" style={{ fontWeight: 600, fontSize: 14 }}>Nota del comitato (facoltativa)</label>
      <textarea id="nota" maxLength={4000} value={nota} onChange={(e) => setNota(e.target.value)}
        placeholder="Es.: vogliamo liberare tempo dalle pratiche per la relazione con i clienti" />
      <p className="mono" style={{ fontSize: 11, marginTop: -6, marginBottom: 12 }}>Resta nello spazio della vostra organizzazione.</p>
      {invia.error && <p className="errore" role="alert">{messaggio(invia.error)}</p>}
      <button type="submit" className="btn btn-primary" disabled={!complete || invia.isPending}>
        {invia.isPending ? 'Calcolo il profilo…' : 'Calcola il profilo di pesi'}
      </button>
    </form>
  )
}

function Decisione({ codice, profilo, atto, titolo, pulsante }: {
  codice: string; profilo: string; atto: 'approvazione' | 'verifica'; titolo: string; pulsante: string
}) {
  const [motivazione, setMotivazione] = useState('')
  const client = useQueryClient()
  const decidi = useMutation({
    mutationFn: () => api.decidiProfilo(codice, profilo, atto, motivazione.trim()),
    onSettled: () => void client.invalidateQueries(),
  })
  return (
    <div className="decisione">
      <label htmlFor={`motivazione-${atto}`} style={{ fontWeight: 600, fontSize: 14 }}>{titolo}</label>
      <textarea id={`motivazione-${atto}`} maxLength={4000} value={motivazione} onChange={(e) => setMotivazione(e.target.value)}
        placeholder="Motivazione dell'atto" />
      {decidi.error && <p className="errore" role="alert">{messaggio(decidi.error)}</p>}
      <button type="button" className="btn btn-primary" disabled={motivazione.trim().length < 3 || decidi.isPending}
        onClick={() => decidi.mutate()}>{decidi.isPending ? 'Registro l\'atto…' : pulsante}</button>
    </div>
  )
}

function Profilo({ codice, dati, ruolo }: { codice: string; dati: StatoIndirizzi; ruolo: string }) {
  const p = dati.profilo!
  const passi = [
    ['Risposte del comitato', true],
    ['Approvazione del comitato', p.approvato !== null],
    ['Verifica dell\'auditor', p.verificato !== null],
    ['Profilo attivo', p.attivo],
  ] as const
  return (
    <section className="card" aria-labelledby="titolo-profilo">
      <span className="eyebrow">Profilo {p.profile_id}</span>
      <h2 id="titolo-profilo" style={{ margin: '6px 0 12px' }}>
        {p.attivo ? 'Il vostro profilo di pesi è attivo' : 'Profilo di pesi proposto dalle vostre risposte'}
      </h2>
      <ol className="passi-atto">
        {passi.map(([nome, fatto]) => <li key={nome} className={fatto ? 'fatto' : ''}><span aria-hidden="true">{fatto ? '✓' : '○'}</span> {nome}</li>)}
      </ol>
      <div className="grid g-12" style={{ marginTop: 16 }}>
        <div className="s7">
          <h3>Pesi di D</h3>
          <table className="pesi">
            <thead><tr><th>Componente</th><th>In uso</th><th>Proposto</th></tr></thead>
            <tbody>
              {Object.keys(VOCI).map((v) => {
                const prima = dati.pesi_in_uso.pesi[v], dopo = p.pesi[v]
                return (
                  <tr key={v}>
                    <td>{VOCI[v]}</td><td className="mono">{prima.toFixed(3)}</td>
                    <td className="mono"><b>{dopo.toFixed(3)}</b> {dopo > prima + 1e-9 ? '▲' : dopo < prima - 1e-9 ? '▼' : ''}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <div className="s5">
          {p.effetto && (
            <div className="soft">
              <h3>Effetto sui task</h3>
              <p style={{ fontSize: 14, marginTop: 4 }}>
                <b style={{ color: 'var(--navy)', fontSize: 26 }}>{p.effetto.cambiano_quadrante}</b> task su {p.effetto.occorrenze} cambiano quadrante.
              </p>
              <p className="mono" style={{ fontSize: 12 }}>Q1 {p.effetto.quadranti.q1} · Q2 {p.effetto.quadranti.q2} · Q3 {p.effetto.quadranti.q3} · Q4 {p.effetto.quadranti.q4}</p>
            </div>
          )}
          {p.controlli.length > 0 && (
            <ul className="controlli">
              {p.controlli.map((c) => <li key={c.codice}><span className={`state ${c.esito ? 'persone' : 'stima'}`}>{c.esito ? 'superato' : 'non superato'}</span> {c.descrizione}</li>)}
            </ul>
          )}
        </div>
      </div>
      {!p.attivo && ruolo === 'comitato_guida' && p.approvato === null && (
        <Decisione codice={codice} profilo={p.profile_id} atto="approvazione" titolo="Approvazione del comitato" pulsante="Approva il profilo di pesi" />
      )}
      {!p.attivo && ruolo === 'auditor' && p.approvato !== null && p.verificato === null && (
        <Decisione codice={codice} profilo={p.profile_id} atto="verifica" titolo="Verifica dell'auditor" pulsante="Dai l'ok al profilo" />
      )}
    </section>
  )
}

export function Indirizzi() {
  const { codice } = useParams({ strict: false }) as { codice: string }
  const io = useQuery({ queryKey: ['io'], queryFn: api.io })
  const organizzazioni = useQuery({ queryKey: ['organizzazioni'], queryFn: api.organizzazioni })
  const dati = useQuery({ queryKey: ['indirizzi', codice], queryFn: () => api.indirizzi(codice) })
  if (dati.isPending || io.isPending || organizzazioni.isPending) return <p className="vuoto" aria-busy="true">Carico gli indirizzi…</p>
  if (dati.error || io.error || organizzazioni.error) {
    return (
      <div className="vuoto">
        <p className="errore" role="alert">{messaggio(dati.error ?? io.error ?? organizzazioni.error)}</p>
        <Link to="/" className="btn btn-secondary" style={{ marginTop: 16 }}>Torna alle tue organizzazioni</Link>
      </div>
    )
  }
  const nome = organizzazioni.data.find((o) => o.codice === codice)?.nome ?? codice
  const ruoli = io.data.ruoli.filter((r) => r.codice === codice || r.org_id === null).map((r) => r.ruolo)
  const ruolo = ruoli.includes('comitato_guida') ? 'comitato_guida' : ruoli.includes('auditor') ? 'auditor' : ruoli[0] ?? ''
  const d = dati.data
  const puoRispondere = ruolo === 'comitato_guida' && d.questionario !== null && (d.profilo === null || d.profilo.attivo)
  return (
    <Guscio codice={codice} nomeOrganizzazione={nome} ruolo={ruolo} soggetto={io.data.soggetto}>
      <div className="head">
        <div>
          <span className="eyebrow">{nome} · indirizzi del comitato</span>
          <h1>La vostra visione, tradotta in pesi</h1>
        </div>
        <Link to="/org/$codice/panoramica" params={{ codice }} className="btn btn-secondary">Torna alla mappa</Link>
      </div>
      {d.questionario === null ? (
        <div className="card vuoto">
          <h2>Il questionario degli indirizzi non è ancora approvato</h2>
          <p>Domande e regola che traduce le risposte in pesi sono un parametro di governance: si usano dopo
            l'approvazione. Fino ad allora la mappa usa i pesi di default NEARTECH ({d.pesi_in_uso.profilo}).</p>
        </div>
      ) : (
        <div className="grid" style={{ gap: 18 }}>
          {d.profilo && <Profilo codice={codice} dati={d} ruolo={ruolo} />}
          {puoRispondere && <Questionario codice={codice} dati={d} />}
          {!d.profilo && ruolo !== 'comitato_guida' && (
            <div className="card vuoto"><h2>Il comitato non ha ancora dato gli indirizzi</h2>
              <p>Quando risponderà al questionario, qui vedrai il profilo di pesi proposto e il suo effetto sui task.</p></div>
          )}
        </div>
      )}
    </Guscio>
  )
}
