import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useDebounce } from '../hooks/useDebounce'

describe('useDebounce', () => {
  it('should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 500))
    expect(result.current).toBe('initial')
  })

  it('should debounce value changes', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'first', delay: 100 },
      }
    )

    expect(result.current).toBe('first')

    // Change value
    rerender({ value: 'second', delay: 100 })
    
    // Immediately after change, should still be old value
    expect(result.current).toBe('first')

    // Wait for debounce
    await waitFor(() => expect(result.current).toBe('second'), {
      timeout: 200,
    })
  })

  it('should use default delay of 500ms', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value),
      {
        initialProps: { value: 'first' },
      }
    )

    rerender({ value: 'second' })

    // Immediately after change, should still be old value
    expect(result.current).toBe('first')

    // Wait for default debounce delay
    await waitFor(() => expect(result.current).toBe('second'), {
      timeout: 700,
    })
  })

  it('should cancel previous timer on rapid changes', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'a', delay: 100 },
      }
    )

    // Rapid changes
    rerender({ value: 'b', delay: 100 })
    rerender({ value: 'c', delay: 100 })
    rerender({ value: 'd', delay: 100 })

    // Should still be initial value
    expect(result.current).toBe('a')

    // Wait for final debounce
    await waitFor(() => expect(result.current).toBe('d'), {
      timeout: 500,
    })
  })
})
