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

export type Fase = 'avvio' | 'indirizzi' | 'verifica' | 'esito'
export type StatoFase = 'fatta' | 'in_corso' | 'da_fare'

export interface Percorso {
  fase_corrente: Fase
  fasi: [
    { codice: 'avvio'; stato: StatoFase; fatti: { documenti: number; attivita: number; in_attesa_di_abbinamento: number; occorrenze: number } },
    { codice: 'indirizzi'; stato: StatoFase; fatti: { profilo_proprio: string | null; profilo_in_uso: string | null;
      proposta: { profile_id: string; approvata: boolean; verificata: boolean } | null } },
    { codice: 'verifica'; stato: StatoFase; fatti: { risultati: number; da_confermare: number | null; quota_giudizi_di_persona: number } },
    { codice: 'esito'; stato: StatoFase; fatti: { approvazione: number | null; impronta: string } },
  ]
}

export interface Panoramica {
  restituzione: Restituzione
  avanzamento: Avanzamento
  percorso: Percorso
}

export interface Domanda {
  codice: string
  voce: 'd1' | 'd2' | 'd3' | 'd4'
  verso: 1 | -1
  testo: string
}

export interface StatoIndirizzi {
  questionario: { versione: string; risposte: string[]; domande: Domanda[]; limiti: { min: number; max: number } } | null
  pesi_in_uso: { profilo: string; pesi: Record<string, number> }
  profilo: {
    profile_id: string
    attivo: boolean
    pesi: Record<string, number>
    approvato: number | null
    verificato: number | null
    controlli: { codice: string; esito: boolean; descrizione: string }[]
    effetto: { quadranti: Record<Quadrante, number>; cambiano_quadrante: number; occorrenze: number } | null
  } | null
}

export interface VoceRubrica {
  codice: string
  nome: string
  asse: 'N' | 'D'
  livelli: string[]
}

export interface Revisione {
  rubrica: { versione: string; voci: VoceRubrica[] }
  coda: {
    task_id: string
    task: string
    ruoli: string | null
    certezza: number
    stime_modello: Record<string, number>
    miei_giudizi: Record<string, number>
    voci_con_giudizi_di_persona: string[]
  }[]
}

export interface Stima {
  token_ingresso: number
  token_uscita: number
  costo: number
  costo_massimo: number
}

export type StatoDocumento = 'da_avviare' | 'in_coda' | 'in_corso' | 'fatto' | 'fallito'
export type StatoLotto = 'da_impostare' | 'da_campionare' | 'da_giudicare' | 'da_misurare' | 'da_decidere' | 'deciso'
  | 'in_applicazione' | 'applicato'

export interface Lotto {
  lotto_id: string
  creato_il: string
  proposte: number
  con_task: number
  livello: 'campione' | 'completa' | 'nulla' | null
  stato: StatoLotto
  campione_id: string | null
  dimensione_campione: number | null
  giudicati: number
  esito_misura: string | null
}

export interface Pipeline {
  prezzi: { parametro_id: string; versione: number; modello: string; ingresso_eur_mtok: number; uscita_eur_mtok: number } | null
  documenti: {
    caricamento_id: string
    nome_file: string
    ruolo: string
    caratteri: number
    caricato_il: string
    stato: StatoDocumento
    errore: string | null
    candidati: number
    stima: Stima | null
  }[]
  stima_da_avviare: Stima | null
  candidati_da_proporre: number
  proposta_in_coda: boolean
  lotti: Lotto[]
  lavori: { job_id: string; tipo: string; stato: StatoDocumento; tentativi: number; errore: string | null; creato_il: string }[]
}

export type EsitoCampione = 'corretto' | 'parziale' | 'errato'

export interface DettaglioLotto {
  lotto: Lotto
  campione: {
    istruzioni: string
    elementi: { posizione: number; candidato: string; task: string; proposta: string; mio_esito: EsitoCampione | null }[]
    misura: { n_elementi: number; n_corretti: number; n_parziali: number; n_errati: number; precisione: number; esito: string } | null
  } | null
  proposte: { proposta_id: string; candidato: string; task_id: string | null; task_proposto: string | null; distanza: number | null; margine: number | null }[] | null
}

