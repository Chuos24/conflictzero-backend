import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { useLocalStorage } from '../hooks/useLocalStorage';

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should return default value when key does not exist', () => {
    const { result } = renderHook(() => useLocalStorage('testKey', 'default'));
    expect(result.current[0]).toBe('default');
  });

  it('should update localStorage when value changes', () => {
    const { result } = renderHook(() => useLocalStorage('testKey', 'default'));
    act(() => {
      result.current[1]('updated');
    });
    expect(localStorage.getItem('testKey')).toBe('"updated"');
    expect(result.current[0]).toBe('updated');
  });

  it('should read existing value from localStorage', () => {
    localStorage.setItem('existingKey', '"existing"');
    const { result } = renderHook(() => useLocalStorage('existingKey', 'default'));
    expect(result.current[0]).toBe('existing');
  });
});
