import type { Panoramica } from './api'

// Gli avvisi della restituzione diventano inviti all'azione: la sperimentazione avanza, non si blocca
// (registro di metodo, sezione 27). Testi: docs/piattaforma/voce-e-testi.md (titolo con il dato, testo con la
// conseguenza).

export interface Invito {
  icona: string
  colore: [string, string]
  titolo: string
  testo: string
}

const percento = (x: number | undefined) => `${Math.round((x ?? 0) * 100)}%`

export function inviti(dati: Panoramica): Invito[] {
  const r = dati.restituzione
  const elenco: Invito[] = []
  const incerti = r.da_rivedere?.length ?? 0
  if (incerti > 0) {
    elenco.push({ icona: String(incerti), colore: ['#FEF3C7', 'var(--amber-ink)'],
      titolo: incerti === 1 ? '1 risultato da confermare' : `${incerti} risultati da confermare`,
      testo: `Il quadrante più probabile non arriva al ${percento(r.soglia_stabilita?.valore)} delle simulazioni. ` +
        'Ogni giudizio dei revisori lo rende più stabile.' })
  }
  const avvisi = new Set(r.avvertenze)
  if (avvisi.has('soglia_di_stabilita_non_approvata')) {
    elenco.push({ icona: 'θ', colore: ['#F1E9F9', 'var(--violet)'], titolo: 'Fissate la soglia di stabilità',
      testo: 'Senza soglia non si distinguono i risultati solidi da quelli da confermare.' })
  } else if (avvisi.has('soglia_comune_non_adottata')) {
    elenco.push({ icona: percento(r.soglia_stabilita?.valore), colore: ['#F1E9F9', 'var(--violet)'],
      titolo: 'Fate vostra la soglia di stabilità',
      testo: `Oggi vale il ${percento(r.soglia_stabilita?.valore)} proposto da NEARTECH. Il comitato può adottarlo o fissarne uno proprio.` })
  }
  if (avvisi.has('d_provvisorio')) {
    const presenti = r.chiavi.componenti_d.length
    elenco.push({ icona: `${presenti}/4`, colore: ['#E6FAFA', 'var(--teal-ink)'],
      titolo: `D si basa su ${presenti} componenti su 4`,
      testo: 'Mancano senso del lavoro e valore per chi riceve il servizio. Si raccolgono con un questionario via email a operatori e utenti.' })
  }
  if (avvisi.has('pesi_uguali')) {
    elenco.push({ icona: '%', colore: ['#EEF2F9', 'var(--navy)'], titolo: 'Ogni task pesa uguale nel suo ruolo',
      testo: 'Indicate quanto tempo occupa ciascun task e il baricentro dei ruoli diventa preciso.' })
  }
  if (avvisi.has('capacita_di_riserva')) {
    elenco.push({ icona: 'IA', colore: ['#EEF2F9', 'var(--navy)'], titolo: 'Capacità dell\'IA: stima documentale',
      testo: 'Ogni valore ha fonte e data. Diventa una misura quando arrivano i test sul campo.' })
  }
  return elenco
}
