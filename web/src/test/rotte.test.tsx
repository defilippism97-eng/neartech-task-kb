import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, RouterProvider } from '@tanstack/react-router'
import { render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MODULI_API } from '../api'
import { creaRouter, VOCI } from '../rotte'
import { TUTTI_I_RUOLI } from '../rotte/tipi'

// Albero delle rotte (sito pubblico alla radice, applicazione sotto /app), registro delle voci del guscio e moduli
// del client: le parti condivise del cantiere per aree (docs/piani/fase-6-cantiere.md).

describe('sito pubblico e applicazione', () => {
  let chiamate: string[]
  let sessione: boolean

  beforeEach(() => {
    chiamate = []
    sessione = true
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      chiamate.push(url)
      if (url === '/api/io' && !sessione) {
        return new Response(JSON.stringify({ detail: 'accesso richiesto' }), { status: 401, headers: { 'Content-Type': 'application/json' } })
      }
      const corpo = url === '/api/io'
        ? { utente_id: 'u', soggetto: 'prova|revisore', ruoli: [{ ruolo: 'revisore', org_id: 'o1', codice: 'acme', nome: 'ACME S.p.A.' }] }
        : url === '/api/ambiente' ? { sso: false, accesso_sviluppo: true }
          : url === '/api/organizzazioni' ? [{ codice: 'acme', nome: 'ACME S.p.A.' }]
            : []
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

  it('la radice è del sito pubblico e non chiede l\'accesso', async () => {
    monta('/')
    expect(await screen.findByRole('heading', { name: 'Neartech' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Accedi alla piattaforma' })).toHaveAttribute('href', '/app')
    expect(chiamate).not.toContain('/api/io')
  })

  it('sotto /app senza sessione si vede l\'accesso', async () => {
    sessione = false
    monta('/app')
    expect(await screen.findByRole('heading', { name: 'Accedi alla tua organizzazione' })).toBeInTheDocument()
  })

  it('il guscio mostra solo le voci del ruolo, senza voci in arrivo', async () => {
    monta('/app/org/acme/lotti')
    expect(await screen.findByRole('heading', { name: 'Ancora nessun lotto' })).toBeInTheDocument()
    const sezioni = screen.getByRole('navigation', { name: 'Sezioni' })
    expect(within(sezioni).getAllByRole('link').map((l) => l.textContent?.trim()))
      .toEqual(['Panoramica', 'Indirizzi', 'Revisione', 'Lotti'])
    expect(within(sezioni).getByRole('link', { name: 'Lotti' })).toHaveAttribute('href', '/app/org/acme/lotti')
    expect(screen.queryByText('In arrivo')).not.toBeInTheDocument()
  })
})

describe('registri delle aree', () => {
  it('ogni voce del guscio indica ruoli esistenti', () => {
    for (const voce of VOCI) {
      expect(voce.ruoli.length).toBeGreaterThan(0)
      expect(voce.ruoli.filter((r) => !TUTTI_I_RUOLI.includes(r))).toEqual([])
    }
    expect(new Set(VOCI.map((v) => v.to)).size).toBe(VOCI.length)
  })

  it('nessuna funzione del client ha lo stesso nome in due moduli', () => {
    const nomi = Object.values(MODULI_API).flatMap((modulo) => Object.keys(modulo))
    expect(nomi.filter((nome, i) => nomi.indexOf(nome) !== i)).toEqual([])
  })
})
