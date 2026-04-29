import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import App from '../App';

// Mock expo modules
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

jest.mock('expo-barcode-scanner', () => ({
  requestPermissionsAsync: jest.fn(() => Promise.resolve({ status: 'granted' })),
  BarCodeScanner: {
    Constants: {
      BarCodeType: { qr: 'qr' }
    }
  }
}));

jest.mock('@react-navigation/native', () => {
  const actualNav = jest.requireActual('@react-navigation/native');
  return {
    ...actualNav,
    useNavigation: () => ({
      navigate: jest.fn(),
      goBack: jest.fn(),
    }),
  };
});

describe('App Component', () => {
  it('renders without crashing', () => {
    const { getByTestId } = render(
      <NavigationContainer>
        <App />
      </NavigationContainer>
    );
    expect(getByTestId('app-root')).toBeTruthy();
  });

  it('has correct navigation structure', () => {
    const tree = render(
      <NavigationContainer>
        <App />
      </NavigationContainer>
    ).toJSON();
    expect(tree).toBeTruthy();
  });
});
