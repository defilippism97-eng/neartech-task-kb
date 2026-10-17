import type { Fase, Percorso, StatoDocumento, StatoLotto } from './api'

// "Tocca a te": l'azione di ogni ruolo in ogni fase del percorso (registro di metodo, sezione 27).
// `pronta` dice se la schermata dell'azione esiste già: la piattaforma cresce a fette (docs/piani/fase-6-piattaforma.md).
// `rotta` porta alla schermata dell'azione, `comando` la esegue da qui.
// Testi: docs/piattaforma/voce-e-testi.md (voi per il comitato, tu per la persona).

export interface Azione {
  titolo: string
  testo: string
  pronta: boolean
  attesa?: boolean  // nessuna azione richiesta ora
  rotta?: 'indirizzi' | 'revisione' | 'documenti' | 'lotti'
  comando?: 'ricalcolo'
}

export const ETICHETTE_RUOLO: Record<string, string> = {
  comitato_guida: 'Comitato guida',
  revisore: 'Revisore',
  auditor: 'Auditor',
  amministratore_tecnico: 'Amministratore tecnico',
  rappresentante_lavoratori: 'Rappresentante dei lavoratori',
}

export const TITOLI_FASI: Record<Fase, string> = {
  avvio: 'Avvio',
  indirizzi: 'Indirizzi',
  verifica: 'Verifica',
  esito: 'Esito',
}

const plurale = (n: number, uno: string, molti: string) => `${n} ${n === 1 ? uno : molti}`

export const STATI_DOCUMENTO: Record<StatoDocumento, string> = {
  da_avviare: 'da avviare', in_coda: 'in coda', in_corso: 'in lavorazione', fatto: 'scomposto', fallito: 'non riuscito',
}

export const STATI_LOTTO: Record<StatoLotto, string> = {
  da_impostare: 'livello da scegliere', da_campionare: 'campione da estrarre', da_giudicare: 'campione da giudicare',
  da_misurare: 'precisione da calcolare', da_decidere: 'da decidere', deciso: 'deciso, da applicare',
  in_applicazione: 'in applicazione', applicato: 'applicato',
}

const ATTESA_RICALCOLO: Azione = { titolo: 'In attesa del ricalcolo', pronta: true, attesa: true,
  testo: 'Il profilo di pesi è attivo. L\'amministratore NEARTECH ricalcola la mappa con i nuovi pesi.' }

