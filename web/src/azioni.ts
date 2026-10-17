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

export const SOTTOTITOLI_FASI: Record<Fase, string> = {
  avvio: 'Mansionari scomposti e abbinati',
  indirizzi: 'La visione del comitato calibra i pesi',
  verifica: 'Ricalcolo e controllo a campione',
  esito: 'Restituzione approvata',
}

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
        testo: `${avvio.fatti.documenti} documenti caricati, ${avvio.fatti.in_attesa_di_abbinamento} attività in attesa di abbinamento. Nessuna azione richiesta ora.` }
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
        testo: `${avvio.fatti.in_attesa_di_abbinamento} attività aspettano la tua decisione, dalla più ambigua.` }
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
