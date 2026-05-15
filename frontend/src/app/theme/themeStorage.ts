import type { AppTheme } from './themeTypes'

const THEME_KEY = 'playlistpass.ui.theme'
const DEFAULT_THEME: AppTheme = 'dark'

const isTheme = (value: unknown): value is AppTheme => value === 'dark' || value === 'red'

export const getDefaultTheme = (): AppTheme => DEFAULT_THEME

export const loadStoredTheme = (): AppTheme => {
  try {
    const raw = window.localStorage.getItem(THEME_KEY)
    return isTheme(raw) ? raw : DEFAULT_THEME
  } catch {
    return DEFAULT_THEME
  }
}

export const saveStoredTheme = (theme: AppTheme): void => {
  window.localStorage.setItem(THEME_KEY, theme)
}