export function azione(ruolo: string, p: Percorso): Azione {
  const [avvio, indirizzi, verifica, esito] = p.fasi
  const fase = p.fase_corrente
  const proposta = indirizzi.fatti.proposta
  const senzaRisultati = fase === 'verifica' && verifica.fatti.risultati === 0
  const daConfermare = verifica.fatti.da_confermare ?? 0
  switch (ruolo) {
    case 'comitato_guida':
      if (fase === 'avvio') return { titolo: 'Seguite la lavorazione dei mansionari', pronta: true, attesa: true,
        testo: `${plurale(avvio.fatti.documenti, 'mansionario caricato', 'mansionari caricati')}, ${plurale(avvio.fatti.in_attesa_di_abbinamento, 'task', 'task')} in attesa di abbinamento. Nessuna azione richiesta ora.` }
      if (fase === 'indirizzi' && proposta?.approvata) return { titolo: 'In attesa della verifica dell\'auditor', pronta: true,
        attesa: true, rotta: 'indirizzi', testo: 'Avete approvato il profilo di pesi: diventa attivo con l\'ok dell\'auditor.' }
      if (fase === 'indirizzi' && proposta) return { titolo: 'Approvate il profilo proposto', pronta: true, rotta: 'indirizzi',
        testo: 'Le risposte al questionario hanno prodotto un profilo di pesi. Guardate l\'effetto sui task e approvatelo.' }
      if (fase === 'indirizzi') return { titolo: 'Date gli indirizzi', pronta: true, rotta: 'indirizzi',
        testo: 'Otto domande sulla vostra visione dell\'innovazione calibrano i pesi di D. Finché mancano, la mappa usa i pesi di default NEARTECH.' }
      if (senzaRisultati) return ATTESA_RICALCOLO
      if (fase === 'verifica') return { titolo: 'Esaminate le proposte di ricalibrazione', pronta: false,
        testo: `I revisori controllano a campione le classificazioni: ${daConfermare} risultati da confermare.` }
      if (esito.fatti.approvazione !== null) return { titolo: 'Restituzione approvata', pronta: true, attesa: true,
        testo: `Atto #${esito.fatti.approvazione} nel registro. Il percorso del pilota è concluso.` }
      return { titolo: 'Approvate la restituzione', pronta: true,
        testo: 'La mappa è pronta: leggetela e approvatela come atto del comitato.' }
    case 'revisore':
      if (fase === 'avvio' && avvio.fatti.in_attesa_di_abbinamento > 0) return { titolo: 'Decidi i lotti di abbinamento', pronta: true, rotta: 'lotti',
        testo: `${plurale(avvio.fatti.in_attesa_di_abbinamento, 'task aspetta', 'task aspettano')} la tua decisione, dal più ambiguo.` }
      if (senzaRisultati) return ATTESA_RICALCOLO
      if (fase === 'verifica') return { titolo: 'Controlla le classificazioni a campione', pronta: true, rotta: 'revisione',
        testo: `${daConfermare} risultati da confermare, dal più incerto. Ogni tuo giudizio sostituisce una stima del modello.` }
      return { titolo: 'Nessuna azione per te ora', pronta: true, attesa: true,
        testo: fase === 'indirizzi'
          ? 'Il comitato sta dando gli indirizzi. Dopo il ricalcolo controllerai a campione le classificazioni.'
          : 'Il lavoro di revisione di questa fase è concluso.' }
    case 'auditor':
      if (fase === 'indirizzi' && proposta?.approvata && !proposta.verificata) return { titolo: 'Verifica il profilo di pesi del comitato',
        pronta: true, rotta: 'indirizzi', testo: 'Il comitato ha approvato un profilo di pesi: controlla limiti ed effetto sui task e dai l\'ok.' }
      return { titolo: 'Segui il processo', pronta: true, attesa: true,
        testo: 'Ogni atto è nel registro, in catena. Quando il comitato approva un profilo di pesi, tocca a te verificarlo.' }
    case 'amministratore_tecnico':
      if (fase === 'avvio') return { titolo: 'Carica i mansionari e avvia l\'abbinamento', pronta: true, rotta: 'documenti',
        testo: 'Scomposizione e abbinamento usano chiamate a pagamento: la stima dei costi viene prima della conferma.' }
      if (senzaRisultati) return { titolo: 'Avvia il ricalcolo', pronta: true, comando: 'ricalcolo',
        testo: 'Il comitato e l\'auditor hanno attivato un nuovo profilo di pesi: ricalcola la mappa.' }
      return { titolo: 'Segui il processo', pronta: true, attesa: true, testo: 'Puoi intervenire in ogni fase.' }
    default:
      return { titolo: 'Segui il processo', pronta: true, attesa: true, testo: 'Nessuna azione richiesta ora.' }
  }
}

// --- Il percorso come tracciato a sigilli (docs/piattaforma/direzione-creativa.md, 2026-10-17) -----------------
// Il lavoro scorre sulle tratte, calcolate dai fatti del motore; si passa da una fase all'altra solo con un sigillo,
// l'atto di una persona. Nessun dato nuovo dall'API e nessuna soglia: solo rapporti tra fatti di `Percorso`.

export type StatoMostrato = 'fatta' | 'in_corso' | 'anticipo' | 'da_fare'
export type Sigillo = { etichetta: string; stato: 'posto' | 'atteso' | 'vuoto' }

