import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './app/styles/tokens.css'
import './app/styles/themes/legacy-red.css'
import './app/styles/themes/dark-reference.css'
import './app/styles/global.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
