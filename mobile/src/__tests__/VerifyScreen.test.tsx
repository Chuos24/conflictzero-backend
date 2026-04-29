import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import VerifyScreen from '../screens/VerifyScreen';

// Mock AuthContext
jest.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    token: 'test-token',
    isAuthenticated: true,
  }),
}));

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        ruc: '20529400790',
        company_name: 'Test Company',
        risk_score: 85,
        risk_level: 'low',
        status: 'active',
      }),
  })
);

describe('VerifyScreen', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders input field and button', () => {
    const { getByPlaceholderText, getByText } = render(<VerifyScreen />);
    
    expect(getByPlaceholderText('Ingrese RUC (11 dígitos)')).toBeTruthy();
    expect(getByText('Verificar')).toBeTruthy();
  });

  it('validates RUC length', async () => {
    const { getByPlaceholderText, getByText, findByText } = render(<VerifyScreen />);
    
    const input = getByPlaceholderText('Ingrese RUC (11 dígitos)');
    fireEvent.changeText(input, '123456');
    fireEvent.press(getByText('Verificar'));
    
    const error = await findByText('El RUC debe tener 11 dígitos');
    expect(error).toBeTruthy();
  });

  it('calls API with valid RUC', async () => {
    const { getByPlaceholderText, getByText } = render(<VerifyScreen />);
    
    const input = getByPlaceholderText('Ingrese RUC (11 dígitos)');
    fireEvent.changeText(input, '20529400790');
    fireEvent.press(getByText('Verificar'));
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        'https://api.conflictzero.com/api/v2/verify',
        expect.any(Object)
      );
    });
  });
});