export const ETICHETTE_STATO_FASE: Record<StatoMostrato, string> = {
  fatta: 'fatta', in_corso: 'in corso', anticipo: 'in anticipo', da_fare: 'da fare',
}

export const indiceCorrente = (p: Percorso) => p.fasi.findIndex((f) => f.codice === p.fase_corrente)
export const concluso = (p: Percorso) => p.fasi[3].fatti.approvazione !== null

/** Una fase in corso dopo quella corrente è «in anticipo»: i suoi risultati sono provvisori. */
export function statoMostrato(p: Percorso, i: number): StatoMostrato {
  const f = p.fasi[i]
  return f.stato === 'in_corso' && i > indiceCorrente(p) ? 'anticipo' : f.stato
}

/** Riempimento della tratta, 0–1: fatta piena, da fare vuota, in corso secondo i fatti. */
export function progressoFase(p: Percorso, i: number): number {
  const f = p.fasi[i]
  if (f.stato === 'fatta') return 1
  if (f.stato === 'da_fare') return 0
  switch (f.codice) {
    case 'avvio': return f.fatti.attivita > 0 ? (f.fatti.attivita - f.fatti.in_attesa_di_abbinamento) / f.fatti.attivita : 0
    case 'indirizzi': {
      if (f.fatti.profilo_proprio) return 1
      const q = f.fatti.proposta
      return [q !== null, q?.approvata, q?.verificata].filter(Boolean).length / 3
    }
    case 'verifica': {
      const { risultati, da_confermare } = f.fatti
      return risultati > 0 && da_confermare !== null ? (risultati - da_confermare) / risultati : 0
    }
    case 'esito': return f.fatti.approvazione !== null ? 1 : 0
  }
}

/** Posizione di «oggi» dentro la tratta corrente: mai attaccata ai bordi, così resta leggibile. */
export const progressoOggi = (p: Percorso) => Math.min(0.92, Math.max(0.08, progressoFase(p, indiceCorrente(p))))

const percento = (x: number) => `${Math.round(x * 100)}%`

/** La riga «prova»: passato = prove, presente = avanzamento, futuro = che cosa succederà. */
export function provaFase(p: Percorso, i: number): string {
  const stato = statoMostrato(p, i)
  const [avvio, indirizzi, verifica, esito] = p.fasi
  switch (p.fasi[i].codice) {
    case 'avvio': {
      const f = avvio.fatti
      if (stato === 'da_fare' || f.documenti === 0) return 'Nessun mansionario caricato'
      if (stato === 'fatta') return `${plurale(f.documenti, 'mansionario', 'mansionari')} · ${f.occorrenze} task nella mappa`
      return `${plurale(f.documenti, 'mansionario', 'mansionari')} · ${f.in_attesa_di_abbinamento} task in attesa di abbinamento`
    }
    case 'indirizzi': {
      const f = indirizzi.fatti
      if (stato === 'da_fare') return 'Il questionario del comitato calibra i pesi di D'
      if (stato === 'fatta') return 'Profilo di pesi del comitato in vigore'
      if (f.proposta?.approvata) return 'Profilo approvato dal comitato'
      if (f.proposta) return 'Profilo di pesi proposto dal questionario'
      return 'Mappa con i pesi di default NEARTECH'
    }
    case 'verifica': {
      const f = verifica.fatti
      const confermare = f.da_confermare === null ? '' : ` · ${f.da_confermare} da confermare`
      if (stato === 'da_fare') return 'I revisori controllano a campione le classificazioni'
      if (stato === 'anticipo') return `${plurale(f.risultati, 'risultato provvisorio', 'risultati provvisori')}${confermare}`
      if (stato === 'fatta') return `${plurale(f.risultati, 'risultato stabile', 'risultati stabili')} · ${percento(f.quota_giudizi_di_persona)} giudizi di persona`
      if (f.risultati === 0) return 'Ricalcolo con il nuovo profilo in attesa'
      if (f.da_confermare === null) return `${plurale(f.risultati, 'risultato', 'risultati')} · stabilità da misurare`
      return `${plurale(f.risultati, 'risultato', 'risultati')}${confermare} · ${percento(f.quota_giudizi_di_persona)} giudizi di persona`
    }
    case 'esito':
      if (stato === 'da_fare') return 'Il comitato approva la restituzione come atto'
      if (stato === 'fatta') return `Atto #${esito.fatti.approvazione} nel registro · impronta ${esito.fatti.impronta.slice(0, 8)}…`
      return 'Mappa pronta da approvare'
  }
}

