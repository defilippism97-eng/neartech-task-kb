import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Senza i globali di Vitest, Testing Library non pulisce il DOM da sola tra un test e l'altro.
afterEach(() => cleanup())
