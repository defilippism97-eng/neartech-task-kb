// Client dell'API della piattaforma. Le richieste che cambiano dati portano l'intestazione della piattaforma
// (protezione contro le richieste da altri siti, vedi neartech.api.app).

export type Quadrante = 'q1' | 'q2' | 'q3' | 'q4'

export interface Ruolo {
  ruolo: string
  org_id: string | null
  codice: string | null
  nome: string | null
}

export interface Io {
  utente_id: string
  soggetto: string
  ruoli: Ruolo[]
}

export interface Ambiente {
  sso: boolean
  accesso_sviluppo?: boolean
}

export interface Occorrenza {
  occorrenza_id: string
  task_id: string
  task: string
  ruolo_id: string
  ruolo: string
  quadrante: Quadrante
  probabilita: number
  pari: boolean
  n: number
  n_dev: number
  d: number
  d_dev: number
  instabile: boolean | null
}

export interface RuoloRestituzione {
  ruolo_id: string
  ruolo: string
  occorrenze: number
  baricentro_n: number
  baricentro_d: number
  dispersione: number
  stabilita: number
  pesi_tempo: 'quote' | 'uguali'
  provvisorio: boolean
  quadranti: Record<Quadrante, number>
  instabili: number | null
}

export interface Restituzione {
  versione: string
  organizzazione: { org_id: string; nome: string; codice: string }
  nota: string
  chiavi: {
    rubriche: string[]
    profili: string[]
    soglie_quadranti: { profilo: string; theta_n: number; theta_d: number }[]
    snapshot: string[]
    metodi_capacita: string[]
    versioni_calcolo: string[]
    capacita: string[]
    componenti_d: string[]
    modelli_giudizi: string[]
  }
  soglia_stabilita: { valore: number; parametro_id: string; versione: number; comune: boolean } | null
  avvertenze: string[]
  riepilogo: {
    occorrenze: number
    con_risultato: number
    senza_risultato: number
    quadranti: Record<Quadrante, number>
    instabili: number | null
    pari: number
  }
  ruoli: RuoloRestituzione[]
  da_rivedere: Occorrenza[] | null
  occorrenze: Occorrenza[]
  impronta: string
  generato_il: string
  approvazione: number | null
}

export interface Avanzamento {
  totale: number
  voci: Record<string, { persone: number; totale: number }>
  quota: number
  occorrenze: Record<string, string[]>
}

export interface Panoramica {
  restituzione: Restituzione
  avanzamento: Avanzamento
}

export class ErroreApi extends Error {
  stato: number
  constructor(stato: number, messaggio: string) {
    super(messaggio)
    this.stato = stato
  }
}

async function richiesta<T>(percorso: string, opzioni: RequestInit = {}): Promise<T> {
  const scrive = opzioni.method && opzioni.method !== 'GET'
  const risposta = await fetch(percorso, {
    credentials: 'same-origin',
    ...opzioni,
    headers: {
      Accept: 'application/json',
      ...(scrive ? { 'Content-Type': 'application/json', 'X-Neartech-Richiesta': '1' } : {}),
      ...opzioni.headers,
    },
  })
  if (!risposta.ok) {
    let messaggio = risposta.statusText
    try {
      const dettaglio = (await risposta.json()).detail
      // FastAPI restituisce gli errori di validazione come elenco: il messaggio resta generico.
      messaggio = typeof dettaglio === 'string' ? dettaglio : 'dati non validi'
    } catch {
      // risposta senza corpo JSON
    }
    throw new ErroreApi(risposta.status, messaggio)
  }
  return risposta.json() as Promise<T>
}

export const api = {
  ambiente: () => richiesta<Ambiente>('/api/ambiente'),
  io: () => richiesta<Io>('/api/io'),
  panoramica: (codice: string) => richiesta<Panoramica>(`/api/organizzazioni/${encodeURIComponent(codice)}/panoramica`),
  approva: (codice: string, impronta: string, motivazione: string) =>
    richiesta<{ atto: number; impronta: string }>(
      `/api/organizzazioni/${encodeURIComponent(codice)}/restituzione/approvazione`,
      { method: 'POST', body: JSON.stringify({ impronta, motivazione }) },
    ),
  esci: () => richiesta<{ uscito: boolean }>('/accesso/esci', { method: 'POST' }),
  entraSviluppo: (soggetto: string) =>
    richiesta<{ entrato: boolean }>('/accesso/sviluppo', { method: 'POST', body: JSON.stringify({ soggetto }) }),
}

// Messaggi fissi dell'API per i due conflitti possibili sull'approvazione (neartech.api.app.ERRORI).
export const SUPERATA = 'i risultati sono cambiati dopo la lettura'
export const GIA_DECISA = 'decisione già presa'

// Gli errori che non cambiano riprovando (permessi, dati, conflitti) si mostrano subito.
export const riprova = (tentativi: number, errore: unknown) =>
  !(errore instanceof ErroreApi && errore.stato < 500) && tentativi < 2
