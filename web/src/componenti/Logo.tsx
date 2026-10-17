// Marchio Neartech «Task Matrix» (docs/identita/guida-identita.html, sezione Marchio): un'asta solida, due moduli
// diagonali che scompongono il processo, una sfera ambra, il punto in cui una persona guarda e decide.
// Variante primaria su chiaro; variante su navy con asta bianca e modulo centrale Cobalt 400.

interface Props {
  variante?: 'chiaro' | 'navy'
  dimensione?: number
  conNome?: boolean
}

export function Logo({ variante = 'chiaro', dimensione = 28, conNome = true }: Props) {
  const asta = variante === 'navy' ? '#FFFFFF' : '#0B2559'
  const modulo = variante === 'navy' ? '#4E77C6' : '#1B499F'
  return (
    <span className={`logo logo-${variante}`}>
      <svg width={dimensione} height={dimensione} viewBox="0 0 48 48" fill="none" aria-hidden="true">
        <rect x="6" y="8" width="9" height="32" rx="2" fill={asta} />
        <rect x="17.5" y="16" width="8" height="8" rx="1.5" fill="#00B4B4" />
        <rect x="24.5" y="24" width="8" height="8" rx="1.5" fill={modulo} />
        <rect x="34" y="20" width="9" height="20" rx="2" fill={asta} />
        <circle cx="38.5" cy="12.5" r="4.5" fill="#F59E0B" />
      </svg>
      {conNome ? <span className="logo-nome">Neartech</span> : <span className="visually-hidden">Neartech</span>}
    </span>
  )
}
