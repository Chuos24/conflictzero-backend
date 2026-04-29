import React, { createContext, useContext } from 'react';
import { useColorScheme } from 'react-native';

interface ThemeContextType {
  isDark: boolean;
  colors: {
    background: string;
    surface: string;
    primary: string;
    secondary: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    success: string;
    warning: string;
  };
}

const darkColors = {
  background: '#0f0f23',
  surface: '#1a1a2e',
  primary: '#e94560',
  secondary: '#533483',
  text: '#ffffff',
  textSecondary: '#8b9bb4',
  border: '#2a2a4a',
  error: '#ff4444',
  success: '#00c853',
  warning: '#ffa726',
};

const lightColors = {
  background: '#f5f5f7',
  surface: '#ffffff',
  primary: '#e94560',
  secondary: '#533483',
  text: '#1a1a2e',
  textSecondary: '#6b7280',
  border: '#e5e7eb',
  error: '#dc2626',
  success: '#059669',
  warning: '#d97706',
};

const ThemeContext = createContext<ThemeContextType>({
  isDark: true,
  colors: darkColors,
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const scheme = useColorScheme();
  const isDark = scheme !== 'light';

  return (
    <ThemeContext.Provider value={{ isDark, colors: isDark ? darkColors : lightColors }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
