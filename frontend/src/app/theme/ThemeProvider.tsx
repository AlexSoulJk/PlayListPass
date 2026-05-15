import { createContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react'
import { getDefaultTheme, loadStoredTheme, saveStoredTheme } from './themeStorage'
import type { AppTheme } from './themeTypes'

type ThemeContextValue = {
  theme: AppTheme
  setTheme: (theme: AppTheme) => void
}

export const ThemeContext = createContext<ThemeContextValue | null>(null)

const getInitialTheme = (): AppTheme => {
  if (typeof window === 'undefined') {
    return getDefaultTheme()
  }
  return loadStoredTheme()
}

export function ThemeProvider({ children }: PropsWithChildren) {
  const [theme, setThemeState] = useState<AppTheme>(getInitialTheme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    saveStoredTheme(theme)
  }, [theme])

  const setTheme = (nextTheme: AppTheme) => {
    setThemeState(nextTheme)
  }

  const value = useMemo(
    () => ({
      theme,
      setTheme,
    }),
    [theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

