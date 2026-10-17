import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from '@tanstack/react-router'
import { useState, type ChangeEvent } from 'react'
import { api, ErroreApi, type Pipeline } from '../api'
import { STATI_DOCUMENTO, STATI_LOTTO } from '../azioni'
import { Guscio } from '../componenti/Guscio'

// Amministratore tecnico (fetta 5 della fase 6): mansionari, stima dei costi, scomposizione, lotti di abbinamento.
// Le chiamate al modello e l'embedding li esegue il lavoratore della coda: qui si caricano i file e si registrano gli atti.

const euro = (x: number) => x.toLocaleString('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 3 })
const migliaia = (x: number) => x.toLocaleString('it-IT')

function messaggio(errore: unknown): string {
  const e = errore as ErroreApi
  if (e?.stato === 403) return 'Solo l\'amministratore tecnico gestisce i documenti di questa organizzazione.'
  if (e?.stato === 422) return 'Operazione non accettata: controlla il file o lo stato dei documenti e riprova.'
  return 'Operazione non riuscita. Controlla la connessione e riprova.'
}

async function base64(file: File): Promise<string> {
  const byte = new Uint8Array(await file.arrayBuffer())
  let binario = ''
  for (let i = 0; i < byte.length; i += 0x8000) binario += String.fromCharCode(...byte.subarray(i, i + 0x8000))
  return btoa(binario)
}

export function Atto({ id, etichetta, pulsante, attesa, esegui, errore = messaggio }: {
  id: string; etichetta: string; pulsante: string; attesa: string; esegui: (motivazione: string) => Promise<unknown>
  errore?: (e: unknown) => string
}) {
  const [motivazione, setMotivazione] = useState('')
  const client = useQueryClient()
  const atto = useMutation({
    mutationFn: () => esegui(motivazione.trim()),
    onSuccess: () => setMotivazione(''),
    onSettled: () => void client.invalidateQueries(),
  })
  return (
    <div className="decisione">
      <label htmlFor={id} style={{ fontWeight: 600, fontSize: 13 }}>{etichetta}</label>
      <textarea id={id} maxLength={4000} value={motivazione} onChange={(e) => setMotivazione(e.target.value)}
        placeholder="Motivazione dell'atto" />
      {atto.error && <p className="errore" role="alert">{errore(atto.error)}</p>}
      <button type="button" className="btn btn-primary" disabled={motivazione.trim().length < 3 || atto.isPending}
        onClick={() => atto.mutate()}>{atto.isPending ? attesa : pulsante}</button>
    </div>
  )
}

function Caricamento({ codice }: { codice: string }) {
  const client = useQueryClient()
  const [esiti, setEsiti] = useState<string[]>([])
  const carica = useMutation({
    mutationFn: async (files: File[]) => {
      const righe: string[] = []
      for (const file of files) {
        try {
          const r = await api.caricaDocumento(codice, file.name, await base64(file))
          righe.push(`${file.name}: ${r.nuovo ? `caricato, ruolo «${r.ruolo}»` : 'già presente'}`)
        } catch (errore) {
          righe.push(`${file.name}: ${(errore as ErroreApi)?.stato === 422
            ? 'non è un mansionario leggibile (serve il campo «Titolo della posizione»)' : messaggio(errore)}`)
        }
      }
      return righe
    },
    onSuccess: setEsiti,
    onSettled: () => void client.invalidateQueries({ queryKey: ['documenti', codice] }),
  })
  const scelti = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    e.target.value = ''
    if (files.length) carica.mutate(files)
  }
  return (
    <div className="caricamento">
      <label className="btn btn-primary">
        {carica.isPending ? 'Carico i file…' : 'Carica mansionari .docx'}
        <input type="file" accept=".docx" multiple onChange={scelti} disabled={carica.isPending} className="nascosto" />
      </label>
      {esiti.length > 0 && <ul className="esiti" aria-live="polite">{esiti.map((x) => <li key={x}>{x}</li>)}</ul>}
    </div>
  )
}

