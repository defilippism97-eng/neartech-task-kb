// Tipi del JSON dell'API usati da più aree (restituzione, percorso, lotti, utente). I tipi di una sola area stanno
// nel modulo dell'area; index.ts li riesporta tutti.

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

export interface Organizzazione {
  codice: string
  nome: string
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
