import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, RouterProvider } from '@tanstack/react-router'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Revisione } from '../api'
import { creaRouter } from '../rotte'

const LIVELLI = ['nessuno', 'basso', 'medio', 'alto', 'pieno']

const revisione = (): Revisione => ({
  rubrica: { versione: 'bozza-3', voci: [
    { codice: 'k1', nome: 'Codificabilità', asse: 'N', livelli: LIVELLI },
    { codice: 'd1', nome: 'Valore per il servizio', asse: 'D', livelli: LIVELLI },
  ] },
  coda: [
    { task_id: 't1', task: 'Riconciliare i conti fornitori', ruoli: 'Controller', certezza: 0.42,
      stime_modello: { k1: 3.4, d1: 1.2 }, miei_giudizi: { k1: 2 }, voci_con_giudizi_di_persona: ['k1'] },
    { task_id: 't2', task: 'Preparare il budget annuale', ruoli: 'Controller', certezza: 0.61,
      stime_modello: { k1: 2, d1: 3 }, miei_giudizi: {}, voci_con_giudizi_di_persona: [] },
  ],
})

describe('revisione', () => {
  let chiamate: { url: string; init?: RequestInit }[]
  let dati: Revisione
  let negato: boolean

  beforeEach(() => {
    chiamate = []
    dati = revisione()
    negato = false
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
      chiamate.push({ url, init })
      if (url.includes('/revisione') && negato) {
        return new Response(JSON.stringify({ detail: 'permesso negato' }), { status: 403, headers: { 'Content-Type': 'application/json' } })
      }
      const corpo = url === '/api/io'
        ? { utente_id: 'u', soggetto: 'prova|revisore', ruoli: [{ ruolo: 'revisore', org_id: 'o1', codice: 'acme', nome: 'ACME S.p.A.' }] }
        : url === '/api/organizzazioni' ? [{ codice: 'acme', nome: 'ACME S.p.A.' }]
          : url.endsWith('/giudizi') ? { atto: 77 } : dati
      return new Response(JSON.stringify(corpo), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }))
  })
  afterEach(() => vi.unstubAllGlobals())

  const monta = () => {
    const router = creaRouter(createMemoryHistory({ initialEntries: ['/org/acme/revisione'] }))
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    )
  }

  it('mostra la coda dal meno certo, la stima del modello e il proprio giudizio', async () => {
    monta()
    expect(await screen.findByRole('heading', { name: '2 task da valutare, dal meno certo' })).toBeInTheDocument()
    const coda = screen.getByRole('list', { name: 'Coda dei task' })
    expect(within(coda).getAllByRole('button')[0]).toHaveTextContent('1/2 tue voci')
    const k1 = screen.getByRole('group', { name: /Codificabilità/ })
    expect(within(k1).getByRole('button', { pressed: true })).toHaveTextContent('2')
    expect(within(k1).getByRole('button', { name: /^3/ })).toHaveClass('modello')
    expect(screen.getByRole('link', { name: 'Revisione' })).toBeInTheDocument()
  })

  it('registra il giudizio con la nota e l\'intestazione della piattaforma', async () => {
    monta()
    await screen.findByRole('heading', { name: '2 task da valutare, dal meno certo' })
    fireEvent.change(screen.getByLabelText('Nota per i prossimi giudizi (facoltativa)'), { target: { value: 'routine' } })
    const d1 = screen.getByRole('group', { name: /Valore per il servizio/ })
    fireEvent.click(within(d1).getByRole('button', { name: /^4/ }))
    await waitFor(() => expect(chiamate.some((c) => c.url.endsWith('/giudizi'))).toBe(true))
    const invio = chiamate.find((c) => c.url.endsWith('/giudizi'))!
    expect(invio.url).toBe('/api/organizzazioni/acme/revisione/giudizi')
    expect(JSON.parse(String(invio.init?.body))).toEqual({ task_id: 't1', voce: 'd1', valore: 4, nota: 'routine' })
    expect(new Headers(invio.init!.headers).get('X-Neartech-Richiesta')).toBe('1')
  })

  it('passa a un altro task della coda', async () => {
    monta()
    await screen.findByRole('heading', { name: '2 task da valutare, dal meno certo' })
    fireEvent.click(screen.getByRole('button', { name: /Preparare il budget annuale/ }))
    expect(screen.getByRole('heading', { level: 2, name: 'Preparare il budget annuale' })).toBeInTheDocument()
  })

  it('con la coda vuota spiega quando si riempie', async () => {
    dati = { ...revisione(), coda: [] }
    monta()
    expect(await screen.findByRole('heading', { name: 'Nessun task da valutare' })).toBeInTheDocument()
  })

  it('a chi non è revisore spiega il limite e offre il ritorno', async () => {
    negato = true
    monta()
    expect(await screen.findByRole('alert')).toHaveTextContent('Solo i revisori')
    expect(screen.getByRole('link', { name: 'Torna alle tue organizzazioni' })).toBeInTheDocument()
  })
})
