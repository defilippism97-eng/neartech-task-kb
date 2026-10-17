import type { ToOptions } from '@tanstack/react-router'
import { ETICHETTE_RUOLO } from '../azioni'
import type { NomeIcona } from '../componenti/Icona'

// Pagine di un'organizzazione (/app/org/$codice/<vista>): le sole che il guscio elenca, con il codice corrente.
export type PercorsoOrganizzazione = Extract<NonNullable<ToOptions['to']>, `/app/org/$codice/${string}`>

// Voce della navigazione laterale (Guscio). Ogni file di area in questa cartella esporta le sue `voci`; il guscio
// mostra quelle che hanno fra i `ruoli` il ruolo corrente, raggruppate per `gruppo` (predefinito: GRUPPO_LAVORO),
// nell'ordine delle aree in index.tsx. `to` è il percorso completo di una rotta registrata, controllato da tsc.
export interface VoceNav {
  to: PercorsoOrganizzazione
  etichetta: string
  icona: NomeIcona
  ruoli: string[]
  gruppo?: string
}

export const GRUPPO_LAVORO = 'Lavoro'

// Tutti i ruoli della piattaforma (tabella ruoli, migrazione 0008), per le voci che vede chiunque.
export const TUTTI_I_RUOLI = Object.keys(ETICHETTE_RUOLO)