function Scomposizione({ codice, dati }: { codice: string; dati: Pipeline }) {
  const daAvviare = dati.documenti.filter((d) => d.stato === 'da_avviare' || d.stato === 'fallito')
  if (daAvviare.length === 0) return null
  const s = dati.stima_da_avviare
  return (
    <section className="card" aria-labelledby="titolo-scomposizione">
      <span className="eyebrow">Scomposizione{dati.prezzi ? ` · ${dati.prezzi.modello}` : ''}</span>
      <h2 id="titolo-scomposizione" style={{ margin: '6px 0 10px' }}>
        {daAvviare.length === 1 ? '1 mansionario da scomporre' : `${daAvviare.length} mansionari da scomporre`}
      </h2>
      {dati.prezzi === null || s === null ? (
        <p className="avviso" role="note">Manca il parametro approvato dei prezzi (<span className="mono">prezzi_scomposizione</span>):
          la stima dei costi viene prima di ogni chiamata al modello. Va approvato dal comitato di governance.</p>
      ) : (
        <>
          <dl className="stima-costi">
            <div><dt>Costo stimato</dt><dd>{euro(s.costo)}</dd></div>
            <div><dt>Al massimo, con i tentativi</dt><dd>{euro(s.costo_massimo)}</dd></div>
            <div><dt>Token in ingresso</dt><dd className="mono">~{migliaia(s.token_ingresso)}</dd></div>
            <div><dt>Token in uscita</dt><dd className="mono">~{migliaia(s.token_uscita)}</dd></div>
          </dl>
          <p className="mono nota-stima">Prezzi dal parametro v{dati.prezzi.versione}: {dati.prezzi.ingresso_eur_mtok} € e {dati.prezzi.uscita_eur_mtok} € per
            milione di token. L'atto registra stima e parametro.</p>
          <Atto id="motivazione-scomposizione" etichetta="Conferma della stima" pulsante="Conferma la stima e avvia"
            attesa="Accodo i documenti…"
            esegui={(m) => api.avviaScomposizione(codice, daAvviare.map((d) => d.caricamento_id), m)} />
        </>
      )}
    </section>
  )
}

