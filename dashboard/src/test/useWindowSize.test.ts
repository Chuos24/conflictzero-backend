import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { useWindowSize } from '../hooks/useWindowSize';

describe('useWindowSize', () => {
  it('should return current window dimensions', () => {
    window.innerWidth = 1024;
    window.innerHeight = 768;

    const { result } = renderHook(() => useWindowSize());
    expect(result.current.width).toBe(1024);
    expect(result.current.height).toBe(768);
  });

  it('should update on resize', () => {
    const { result } = renderHook(() => useWindowSize());

    window.innerWidth = 800;
    window.innerHeight = 600;

    act(() => {
      window.dispatchEvent(new Event('resize'));
    });

    expect(result.current.width).toBe(800);
    expect(result.current.height).toBe(600);
  });
});