export interface Organizzazione {
  codice: string
  nome: string
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

const org = (codice: string) => `/api/organizzazioni/${encodeURIComponent(codice)}`

export const api = {
  ambiente: () => richiesta<Ambiente>('/api/ambiente'),
  io: () => richiesta<Io>('/api/io'),
  organizzazioni: () => richiesta<Organizzazione[]>('/api/organizzazioni'),
  panoramica: (codice: string) => richiesta<Panoramica>(`/api/organizzazioni/${encodeURIComponent(codice)}/panoramica`),
  approva: (codice: string, impronta: string, motivazione: string) =>
    richiesta<{ atto: number; impronta: string }>(
      `/api/organizzazioni/${encodeURIComponent(codice)}/restituzione/approvazione`,
      { method: 'POST', body: JSON.stringify({ impronta, motivazione }) },
    ),
  indirizzi: (codice: string) => richiesta<StatoIndirizzi>(`/api/organizzazioni/${encodeURIComponent(codice)}/indirizzi`),
  rispondi: (codice: string, risposte: Record<string, number>, nota: string) =>
    richiesta<{ profile_id: string }>(`/api/organizzazioni/${encodeURIComponent(codice)}/indirizzi/risposte`,
      { method: 'POST', body: JSON.stringify({ risposte, nota }) }),
  decidiProfilo: (codice: string, profilo: string, atto: 'approvazione' | 'verifica', motivazione: string) =>
    richiesta<{ atto: number }>(
      `/api/organizzazioni/${encodeURIComponent(codice)}/indirizzi/${encodeURIComponent(profilo)}/${atto}`,
      { method: 'POST', body: JSON.stringify({ motivazione }) }),
  revisione: (codice: string) => richiesta<Revisione>(`/api/organizzazioni/${encodeURIComponent(codice)}/revisione`),
  giudica: (codice: string, task_id: string, voce: string, valore: number, nota: string) =>
    richiesta<{ atto: number }>(`/api/organizzazioni/${encodeURIComponent(codice)}/revisione/giudizi`,
      { method: 'POST', body: JSON.stringify({ task_id, voce, valore, nota }) }),
  documenti: (codice: string) => richiesta<Pipeline>(`${org(codice)}/documenti`),
  caricaDocumento: (codice: string, nome_file: string, contenuto: string) =>
    richiesta<{ caricamento_id: string; nuovo: boolean; ruolo: string }>(`${org(codice)}/documenti`,
      { method: 'POST', body: JSON.stringify({ nome_file, contenuto }) }),
  avviaScomposizione: (codice: string, caricamenti: string[], motivazione: string) =>
    richiesta<{ atto: number } & Stima>(`${org(codice)}/documenti/scomposizione`,
      { method: 'POST', body: JSON.stringify({ caricamenti, motivazione }) }),
  proponiLotto: (codice: string, motivazione: string) =>
    richiesta<{ atto: number }>(`${org(codice)}/abbinamenti/proposta`, { method: 'POST', body: JSON.stringify({ motivazione }) }),
  applicaLotto: (codice: string, lotto: string, motivazione: string) =>
    richiesta<{ atto: number }>(`${org(codice)}/lotti/${encodeURIComponent(lotto)}/applicazione`,
      { method: 'POST', body: JSON.stringify({ motivazione }) }),
  lotti: (codice: string) => richiesta<Lotto[]>(`${org(codice)}/lotti`),
  lotto: (codice: string, lotto: string) => richiesta<DettaglioLotto>(`${org(codice)}/lotti/${encodeURIComponent(lotto)}`),
  azioneLotto: (codice: string, lotto: string, azione: 'livello' | 'campione' | 'giudizi' | 'misura' | 'decisione', corpo: object = {}) =>
    richiesta<unknown>(`${org(codice)}/lotti/${encodeURIComponent(lotto)}/${azione}`, { method: 'POST', body: JSON.stringify(corpo) }),
  ricalcola: (codice: string) =>
    richiesta<{ nuove: number }>(`/api/organizzazioni/${encodeURIComponent(codice)}/calcolo`, { method: 'POST' }),
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
