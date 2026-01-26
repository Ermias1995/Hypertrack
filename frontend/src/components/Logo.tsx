import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'

interface LogoProps {
  className?: string
}

export default function Logo({ className = '' }: LogoProps) {
  const [isDark, setIsDark] = useState(() => {
    // Initial check
    return document.documentElement.classList.contains('dark') ||
      (localStorage.getItem('theme') === 'dark') ||
      (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
  })

  useEffect(() => {
    // Watch for dark mode changes
    const checkDarkMode = () => {
      const isDarkMode = document.documentElement.classList.contains('dark')
      setIsDark(isDarkMode)
    }

    checkDarkMode()

    // Watch for class changes on documentElement
    const observer = new MutationObserver(checkDarkMode)

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    })

    return () => {
      observer.disconnect()
    }
  }, [])

  // Try to use image logos first, fallback to SVG
  const logoSrc = isDark 
    ? '/logo-dark.png' 
    : '/logo-light.png'

  return (
    <Link to="/" className={`flex items-center gap-3 ${className}`}>
      <div className="relative">
        {/* Try image first */}
        <img
          src={logoSrc}
          alt="Playlist Tracker Logo"
          className="h-14 w-auto"
          onError={(e) => {
            // Fallback to SVG if image not found
            const target = e.target as HTMLImageElement
            target.style.display = 'none'
            const svgFallback = target.nextElementSibling as HTMLElement
            if (svgFallback) svgFallback.style.display = 'block'
          }}
        />
        {/* SVG Fallback */}
        <svg
          className="h-14 w-14 hidden"
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Gradient triangle (play button) */}
          <defs>
            <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#10b981" />
            </linearGradient>
          </defs>
          <path
            d="M20 20 L20 80 L70 50 Z"
            fill="url(#logoGradient)"
          />
          {/* Magnifying glass frame */}
          <circle
            cx="50"
            cy="50"
            r="18"
            stroke="#6d28d9"
            strokeWidth="3"
            fill="none"
          />
          {/* Magnifying glass handle */}
          <line
            x1="65"
            y1="65"
            x2="75"
            y2="75"
            stroke="#6d28d9"
            strokeWidth="3"
            strokeLinecap="round"
          />
          {/* Bar chart inside magnifying glass */}
          <rect x="42" y="55" width="4" height="8" fill="#10b981" />
          <rect x="48" y="50" width="4" height="13" fill="#10b981" />
          <rect x="54" y="45" width="4" height="18" fill="#10b981" />
        </svg>
      </div>
      {/* Text */}
      <div className="flex items-center gap-1">
        <span className="text-slate-900 dark:text-slate-100 font-bold text-lg">
          Playlist
        </span>
        <span className="text-emerald-500 dark:text-emerald-400 font-bold text-lg">
          Tracker
        </span>
      </div>
    </Link>
  )
}
