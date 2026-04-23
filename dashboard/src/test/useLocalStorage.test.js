import React from 'react'
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  useLocalStorage,
  useDebounce,
  useWindowSize,
  useToggle,
  useDocumentTitle
} from '../hooks/useLocalStorage'

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('returns initial value when localStorage is empty', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'default'))
    
    expect(result.current[0]).toBe('default')
  })

  it('reads existing value from localStorage', () => {
    localStorage.setItem('existing-key', JSON.stringify('stored-value'))
    
    const { result } = renderHook(() => useLocalStorage('existing-key', 'default'))
    
    expect(result.current[0]).toBe('stored-value')
  })

  it('sets value in localStorage', () => {
    const { result } = renderHook(() => useLocalStorage('set-key', 'initial'))
    
    act(() => {
      result.current[1]('new-value')
    })
    
    expect(result.current[0]).toBe('new-value')
    expect(JSON.parse(localStorage.getItem('set-key'))).toBe('new-value')
  })

  it('accepts function as setter value', () => {
    const { result } = renderHook(() => useLocalStorage('func-key', 0))
    
    act(() => {
      result.current[1](prev => prev + 1)
    })
    
    expect(result.current[0]).toBe(1)
  })

  it('removes value from localStorage', () => {
    const { result } = renderHook(() => useLocalStorage('remove-key', 'initial'))
    
    act(() => {
      result.current[1]('set-value')
    })
    
    expect(result.current[0]).toBe('set-value')
    
    act(() => {
      result.current[2]() // removeValue
    })
    
    expect(result.current[0]).toBe('initial')
    expect(localStorage.getItem('remove-key')).toBeNull()
  })

  it('handles JSON parse errors gracefully', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    localStorage.setItem('bad-json', 'not-valid-json')
    
    const { result } = renderHook(() => useLocalStorage('bad-json', 'fallback'))
    
    expect(result.current[0]).toBe('fallback')
    expect(consoleSpy).toHaveBeenCalled()
    
    consoleSpy.mockRestore()
  })

  it('handles localStorage set errors gracefully', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('Quota exceeded')
    })
    
    const { result } = renderHook(() => useLocalStorage('error-key', 'initial'))
    
    act(() => {
      result.current[1]('new-value')
    })
    
    expect(consoleSpy).toHaveBeenCalled()
    
    setItemSpy.mockRestore()
    consoleSpy.mockRestore()
  })

  it('works with complex objects', () => {
    const complexValue = { users: [{ id: 1, name: 'Test' }], count: 5 }
    const { result } = renderHook(() => useLocalStorage('complex-key', null))
    
    act(() => {
      result.current[1](complexValue)
    })
    
    expect(result.current[0]).toEqual(complexValue)
    expect(JSON.parse(localStorage.getItem('complex-key'))).toEqual(complexValue)
  })
})

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 300))
    
    expect(result.current).toBe('initial')
  })

  it('debounces value changes', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'initial' } }
    )
    
    rerender({ value: 'changed' })
    expect(result.current).toBe('initial') // still old value
    
    act(() => {
      vi.advanceTimersByTime(300)
    })
    
    expect(result.current).toBe('changed')
  })

  it('resets timer on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'initial' } }
    )
    
    rerender({ value: 'change-1' })
    act(() => { vi.advanceTimersByTime(100) })
    
    rerender({ value: 'change-2' })
    act(() => { vi.advanceTimersByTime(200) })
    
    // Should still be initial because timer was reset
    expect(result.current).toBe('initial')
    
    act(() => { vi.advanceTimersByTime(100) })
    expect(result.current).toBe('change-2')
  })
})

describe('useWindowSize', () => {
  it('returns current window dimensions', () => {
    window.innerWidth = 1024
    window.innerHeight = 768
    
    const { result } = renderHook(() => useWindowSize())
    
    expect(result.current.width).toBe(1024)
    expect(result.current.height).toBe(768)
  })

  it('updates on window resize', () => {
    const { result } = renderHook(() => useWindowSize())
    
    act(() => {
      window.innerWidth = 800
      window.innerHeight = 600
      window.dispatchEvent(new Event('resize'))
    })
    
    expect(result.current.width).toBe(800)
    expect(result.current.height).toBe(600)
  })
})

describe('useToggle', () => {
  it('returns default false value', () => {
    const { result } = renderHook(() => useToggle())
    
    expect(result.current.value).toBe(false)
  })

  it('returns custom initial value', () => {
    const { result } = renderHook(() => useToggle(true))
    
    expect(result.current.value).toBe(true)
  })

  it('toggles value', () => {
    const { result } = renderHook(() => useToggle(false))
    
    act(() => {
      result.current.toggle()
    })
    
    expect(result.current.value).toBe(true)
    
    act(() => {
      result.current.toggle()
    })
    
    expect(result.current.value).toBe(false)
  })

  it('sets value to true', () => {
    const { result } = renderHook(() => useToggle(false))
    
    act(() => {
      result.current.setTrue()
    })
    
    expect(result.current.value).toBe(true)
  })

  it('sets value to false', () => {
    const { result } = renderHook(() => useToggle(true))
    
    act(() => {
      result.current.setFalse()
    })
    
    expect(result.current.value).toBe(false)
  })
})

describe('useDocumentTitle', () => {
  const originalTitle = document.title

  afterEach(() => {
    document.title = originalTitle
  })

  it('sets document title', () => {
    renderHook(() => useDocumentTitle('Test Page'))
    
    expect(document.title).toBe('Test Page | Conflict Zero')
  })

  it('uses custom suffix', () => {
    renderHook(() => useDocumentTitle('Admin', ' | Dashboard'))
    
    expect(document.title).toBe('Admin | Dashboard')
  })

  it('restores original title on unmount', () => {
    document.title = 'Original'
    
    const { unmount } = renderHook(() => useDocumentTitle('Temp'))
    
    expect(document.title).toBe('Temp | Conflict Zero')
    
    unmount()
    
    expect(document.title).toBe('Original')
  })
})
