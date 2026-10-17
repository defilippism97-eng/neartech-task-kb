import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, RouterProvider } from '@tanstack/react-router'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Fase, Occorrenza, Panoramica, Percorso } from '../api'
import { Avanzamento } from '../componenti/Avanzamento'
import { MappaQuadranti } from '../componenti/MappaQuadranti'
import { creaRouter } from '../rotte'
import { inviti } from '../inviti'

const occorrenza = (id: string, n: number, d: number, quadrante: Occorrenza['quadrante']): Occorrenza => ({
  occorrenza_id: id, task_id: `t-${id}`, task: `Task ${id}`, ruolo_id: 'r1', ruolo: 'Controller', quadrante,
  probabilita: 0.9, pari: false, n, n_dev: 0.05, d, d_dev: 0.05, instabile: false,
})

const percorso = (fase: Fase, approvazione: number | null = null): Percorso => {
  const ordine: Fase[] = ['avvio', 'indirizzi', 'verifica', 'esito']
  const stato = (f: Fase) => (ordine.indexOf(f) < ordine.indexOf(fase) || approvazione !== null ? 'fatta'
    : f === fase ? 'in_corso' : 'da_fare')
  return {
    fase_corrente: fase,
    fasi: [
      { codice: 'avvio', stato: stato('avvio'), fatti: { documenti: 6, attivita: 30, in_attesa_di_abbinamento: 0, occorrenze: 3 } },
      { codice: 'indirizzi', stato: stato('indirizzi'), fatti: { profilo_proprio: null, profilo_in_uso: 'p', proposta: null } },
      { codice: 'verifica', stato: stato('verifica'), fatti: { risultati: 2, da_confermare: 1, quota_giudizi_di_persona: 0.125 } },
      { codice: 'esito', stato: stato('esito'), fatti: { approvazione, impronta: 'f'.repeat(64) } },
    ],
  }
}

const panoramica = (sovrascrivi: Partial<Panoramica['restituzione']> = {}, fase: Fase = 'esito'): Panoramica => ({
  percorso: percorso(fase, sovrascrivi.approvazione ?? null),
  restituzione: {
    versione: 'restituzione-v2',
    organizzazione: { org_id: 'o1', nome: 'ACME S.p.A.', codice: 'acme' },
    nota: 'Nessun output riguarda una persona.',
    chiavi: { rubriche: ['r'], profili: ['p'], soglie_quadranti: [{ profilo: 'p', theta_n: 0.5, theta_d: 0.5 }], snapshot: ['s'],
      metodi_capacita: ['m'], versioni_calcolo: ['v'], capacita: ['riserva'], componenti_d: ['d1', 'd2'], modelli_giudizi: ['x'] },
    soglia_stabilita: { valore: 0.8, parametro_id: 'p1', versione: 1, comune: true },
    avvertenze: ['capacita_di_riserva', 'd_provvisorio', 'pesi_uguali', 'soglia_comune_non_adottata'],
    riepilogo: { occorrenze: 3, con_risultato: 2, senza_risultato: 1, quadranti: { q1: 1, q2: 0, q3: 0, q4: 1 }, instabili: 1, pari: 0 },
    ruoli: [{ ruolo_id: 'r1', ruolo: 'Controller', occorrenze: 2, baricentro_n: 0.4, baricentro_d: 0.5, dispersione: 0.1,
      stabilita: 0.85, pesi_tempo: 'uguali', provvisorio: true, quadranti: { q1: 1, q2: 0, q3: 0, q4: 1 }, instabili: 1 }],
    da_rivedere: [occorrenza('b', 0.2, 0.3, 'q4')],
    occorrenze: [occorrenza('a', 0.7, 0.8, 'q1'), occorrenza('b', 0.2, 0.3, 'q4')],
    impronta: 'f'.repeat(64),
    generato_il: '2026-10-17T10:00:00Z',
    approvazione: null,
    ...sovrascrivi,
  },
  avanzamento: { totale: 2, quota: 0.125, occorrenze: { a: ['d1', 'k1'] },
    voci: Object.fromEntries(['k1', 'k2', 'k3', 'r', 'd1', 'd2', 'd3', 'd4'].map((v) => [v, { persone: ['k1', 'd1'].includes(v) ? 1 : 0, totale: 2 }])) },
})

