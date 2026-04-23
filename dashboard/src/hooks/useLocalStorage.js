import { useState, useEffect, useCallback } from 'react'

/**
 * Custom hook for managing localStorage with JSON support
 * @param {string} key - localStorage key
 * @param {any} initialValue - Default value if key doesn't exist
 * @returns {[any, Function, Function]} - [value, setValue, removeValue]
 */
export function useLocalStorage(key, initialValue = null) {
  // Get initial value from localStorage or use default
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  // Return a wrapped version of useState's setter function
  const setValue = useCallback((value) => {
    try {
      // Allow value to be a function so we have same API as useState
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      window.localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error)
    }
  }, [key, storedValue])

  // Remove value from localStorage
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
 * @param {any} value - Value to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {any} - Debounced value
 */
export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value)

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
 * @returns {{width: number, height: number}} - Window dimensions
 */
export function useWindowSize() {
  const [windowSize, setWindowSize] = useState({
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
 * @param {Function} apiFunction - Async function to call
 * @returns {{data: any, loading: boolean, error: Error|null, execute: Function}}
 */
export function useApi(apiFunction) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const execute = useCallback(async (...args) => {
    try {
      setLoading(true)
      setError(null)
      const result = await apiFunction(...args)
      setData(result)
      return result
    } catch (err) {
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [apiFunction])

  return { data, loading, error, execute }
}

/**
 * Custom hook for document title
 * @param {string} title - Page title
 * @param {string} suffix - Appended suffix (default: " | Conflict Zero")
 */
export function useDocumentTitle(title, suffix = ' | Conflict Zero') {
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
 * @param {boolean} initialValue - Initial toggle value
 * @returns {[boolean, Function]} - [value, toggle]
 */
export function useToggle(initialValue = false) {
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
 * @param {string} initialValue - Initial input value
 * @param {Function} validator - Validation function
 * @returns {{value: string, onChange: Function, error: string|null, isValid: boolean}}
 */
export function useFormInput(initialValue = '', validator = null) {
  const [value, setValue] = useState(initialValue)
  const [touched, setTouched] = useState(false)

  const onChange = useCallback((e) => {
    setValue(e.target.value)
    if (!touched) setTouched(true)
  }, [touched])

  const error = touched && validator ? validator(value) : null
  const isValid = touched ? !error : true

  return { value, onChange, error, isValid, setValue, setTouched }
}

/**
 * Custom hook for click outside detection
 * @param {Function} onClickOutside - Callback when clicking outside
 * @returns {Object} - Ref to attach to element
 */
export function useClickOutside(onClickOutside) {
  const ref = useState({ current: null })[0]

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (ref.current && !ref.current.contains(event.target)) {
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
