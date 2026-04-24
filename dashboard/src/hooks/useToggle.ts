import { useState, useCallback } from 'react'

export interface UseToggleReturn {
  value: boolean
  toggle: () => void
  setValue: (value: boolean) => void
}

export function useToggle(initialValue = false): UseToggleReturn {
  const [value, setValue] = useState(initialValue)

  const toggle = useCallback(() => {
    setValue(v => !v)
  }, [])

  return { value, toggle, setValue }
}
