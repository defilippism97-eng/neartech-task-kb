import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, RouterProvider } from '@tanstack/react-router'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { DettaglioLotto, Lotto, Pipeline } from '../api'
import { creaRouter } from '../rotte'

const lotto = (stato: Lotto['stato']): Lotto => ({
  lotto_id: 'aaaaaaaa-0000-0000-0000-000000000001', creato_il: '2026-10-17T10:00:00Z', proposte: 3, con_task: 3,
  livello: stato === 'da_impostare' ? null : 'campione', stato, campione_id: stato === 'da_impostare' ? null : 'c1',
  dimensione_campione: 2, giudicati: 0, esito_misura: null,
})

const pipeline = (sovrascrivi: Partial<Pipeline> = {}): Pipeline => ({
  prezzi: { parametro_id: 'p', versione: 1, modello: 'claude-sonnet-5-5', ingresso_eur_mtok: 3, uscita_eur_mtok: 15 },
  documenti: [{ caricamento_id: 'd1', nome_file: 'tesoreria.docx', ruolo: 'Addetto tesoreria', caratteri: 900,
    caricato_il: '2026-10-17T10:00:00Z', stato: 'da_avviare', errore: null, candidati: 0,
    stima: { token_ingresso: 1200, token_uscita: 700, costo: 0.0141, costo_massimo: 0.0282 } }],
  stima_da_avviare: { token_ingresso: 1200, token_uscita: 700, costo: 0.0141, costo_massimo: 0.0282 },
  candidati_da_proporre: 0, proposta_in_coda: false, lotti: [], lavori: [], ...sovrascrivi,
})

describe('documenti e lotti', () => {
  let chiamate: { url: string; init?: RequestInit }[]
  let risposte: Record<string, unknown>
  let ruolo: string

  beforeEach(() => {
    chiamate = []
    ruolo = 'amministratore_tecnico'
    risposte = {}
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
      chiamate.push({ url, init })
      const corpo = url === '/api/io'
        ? { utente_id: 'u', soggetto: 'prova', ruoli: [{ ruolo, org_id: null, codice: null, nome: null }] }
        : url === '/api/organizzazioni' ? [{ codice: 'acme', nome: 'ACME S.p.A.' }]
          : init?.method === 'POST' ? { atto: 5 }
            : risposte[url]
      return new Response(JSON.stringify(corpo), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }))
  })
  afterEach(() => vi.unstubAllGlobals())

  const monta = (percorso: string) => {
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <RouterProvider router={creaRouter(createMemoryHistory({ initialEntries: [percorso] }))} />
      </QueryClientProvider>,
    )
  }

  it('mostra la stima e avvia la scomposizione solo con una motivazione', async () => {
    risposte['/api/organizzazioni/acme/documenti'] = pipeline()
    monta('/app/org/acme/documenti')
    expect(await screen.findByRole('heading', { name: '1 mansionario da scomporre' })).toBeInTheDocument()
    expect(screen.getByText('Costo stimato').nextSibling).toHaveTextContent('0,014')
    const avvia = screen.getByRole('button', { name: 'Conferma la stima e avvia' })
    expect(avvia).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Conferma della stima'), { target: { value: 'avvio del pilota' } })
    fireEvent.click(avvia)
    await waitFor(() => expect(chiamate.some((c) => c.url.endsWith('/documenti/scomposizione'))).toBe(true))
    const invio = chiamate.find((c) => c.url.endsWith('/documenti/scomposizione'))!
    expect(JSON.parse(String(invio.init?.body))).toEqual({ caricamenti: ['d1'], motivazione: 'avvio del pilota' })
  })

  it('senza prezzi approvati spiega che la stima viene prima', async () => {
    risposte['/api/organizzazioni/acme/documenti'] = pipeline({ prezzi: null, stima_da_avviare: null })
    monta('/app/org/acme/documenti')
    expect(await screen.findByRole('note')).toHaveTextContent('prezzi_scomposizione')
    expect(screen.queryByRole('button', { name: 'Conferma la stima e avvia' })).not.toBeInTheDocument()
  })

  it('il revisore giudica il campione senza vedere distanze', async () => {
    ruolo = 'revisore'
    const l = lotto('da_giudicare')
    risposte['/api/organizzazioni/acme/lotti'] = [l]
    risposte[`/api/organizzazioni/acme/lotti/${l.lotto_id}`] = {
      lotto: l, proposte: null,
      campione: { istruzioni: 'istruzioni-abbinamento-v1', misura: null, elementi: [
        { posizione: 1, candidato: 'Riconciliazioni bancarie giornaliere', task: 'Riconciliazioni bancarie', proposta: 'stesso task', mio_esito: null },
      ] },
    } satisfies DettaglioLotto
    monta('/app/org/acme/lotti')
    expect(await screen.findByRole('heading', { name: '0 di 2 coppie giudicate' })).toBeInTheDocument()
    const gruppo = await screen.findByRole('group', { name: 'Giudizio sulla coppia 1' })
    expect(screen.queryByText(/distanza/)).not.toBeInTheDocument()
    fireEvent.click(gruppo.querySelector('button')!)
    await waitFor(() => expect(chiamate.some((c) => c.url.endsWith('/giudizi'))).toBe(true))
    expect(JSON.parse(String(chiamate.find((c) => c.url.endsWith('/giudizi'))!.init?.body))).toEqual({ posizione: 1, esito: 'corretto' })
  })

  it('senza lotti il revisore sa da dove arriveranno', async () => {
    ruolo = 'revisore'
    risposte['/api/organizzazioni/acme/lotti'] = []
    monta('/app/org/acme/lotti')
    expect(await screen.findByRole('heading', { name: 'Ancora nessun lotto' })).toBeInTheDocument()
  })
})
