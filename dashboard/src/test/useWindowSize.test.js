import { describe, it, expect, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useWindowSize } from '../hooks/useWindowSize'

describe('useWindowSize', () => {
  const originalInnerWidth = window.innerWidth
  const originalInnerHeight = window.innerHeight

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    })
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: originalInnerHeight,
    })
  })

  it('should return current window dimensions', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    })
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 768,
    })

    const { result } = renderHook(() => useWindowSize())

    expect(result.current.width).toBe(1024)
    expect(result.current.height).toBe(768)
  })

  it('should identify mobile breakpoint', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    })

    const { result } = renderHook(() => useWindowSize())

    expect(result.current.isMobile).toBe(true)
    expect(result.current.isTablet).toBe(false)
    expect(result.current.isDesktop).toBe(false)
  })

  it('should identify tablet breakpoint', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 800,
    })

    const { result } = renderHook(() => useWindowSize())

    expect(result.current.isMobile).toBe(false)
    expect(result.current.isTablet).toBe(true)
    expect(result.current.isDesktop).toBe(false)
  })

  it('should identify desktop breakpoint', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1200,
    })

    const { result } = renderHook(() => useWindowSize())

    expect(result.current.isMobile).toBe(false)
    expect(result.current.isTablet).toBe(false)
    expect(result.current.isDesktop).toBe(true)
  })

  it('should identify wide breakpoint', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1600,
    })

    const { result } = renderHook(() => useWindowSize())

    expect(result.current.isWide).toBe(true)
  })

  it('should update on window resize', () => {
    const { result } = renderHook(() => useWindowSize())

    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    })

    // Trigger resize event
    window.dispatchEvent(new Event('resize'))

    expect(result.current.width).toBe(500)
    expect(result.current.isMobile).toBe(true)
  })

  it('should cleanup event listener on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')

    const { unmount } = renderHook(() => useWindowSize())

    unmount()

    expect(removeEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function))

    removeEventListenerSpy.mockRestore()
  })
})
