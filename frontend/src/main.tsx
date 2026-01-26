import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Initialize theme before React renders to prevent flash
const storedTheme = localStorage.getItem('theme')
if (storedTheme === 'dark') {
  document.documentElement.classList.add('dark')
} else if (storedTheme === 'light') {
  document.documentElement.classList.remove('dark')
} else {
  // Use system preference if no stored theme
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark')
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
