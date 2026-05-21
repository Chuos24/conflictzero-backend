import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { useToggle } from '../hooks/useToggle';

describe('useToggle', () => {
  it('should initialize with default false', () => {
    const { result } = renderHook(() => useToggle());
    expect(result.current[0]).toBe(false);
  });

  it('should initialize with provided value', () => {
    const { result } = renderHook(() => useToggle(true));
    expect(result.current[0]).toBe(true);
  });

  it('should toggle value', () => {
    const { result } = renderHook(() => useToggle(false));
    act(() => {
      result.current[1]();
    });
    expect(result.current[0]).toBe(true);
    act(() => {
      result.current[1]();
    });
    expect(result.current[0]).toBe(false);
  });

  it('should set specific value via setValue', () => {
    const { result } = renderHook(() => useToggle(false));
    act(() => {
      result.current[4](true);
    });
    expect(result.current[0]).toBe(true);
  });
});