export function Documenti() {
  const { codice } = useParams({ strict: false }) as { codice: string }
  const io = useQuery({ queryKey: ['io'], queryFn: api.io })
  const organizzazioni = useQuery({ queryKey: ['organizzazioni'], queryFn: api.organizzazioni })
  const dati = useQuery({
    queryKey: ['documenti', codice], queryFn: () => api.documenti(codice),
    // Mentre il lavoratore lavora, lo stato si aggiorna da solo.
    refetchInterval: (q) => {
      const d = q.state.data
      const attivi = d && (d.proposta_in_coda || d.documenti.some((x) => x.stato === 'in_coda' || x.stato === 'in_corso')
        || d.lotti.some((l) => l.stato === 'in_applicazione'))
      return attivi ? 4000 : false
    },
  })
  if (dati.isPending || io.isPending || organizzazioni.isPending) return <p className="vuoto" aria-busy="true">Carico i documenti…</p>
  if (dati.error || io.error || organizzazioni.error) {
    return (
      <div className="vuoto">
        <p className="errore" role="alert">{messaggio(dati.error ?? io.error ?? organizzazioni.error)}</p>
        <Link to="/" className="btn btn-secondary" style={{ marginTop: 16 }}>Torna alle tue organizzazioni</Link>
      </div>
    )
  }
  const nome = organizzazioni.data.find((o) => o.codice === codice)?.nome ?? codice
  const d = dati.data
  const estratte = d.documenti.reduce((n, x) => n + x.candidati, 0)
  return (
    <Guscio codice={codice} nomeOrganizzazione={nome} ruolo="amministratore_tecnico" soggetto={io.data.soggetto}>
      <div className="head">
        <div>
          <span className="eyebrow">{nome} · documenti e abbinamento</span>
          <h1>{d.documenti.length === 0 ? 'Carica i mansionari dell\'organizzazione'
            : `${d.documenti.length} ${d.documenti.length === 1 ? 'mansionario' : 'mansionari'}, ${estratte} task estratti`}</h1>
        </div>
        <Link to="/org/$codice/panoramica" params={{ codice }} className="btn btn-secondary">Torna alla mappa</Link>
      </div>
      <div className="grid" style={{ gap: 18 }}>
        <section className="card" aria-labelledby="titolo-mansionari">
          <div className="riga-titolo">
            <div>
              <span className="eyebrow">Mansionari</span>
              <h2 id="titolo-mansionari" style={{ margin: '6px 0 4px' }}>Documenti caricati</h2>
              <p style={{ fontSize: 13 }}>Il testo resta nello spazio riservato dell'organizzazione. Il ruolo si legge dal campo «Titolo della posizione».</p>
            </div>
            <Caricamento codice={codice} />
          </div>
          {d.documenti.length === 0 ? (
            <p className="vuoto-breve">Nessun mansionario ancora. Caricali in formato .docx: la scomposizione parte solo dopo la conferma della stima.</p>
          ) : (
            <div className="tabella-scorre">
              <table className="tabella">
                <thead><tr><th>File</th><th>Ruolo</th><th>Stato</th><th>Task</th><th>Stima</th></tr></thead>
                <tbody>
                  {d.documenti.map((x) => (
                    <tr key={x.caricamento_id}>
                      <td className="mono">{x.nome_file}</td>
                      <td>{x.ruolo}</td>
                      <td><span className={`chip chip-${x.stato}`}>{STATI_DOCUMENTO[x.stato]}</span>
                        {x.errore && <div className="errore-breve">{x.errore}</div>}</td>
                      <td className="mono">{x.stato === 'fatto' ? x.candidati : '–'}</td>
                      <td className="mono">{x.stima ? euro(x.stima.costo) : '–'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <Scomposizione codice={codice} dati={d} />

        <section className="card" aria-labelledby="titolo-abbinamento">
          <span className="eyebrow">Abbinamento al dataset</span>
          <h2 id="titolo-abbinamento" style={{ margin: '6px 0 6px' }}>
            {d.candidati_da_proporre === 1 ? '1 task da abbinare' : `${d.candidati_da_proporre} task da abbinare`}
          </h2>
          <p style={{ fontSize: 13 }}>Un lotto propone per ogni task del mansionario il più vicino del dataset. Livello di revisione, campione e
            decisione spettano al revisore; l'applicazione torna a te.</p>
          {d.proposta_in_coda ? (
            <p className="avviso" role="status">Proposta in coda: il lavoratore calcola le vicinanze.</p>
          ) : d.candidati_da_proporre > 0 && (
            <Atto id="motivazione-proposta" etichetta="Richiesta del lotto" pulsante="Proponi un lotto" attesa="Accodo la proposta…"
              esegui={(m) => api.proponiLotto(codice, m)} />
          )}
          {d.lotti.length > 0 && (
            <div className="tabella-scorre" style={{ marginTop: 14 }}>
              <table className="tabella">
                <thead><tr><th>Lotto</th><th>Proposte</th><th>Livello</th><th>Stato</th></tr></thead>
                <tbody>
                  {d.lotti.map((l) => (
                    <tr key={l.lotto_id}>
                      <td className="mono">{l.lotto_id.slice(0, 8)} · {new Date(l.creato_il).toLocaleDateString('it-IT')}</td>
                      <td className="mono">{l.proposte}</td>
                      <td>{l.livello ?? '–'}</td>
                      <td>
                        <span className={`chip chip-lotto-${l.stato}`}>{STATI_LOTTO[l.stato]}</span>
                        {l.stato === 'deciso' && (
                          <Atto id={`motivazione-applica-${l.lotto_id}`} etichetta="Applicazione del lotto" pulsante="Applica il lotto"
                            attesa="Accodo l'applicazione…" esegui={(m) => api.applicaLotto(codice, l.lotto_id, m)} />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {d.lavori.length > 0 && (
          <section className="card" aria-labelledby="titolo-lavori">
            <span className="eyebrow">Coda dei lavori</span>
            <h2 id="titolo-lavori" style={{ margin: '6px 0 10px' }}>Ultimi lavori</h2>
            <ul className="lavori">
              {d.lavori.map((j) => (
                <li key={j.job_id}>
                  <span className={`chip chip-${j.stato}`}>{j.stato === 'fatto' ? 'completato' : STATI_DOCUMENTO[j.stato]}</span>
                  <span>{j.tipo.replaceAll('_', ' ')}</span>
                  <span className="mono">{new Date(j.creato_il).toLocaleString('it-IT')}{j.tentativi > 1 ? ` · ${j.tentativi} tentativi` : ''}</span>
                  {j.errore && <span className="errore-breve">{j.errore}</span>}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </Guscio>
  )
}
