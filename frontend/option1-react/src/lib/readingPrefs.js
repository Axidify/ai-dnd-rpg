import { useEffect, useState } from 'react'

/** Reading settings: theme and story text size, remembered per browser. */
export const THEMES = [
  { id: 'lamplight', label: 'Lamplight', hint: 'Dark, candlelit' },
  { id: 'parchment', label: 'Parchment', hint: 'Light, like a book' },
]
export const TEXT_SIZES = [
  { id: 'small', label: 'S' },
  { id: 'medium', label: 'M' },
  { id: 'large', label: 'L' },
  { id: 'xlarge', label: 'XL' },
]

const KEY = 'reading-prefs'
const DEFAULTS = { theme: 'lamplight', textSize: 'medium' }

function load() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || '{}') }
  } catch {
    return DEFAULTS
  }
}

function apply({ theme, textSize }) {
  const root = document.documentElement
  root.dataset.theme = theme
  root.dataset.textsize = textSize
}

// Apply before first paint so a light theme doesn't flash dark
apply(load())

export function useReadingPrefs() {
  const [prefs, setPrefs] = useState(load)
  useEffect(() => {
    apply(prefs)
    try {
      localStorage.setItem(KEY, JSON.stringify(prefs))
    } catch {
      // Private mode / blocked storage: settings last for this visit only
    }
  }, [prefs])
  const update = (patch) => setPrefs((p) => ({ ...p, ...patch }))
  return [prefs, update]
}
