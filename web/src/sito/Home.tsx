import { Link } from '@tanstack/react-router'
import { Logo } from '../componenti/Logo'

// Home del sito pubblico (corsia sito): segnaposto finché la corsia non costruisce il sito. Nessun accesso richiesto;
// la piattaforma per le aziende pilota sta sotto /app.
export function Home() {
  return (
    <div className="accesso">
      <main className="card">
        <Logo variante="chiaro" dimensione={34} />
        <h1>Neartech</h1>
        <p>Dove l'IA arriva, dove la persona resta.</p>
        <Link to="/app" className="btn btn-pill" style={{ marginTop: 22, justifyContent: 'center', width: '100%' }}>
          Accedi alla piattaforma
        </Link>
      </main>
    </div>
  )
}
