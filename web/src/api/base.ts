// API di base: ambiente, utente corrente, organizzazioni visibili, accesso e uscita (neartech.api.rotte.base,
// neartech.api.accesso).
import { richiesta } from './client'
import type { Io, Organizzazione } from './tipi'

export interface Ambiente {
  sso: boolean
  accesso_sviluppo?: boolean
}

export const base = {
  ambiente: () => richiesta<Ambiente>('/api/ambiente'),
  io: () => richiesta<Io>('/api/io'),
  organizzazioni: () => richiesta<Organizzazione[]>('/api/organizzazioni'),
  esci: () => richiesta<{ uscito: boolean }>('/accesso/esci', { method: 'POST' }),
  entraSviluppo: (soggetto: string) =>
    richiesta<{ entrato: boolean }>('/accesso/sviluppo', { method: 'POST', body: JSON.stringify({ soggetto }) }),
}
