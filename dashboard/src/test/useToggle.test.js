import { describe, it, expect, act } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useToggle } from '../hooks/useToggle'

describe('useToggle', () => {
  it('should default to false', () => {
    const { result } = renderHook(() => useToggle())
    const [value] = result.current

    expect(value).toBe(false)
  })

  it('should accept initial value', () => {
    const { result } = renderHook(() => useToggle(true))
    const [value] = result.current

    expect(value).toBe(true)
  })

  it('should toggle value', () => {
    const { result } = renderHook(() => useToggle(false))
    const [, toggle] = result.current

    act(() => {
      toggle()
    })

    expect(result.current[0]).toBe(true)

    act(() => {
      toggle()
    })

    expect(result.current[0]).toBe(false)
  })

  it('should set value to true', () => {
    const { result } = renderHook(() => useToggle(false))
    const [, , setTrue] = result.current

    act(() => {
      setTrue()
    })

    expect(result.current[0]).toBe(true)
  })

  it('should set value to false', () => {
    const { result } = renderHook(() => useToggle(true))
    const [, , , setFalse] = result.current

    act(() => {
      setFalse()
    })

    expect(result.current[0]).toBe(false)
  })

  it('should set specific value', () => {
    const { result } = renderHook(() => useToggle(false))
    const [, , , , setValue] = result.current

    act(() => {
      setValue(true)
    })

    expect(result.current[0]).toBe(true)

    act(() => {
      setValue(false)
    })

    expect(result.current[0]).toBe(false)
  })

  it('should toggle multiple times', () => {
    const { result } = renderHook(() => useToggle(false))
    const [, toggle] = result.current

    // Toggle 4 times
    for (let i = 0; i < 4; i++) {
      act(() => {
        toggle()
      })
    }

    expect(result.current[0]).toBe(false)

    // Toggle 5 times
    act(() => {
      toggle()
    })

    expect(result.current[0]).toBe(true)
  })
})
