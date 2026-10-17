import type { Fase, Percorso } from './api'

// "Tocca a te": l'azione di ogni ruolo in ogni fase del percorso (registro di metodo, sezione 27).
// `pronta` dice se la schermata dell'azione esiste già: la piattaforma cresce a fette (docs/piani/fase-6-piattaforma.md).
// Testi: docs/piattaforma/voce-e-testi.md (voi per il comitato, tu per la persona).

export interface Azione {
  titolo: string
  testo: string
  pronta: boolean
  attesa?: boolean  // nessuna azione richiesta ora
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

export function azione(ruolo: string, p: Percorso): Azione {
  const [avvio, , verifica, esito] = p.fasi
  const fase = p.fase_corrente
  const daConfermare = verifica.fatti.da_confermare ?? 0
  switch (ruolo) {
    case 'comitato_guida':
      if (fase === 'avvio') return { titolo: 'Seguite la lavorazione dei mansionari', pronta: true, attesa: true,
        testo: `${avvio.fatti.documenti} documenti caricati, ${avvio.fatti.in_attesa_di_abbinamento} attività in attesa di abbinamento. Nessuna azione richiesta ora.` }
      if (fase === 'indirizzi') return { titolo: 'Date gli indirizzi', pronta: false,
        testo: 'Un questionario sulla vostra visione dell\'innovazione calibra i pesi di D. Finché manca, la mappa usa i pesi di default NEARTECH.' }
      if (fase === 'verifica') return { titolo: 'Esaminate le proposte di ricalibrazione', pronta: false,
        testo: `I revisori controllano a campione le classificazioni: ${daConfermare} risultati da confermare.` }
      if (esito.fatti.approvazione !== null) return { titolo: 'Restituzione approvata', pronta: true, attesa: true,
        testo: `Atto #${esito.fatti.approvazione} nel registro. Il percorso del pilota è concluso.` }
      return { titolo: 'Approvate la restituzione', pronta: true,
        testo: 'La mappa è pronta: leggetela e approvatela come atto del comitato.' }
    case 'revisore':
      if (fase === 'avvio' && avvio.fatti.in_attesa_di_abbinamento > 0) return { titolo: 'Decidi i lotti di abbinamento', pronta: false,
        testo: `${avvio.fatti.in_attesa_di_abbinamento} attività aspettano la tua decisione, dalla più ambigua.` }
      if (fase === 'verifica') return { titolo: 'Controlla le classificazioni a campione', pronta: false,
        testo: `${daConfermare} risultati da confermare, dal più incerto. Ogni tuo giudizio sostituisce una stima del modello.` }
      return { titolo: 'Nessuna azione per te ora', pronta: true, attesa: true,
        testo: fase === 'indirizzi'
          ? 'Il comitato sta dando gli indirizzi. Dopo il ricalcolo controllerai a campione le classificazioni.'
          : 'Il lavoro di revisione di questa fase è concluso.' }
    case 'auditor':
      return { titolo: fase === 'indirizzi' ? 'Verifica il profilo di pesi del comitato' : 'Segui il processo',
        pronta: fase !== 'indirizzi', attesa: fase !== 'indirizzi',
        testo: fase === 'indirizzi'
          ? 'Quando il comitato approva il profilo di pesi, tocca a te dare l\'ok: nessun task sotto il pavimento legale.'
          : 'Ogni atto è nel registro, in catena: puoi verificarlo in qualsiasi momento.' }
    case 'amministratore_tecnico':
      if (fase === 'avvio') return { titolo: 'Carica i mansionari e avvia l\'abbinamento', pronta: false,
        testo: 'Scomposizione e abbinamento usano chiamate a pagamento: la stima dei costi viene prima della conferma.' }
      if (fase === 'verifica') return { titolo: 'Avvia il ricalcolo', pronta: false,
        testo: 'Dopo gli indirizzi del comitato, il calcolo usa il nuovo profilo di pesi.' }
      return { titolo: 'Segui il processo', pronta: true, attesa: true, testo: 'Puoi intervenire in ogni fase dal pannello di amministrazione.' }
    default:
      return { titolo: 'Segui il processo', pronta: true, attesa: true, testo: 'Nessuna azione richiesta ora.' }
  }
}
