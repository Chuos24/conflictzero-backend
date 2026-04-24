import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

export interface ThemeContextType {
  theme: 'light' | 'dark'
  isDark: boolean
  toggleTheme: () => void
  setDark: () => void
  setLight: () => void
}

const ThemeContext = createContext<ThemeContextType | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }): JSX.Element {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('cz_theme')
    if (saved === 'light' || saved === 'dark') return saved
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }
    return 'dark'
  })
  
  const [isDark, setIsDark] = useState(theme === 'dark')

  useEffect(() => {
    setIsDark(theme === 'dark')
    document.documentElement.setAttribute('data-theme', theme)
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.documentElement.classList.toggle('light', theme === 'light')
    localStorage.setItem('cz_theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  const setDark = () => setTheme('dark')
  const setLight = () => setTheme('light')

  return (
    <ThemeContext.Provider value={{ theme, isDark, toggleTheme, setDark, setLight }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}