/** La riga «sigillo»: l'atto che chiude la fase, posto, atteso da qualcuno, o che verrà. */
export function sigilloFase(p: Percorso, i: number): { testo: string; sigilli: Sigillo[] } {
  const stato = statoMostrato(p, i)
  const f = p.fasi[i]
  const uno = (s: Sigillo['stato'], testo: string) => ({ testo, sigilli: [{ etichetta: '', stato: s }] })
  switch (f.codice) {
    case 'avvio':
      if (stato === 'fatta') return uno('posto', '✓ Abbinamenti applicati')
      if (stato === 'da_fare') return uno('vuoto', 'Poi: il revisore decide gli abbinamenti')
      return uno('atteso', 'Attende: il revisore, sui lotti')
    case 'indirizzi': {
      const q = f.fatti.proposta
      const comitato = stato === 'fatta' || !!q?.approvata
      const auditor = stato === 'fatta' || !!q?.verificata
      const sigilli: Sigillo[] = [
        { etichetta: 'C', stato: comitato ? 'posto' : stato === 'da_fare' ? 'vuoto' : 'atteso' },
        { etichetta: 'A', stato: auditor ? 'posto' : comitato ? 'atteso' : 'vuoto' },
      ]
      if (stato === 'fatta') return { testo: '✓ Comitato · ✓ Auditor', sigilli }
      if (stato === 'da_fare') return { testo: 'Poi: approvazione del comitato e verifica dell\'auditor', sigilli }
      if (comitato) return { testo: '✓ Comitato · attende: l\'auditor', sigilli }
      if (q) return { testo: 'Attende: il comitato, poi l\'auditor', sigilli }
      return { testo: 'Attende: il comitato, sul questionario', sigilli }
    }
    case 'verifica':
      if (stato === 'fatta') return uno('posto', '✓ Nessun risultato da confermare')
      if (stato === 'da_fare') return uno('vuoto', 'Poi: nessun risultato da confermare')
      if (stato === 'anticipo') return uno('vuoto', 'Si chiude dopo gli indirizzi')
      if (f.fatti.risultati === 0) return uno('atteso', 'Attende: l\'amministratore NEARTECH')
      if (f.fatti.da_confermare === null) return uno('atteso', 'Attende: la soglia di stabilità del comitato')
      return uno('atteso', 'Attende: i revisori')
    case 'esito':
      if (stato === 'fatta') return uno('posto', '✓ Restituzione approvata')
      if (stato === 'da_fare') return uno('vuoto', 'Poi: atto nel registro, con impronta')
      return uno('atteso', 'Attende: il comitato')
  }
}

/** Chi deve agire adesso, per la banda in attesa. */
export function chiAgisce(p: Percorso): string {
  const [avvio, indirizzi, verifica] = p.fasi
  switch (p.fase_corrente) {
    case 'avvio': return avvio.fatti.documenti === 0 || avvio.fatti.in_attesa_di_abbinamento === 0
      ? 'l\'amministratore NEARTECH' : 'il revisore'
    case 'indirizzi': return indirizzi.fatti.proposta?.approvata && !indirizzi.fatti.proposta.verificata
      ? 'l\'auditor' : 'il comitato guida'
    case 'verifica': return verifica.fatti.risultati === 0 ? 'l\'amministratore NEARTECH' : 'i revisori'
    case 'esito': return 'il comitato guida'
  }
}
