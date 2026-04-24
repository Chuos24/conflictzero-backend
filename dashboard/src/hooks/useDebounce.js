import { useState, useEffect } from 'react'

/**
 * Hook para debounce de valores
 * Útil para búsquedas en tiempo real, validación de inputs, etc.
 * 
 * @param {any} value - Valor a debouncear
 * @param {number} delay - Delay en ms (default: 500)
 * @returns {any} Valor debounceado
 * 
 * @example
 * const [search, setSearch] = useState('')
 * const debouncedSearch = useDebounce(search, 300)
 * 
 * useEffect(() => {
 *   // Solo se ejecuta cuando el usuario deja de escribir por 300ms
 *   fetchResults(debouncedSearch)
 * }, [debouncedSearch])
 */
export function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(timer)
    }
  }, [value, delay])

  return debouncedValue
}

export default useDebounce
