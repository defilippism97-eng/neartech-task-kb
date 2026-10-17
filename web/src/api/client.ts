// Client dell'API della piattaforma: richiesta con le credenziali della sessione e tipo di errore. Le richieste che
// cambiano dati portano l'intestazione della piattaforma (protezione contro le richieste da altri siti, vedi
// neartech.api.app). Lo usano tutti i moduli di area di questa cartella; le viste passano da `api` (index.ts).

export class ErroreApi extends Error {
  stato: number
  constructor(stato: number, messaggio: string) {
    super(messaggio)
    this.stato = stato
  }
}

export async function richiesta<T>(percorso: string, opzioni: RequestInit = {}): Promise<T> {
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

// Percorso delle rotte di un'organizzazione (/api/organizzazioni/<codice>), con il codice codificato.
export const org = (codice: string) => `/api/organizzazioni/${encodeURIComponent(codice)}`

// Messaggi fissi dell'API per i due conflitti possibili sull'approvazione (neartech.api.app.ERRORI).
export const SUPERATA = 'i risultati sono cambiati dopo la lettura'
export const GIA_DECISA = 'decisione già presa'

// Gli errori che non cambiano riprovando (permessi, dati, conflitti) si mostrano subito.
export const riprova = (tentativi: number, errore: unknown) =>
  !(errore instanceof ErroreApi && errore.stato < 500) && tentativi < 2
