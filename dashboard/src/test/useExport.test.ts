import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';

import { useExport } from '../hooks/useExport';
import api from '../services/api';

// Mock api
vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

// Mock helpers
vi.mock('../utils/helpers', () => ({
  downloadFile: vi.fn(),
}));

describe('useExport', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useExport());

    expect(result.current.exporting).toBe(false);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.exportToCSV).toBe('function');
    expect(typeof result.current.exportVerifications).toBe('function');
    expect(typeof result.current.exportToPDF).toBe('function');
  });

  it('should export to CSV successfully', async () => {
    const mockBlob = new Blob(['test'], { type: 'text/csv' });
    const { downloadFile } = await import('../utils/helpers');
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockBlob });

    const { result } = renderHook(() => useExport());

    await act(async () => {
      const success = await result.current.exportToCSV('/test', 'file.csv');
      expect(success).toBe(true);
    });

    expect(result.current.exporting).toBe(false);
    expect(result.current.error).toBeNull();
    expect(api.get).toHaveBeenCalledWith('/test', { responseType: 'blob' });
    expect(downloadFile).toHaveBeenCalledWith(mockBlob, 'file.csv');
  });

  it('should handle CSV export error', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useExport());

    await act(async () => {
      const success = await result.current.exportToCSV('/test', 'file.csv');
      expect(success).toBe(false);
    });

    expect(result.current.exporting).toBe(false);
    expect(result.current.error).toBe('Network error');
  });

  it('should export verifications with date in filename', async () => {
    const mockBlob = new Blob(['test'], { type: 'text/csv' });
    const { downloadFile } = await import('../utils/helpers');
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockBlob });

    const { result } = renderHook(() => useExport());

    await act(async () => {
      const success = await result.current.exportVerifications();
      expect(success).toBe(true);
    });

    expect(api.get).toHaveBeenCalledWith('/dashboard/export/csv', { responseType: 'blob' });
    expect(downloadFile).toHaveBeenCalled();
    const filename = vi.mocked(downloadFile).mock.calls[0][1] as string;
    expect(filename).toMatch(/verificaciones_\d{4}-\d{2}-\d{2}\.csv/);
  });

  it('should handle PDF export when element not found', async () => {
    const { result } = renderHook(() => useExport());

    await act(async () => {
      const success = await result.current.exportToPDF('nonexistent', 'test.pdf');
      expect(success).toBe(false);
    });

    expect(result.current.error).toBe('Elemento no encontrado');
  });
});