describe('mappa dei quadranti', () => {
  it('descrive i conteggi per quadrante e distingue i punti giudicati da persone', () => {
    const { container } = render(
      <MappaQuadranti occorrenze={panoramica().restituzione.occorrenze} thetaN={0.5} thetaD={0.5} giudicate={{ a: 2 }} />,
    )
    expect(screen.getByRole('img').getAttribute('aria-label')).toContain('Q1 · persona necessaria e desiderata 1')
    const punti = container.querySelectorAll('circle.punto')
    expect(punti).toHaveLength(2)
    expect(punti[0].getAttribute('fill')).toBe('#10B981')
    expect(punti[1].getAttribute('fill')).toBe('#fff')
  })
})

describe('avanzamento della sperimentazione', () => {
  it('mostra la quota di giudizi di persona e le voci che aspettano', () => {
    render(<Avanzamento dati={panoramica().avanzamento} />)
    expect(screen.getByRole('heading', { name: '13 giudizi su 100 vengono dalle vostre persone' })).toBeInTheDocument()
    expect(screen.getByText(/Ancora senza giudizi di persona: k2, k3, r, d2, d3, d4/)).toBeInTheDocument()
  })
})

describe('inviti all\'azione', () => {
  it('trasforma gli avvisi in inviti, non in blocchi', () => {
    const titoli = inviti(panoramica()).map((i) => i.titolo)
    expect(titoli).toEqual(['1 risultato da confermare', 'Fate vostra la soglia di stabilità',
      'D si basa su 2 componenti su 4', 'Ogni task pesa uguale nel suo ruolo', 'Capacità dell\'IA: stima documentale'])
  })
})

