import { useState, useCallback } from 'react'

/**
 * Hook para toggle de estados booleanos
 * Útil para modales, dropdowns, sidebars, switches, etc.
 * 
 * @param {boolean} initialValue - Valor inicial (default: false)
 * @returns {Array} [value, toggle, setTrue, setFalse, setValue]
 * 
 * @example
 * const [isOpen, toggleOpen, openModal, closeModal] = useToggle(false)
 * 
 * return (
 *   <>
 *     <button onClick={toggleOpen}>Toggle</button>
 *     <button onClick={openModal}>Open</button>
 *     <button onClick={closeModal}>Close</button>
 *     {isOpen && <Modal />}
 *   </>
 * )
 */
export function useToggle(initialValue = false) {
  const [value, setValue] = useState(initialValue)

  const toggle = useCallback(() => {
    setValue((prev) => !prev)
  }, [])

  const setTrue = useCallback(() => {
    setValue(true)
  }, [])

  const setFalse = useCallback(() => {
    setValue(false)
  }, [])

  return [value, toggle, setTrue, setFalse, setValue]
}

export default useToggle
