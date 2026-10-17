// Icone a tratto della piattaforma (24×24, tratto 1.8, colore del testo). Disegnate qui: nessuna libreria in più.
// Decorative: chi le usa mette accanto il testo, quindi sono nascoste alle tecnologie assistive.

const TRATTI = {
  panoramica: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.5" /></>,
  indirizzi: <><circle cx="12" cy="12" r="8.5" /><path d="m15.5 8.5-2 5-5 2 2-5z" /></>,
  revisione: <><rect x="3.5" y="3.5" width="17" height="17" rx="3" /><path d="m8 12 3 3 5-6" /></>,
  lotti: <><path d="m12 3.5 8.5 4.5-8.5 4.5L3.5 8z" /><path d="m3.5 12 8.5 4.5 8.5-4.5" /><path d="m3.5 16 8.5 4.5 8.5-4.5" /></>,
  documenti: <><path d="M6 3.5h8l4.5 4.5v12.5H6z" /><path d="M14 3.5V8h4.5M9 13h6M9 16.5h6" /></>,
  ruoli: <><circle cx="9" cy="8.5" r="3.5" /><path d="M3.5 19.5c.8-3.3 3-5 5.5-5s4.7 1.7 5.5 5" /><path d="M15.5 5.5a3.2 3.2 0 0 1 0 6.2M17.5 14.8c1.6.7 2.6 2.3 3 4.7" /></>,
  questionari: <><path d="M9 6h11M9 12h11M9 18h11" /><circle cx="4.8" cy="6" r="1.1" /><circle cx="4.8" cy="12" r="1.1" /><circle cx="4.8" cy="18" r="1.1" /></>,
  parametri: <><path d="M4 7h9M17 7h3M4 17h3M11 17h9" /><circle cx="15" cy="7" r="2.2" /><circle cx="9" cy="17" r="2.2" /></>,
  registro: <><path d="M5 4.5h11.5a2 2 0 0 1 2 2v13H7a2 2 0 0 1-2-2z" /><path d="M5 17.5a2 2 0 0 1 2-2h11.5M9 8.5h6" /></>,
  freccia: <path d="M8 16 16 8M9.5 8H16v6.5" />,
  bersaglio: <><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="4.5" /><circle cx="12" cy="12" r="1" /></>,
  scudo: <><path d="M12 3.5 19 6v5.5c0 4.3-2.9 7.5-7 9-4.1-1.5-7-4.7-7-9V6z" /><path d="m9 12 2.2 2.2L15.5 10" /></>,
  esci: <><path d="M14 4.5h4.5v15H14" /><path d="M10 8.5 6.5 12l3.5 3.5M6.5 12H15" /></>,
} as const

export type NomeIcona = keyof typeof TRATTI

export function Icona({ nome, dimensione = 18 }: { nome: NomeIcona; dimensione?: number }) {
  return (
    <svg className="icona" width={dimensione} height={dimensione} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {TRATTI[nome]}
    </svg>
  )
}
