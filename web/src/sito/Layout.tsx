import { Outlet } from '@tanstack/react-router'

// Impianto del sito pubblico (corsia sito, docs/piani/fase-6-cantiere.md): la radice e gli altri percorsi pubblici,
// senza accesso. Per ora solo il contenitore delle pagine; intestazione e piè di pagina li aggiunge la corsia sito.
export function LayoutPubblico() {
  return <Outlet />
}
