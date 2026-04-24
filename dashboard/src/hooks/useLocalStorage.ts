import { useState, useEffect, useCallback } from 'react'

/**
 * Custom hook for managing localStorage with JSON support
 */
export function useLocalStorage<T>(key: string, initialValue: T | null = null): [T | null, (value: T | ((prev: T | null) => T)) => void, () => void] {
  const [storedValue, setStoredValue] = useState<T | null>(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) as T : initialValue
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  const setValue = useCallback((value: T | ((prev: T | null) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      window.localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error)
    }
  }, [key, storedValue])

  const removeValue = useCallback(() => {
    try {
      window.localStorage.removeItem(key)
      setStoredValue(initialValue)
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error)
    }
  }, [key, initialValue])

  return [storedValue, setValue, removeValue]
}

/**
 * Custom hook for debounced values
 */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

/**
 * Custom hook for window size
 */
export interface WindowSize {
  width: number
  height: number
}

export function useWindowSize(): WindowSize {
  const [windowSize, setWindowSize] = useState<WindowSize>({
    width: window.innerWidth,
    height: window.innerHeight
  })

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      })
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return windowSize
}

/**
 * Custom hook for API calls with loading/error states
 */
interface UseApiReturn<T> {
  data: T | null
  loading: boolean
  error: Error | null
  execute: (...args: unknown[]) => Promise<T>
}

export function useApi<T>(apiFunction: (...args: unknown[]) => Promise<T>): UseApiReturn<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const execute = useCallback(async (...args: unknown[]) => {
    try {
      setLoading(true)
      setError(null)
      const result = await apiFunction(...args)
      setData(result)
      return result
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }, [apiFunction])

  return { data, loading, error, execute }
}

/**
 * Custom hook for document title
 */
export function useDocumentTitle(title: string, suffix = ' | Conflict Zero'): void {
  useEffect(() => {
    const previousTitle = document.title
    document.title = title + suffix
    return () => {
      document.title = previousTitle
    }
  }, [title, suffix])
}

/**
 * Custom hook for toggle state
 */
export interface UseToggleReturn {
  value: boolean
  toggle: () => void
  setTrue: () => void
  setFalse: () => void
}

export function useToggle(initialValue = false): UseToggleReturn {
  const [value, setValue] = useState(initialValue)

  const toggle = useCallback(() => {
    setValue(v => !v)
  }, [])

  const setTrue = useCallback(() => {
    setValue(true)
  }, [])

  const setFalse = useCallback(() => {
    setValue(false)
  }, [])

  return { value, toggle, setTrue, setFalse }
}

/**
 * Custom hook for form input with validation
 */
export interface UseFormInputReturn {
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  error: string | null
  isValid: boolean
  setValue: (value: string) => void
  setTouched: (touched: boolean) => void
}

export function useFormInput(initialValue = '', validator: ((value: string) => string | null) | null = null): UseFormInputReturn {
  const [value, setValue] = useState(initialValue)
  const [touched, setTouched] = useState(false)

  const onChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setValue(e.target.value)
    if (!touched) setTouched(true)
  }, [touched])

  const error = touched && validator ? validator(value) : null
  const isValid = touched ? !error : true

  return { value, onChange, error, isValid, setValue, setTouched }
}

/**
 * Custom hook for click outside detection
 */
export function useClickOutside(onClickOutside: () => void): React.RefObject<HTMLElement | null> {
  const ref = useState<React.RefObject<HTMLElement | null>>({ current: null })[0]

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        onClickOutside()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [onClickOutside, ref])

  return ref
}