describe('panoramica del comitato', () => {
  let chiamate: { url: string; init?: RequestInit }[]
  let dati: Panoramica
  let ruolo: string
  let conflitto: string | null

  beforeEach(() => {
    chiamate = []
    dati = panoramica()
    ruolo = 'comitato_guida'
    conflitto = null
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
      chiamate.push({ url, init })
      if (url.endsWith('/approvazione') && conflitto) {
        return new Response(JSON.stringify({ detail: conflitto }), { status: 409, headers: { 'Content-Type': 'application/json' } })
      }
      const corpo = url === '/api/io'
        ? { utente_id: 'u', soggetto: 'prova|comitato', ruoli: [{ ruolo, org_id: 'o1', codice: 'acme', nome: 'ACME S.p.A.' }] }
        : url.endsWith('/approvazione') ? { atto: 91, impronta: dati.restituzione.impronta } : dati
      return new Response(JSON.stringify(corpo), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }))
    // jsdom non apre le finestre di dialogo: le si apre e chiude con l'attributo open.
    HTMLDialogElement.prototype.showModal = function (this: HTMLDialogElement) { this.setAttribute('open', '') }
    HTMLDialogElement.prototype.close = function (this: HTMLDialogElement) { this.removeAttribute('open') }
  })
  afterEach(() => vi.unstubAllGlobals())

  const monta = () => {
    const router = creaRouter(createMemoryHistory({ initialEntries: ['/org/acme/panoramica'] }))
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    )
  }

  it('mostra mappa, ruoli e inviti', async () => {
    monta()
    expect(await screen.findByRole('heading', { name: '2 task in 1 ruolo: dove sta ciascuno' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '1 risultato da confermare' })).toBeInTheDocument()
    const tabellaRuoli = screen.getByRole('region', { name: 'Ruoli' })
    expect(within(tabellaRuoli).getByRole('cell', { name: 'Controller' })).toBeInTheDocument()
    expect(screen.getByText('Comitato guida')).toBeInTheDocument()
  })

  it('nella fase degli indirizzi il comitato vede che cosa gli tocca e una mappa provvisoria', async () => {
    dati = panoramica({}, 'indirizzi')
    monta()
    expect(await screen.findByRole('heading', { name: 'Date gli indirizzi' })).toBeInTheDocument()
    expect(screen.getByText('mappa provvisoria')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Approva la restituzione' })).not.toBeInTheDocument()
    expect(screen.getByRole('listitem', { current: 'step' })).toHaveTextContent('Indirizzi')
  })

  it('il revisore vede la propria azione nella stessa fase', async () => {
    ruolo = 'revisore'
    dati = panoramica({}, 'verifica')
    monta()
    expect(await screen.findByRole('heading', { name: 'Controlla le classificazioni a campione' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Apri la coda' })).toHaveAttribute('href', '/org/acme/revisione')
  })

  it('senza risultati spiega come si riempie la mappa', async () => {
    dati = panoramica({ occorrenze: [], riepilogo: { occorrenze: 3, con_risultato: 0, senza_risultato: 3,
      quadranti: { q1: 0, q2: 0, q3: 0, q4: 0 }, instabili: null, pari: 0 }, ruoli: [] }, 'avvio')
    monta()
    expect(await screen.findByRole('heading', { name: 'La mappa si riempie dopo il primo calcolo' })).toBeInTheDocument()
  })

  it('mostra che cosa sta caricando', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    monta()
    return waitFor(() => expect(screen.getByText(/Verifico l'accesso|Carico la mappa/)).toBeInTheDocument())
  })

  it('non mostra l\'approvazione a chi non è del comitato', async () => {
    ruolo = 'revisore'
    monta()
    expect(await screen.findByRole('heading', { name: '2 task in 1 ruolo: dove sta ciascuno' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Approva la restituzione' })).not.toBeInTheDocument()
  })

  it('dice chiaramente se un altro membro ha già approvato', async () => {
    conflitto = 'decisione già presa'
    monta()
    fireEvent.click(await screen.findByRole('button', { name: 'Approva la restituzione' }))
    fireEvent.change(screen.getByLabelText('Motivazione dell\'atto'), { target: { value: 'letta in seduta' } })
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Approva la restituzione' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Un altro membro del comitato ha già approvato')
  })

  it('approva la restituzione con la sua impronta e l\'intestazione della piattaforma', async () => {
    monta()
    fireEvent.click(await screen.findByRole('button', { name: 'Approva la restituzione' }))
    fireEvent.change(screen.getByLabelText('Motivazione dell\'atto'), { target: { value: 'letta in seduta' } })
    const dialogo = screen.getByRole('dialog')
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Approva la restituzione' }))
    await waitFor(() => expect(chiamate.some((c) => c.url.endsWith('/approvazione'))).toBe(true))
    const invio = chiamate.find((c) => c.url.endsWith('/approvazione'))!
    expect(JSON.parse(invio.init!.body as string)).toEqual({ impronta: 'f'.repeat(64), motivazione: 'letta in seduta' })
    expect((invio.init!.headers as Record<string, string>)['X-Neartech-Richiesta']).toBe('1')
  })

  it('mostra la restituzione già approvata come percorso concluso', async () => {
    dati = panoramica({ approvazione: 91 })
    monta()
    expect(await screen.findByText('percorso concluso · atto #91')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Restituzione approvata' })).toBeInTheDocument()
    expect(screen.getByText('Percorso concluso')).toBeInTheDocument()
    expect(screen.queryByRole('listitem', { current: 'step' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Approva la restituzione' })).not.toBeInTheDocument()
  })

  it('il tracciato dice dove siete, le prove e chi deve agire', async () => {
    dati = panoramica({}, 'indirizzi')
    monta()
    const corrente = await screen.findByRole('listitem', { current: 'step' })
    expect(corrente).toHaveTextContent('Fase 2 di 4, Indirizzi: in corso. Mappa con i pesi di default NEARTECH. Attende: il comitato, sul questionario.')
    expect(screen.getByText('fase 2 di 4 · Indirizzi')).toBeInTheDocument()
    expect(screen.getByText('Tocca a voi')).toBeInTheDocument()
    expect(screen.getByText('Fase 1 di 4, Avvio: fatta. 6 mansionari · 3 task nella mappa. fatto: Abbinamenti applicati.')).toBeInTheDocument()
  })

  it('una fase in corso dopo quella corrente è in anticipo, con risultati provvisori', async () => {
    const d = panoramica({}, 'indirizzi')
    d.percorso.fasi[2].stato = 'in_corso'
    dati = d
    ruolo = 'revisore'
    monta()
    expect(await screen.findByText(/Fase 3 di 4, Verifica: in corso in anticipo, risultati provvisori\. 2 risultati provvisori · 1 da confermare/))
      .toBeInTheDocument()
    expect(screen.getByText('In attesa · ora agisce il comitato guida')).toBeInTheDocument()
  })

  it('in fase di esito l\'approvazione sta nella banda del percorso, non nell\'intestazione', async () => {
    monta()
    const banda = await screen.findByRole('group', { name: 'Approvate la restituzione' })
    expect(within(banda).getByRole('button', { name: 'Approva la restituzione' })).toBeInTheDocument()
  })
})
