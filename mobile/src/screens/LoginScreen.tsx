import React, { useState } from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { Input, Button, Text } from '../components';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

export function LoginScreen({ navigation }: any) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, isLoading } = useAuth();
  const { colors } = useTheme();

  async function handleLogin() {
    setError('');
    try {
      await login(email, password);
      navigation.replace('Main');
    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión');
    }
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={[styles.container, { backgroundColor: colors.background }]}
    >
      <View style={styles.content}>
        <Text style={[styles.title, { color: colors.text }]}>
          Conflict Zero
        </Text>
        <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
          Verificación Inteligente de Proveedores
        </Text>

        <View style={styles.form}>
          <Input
            label="Email"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            placeholder="tu@empresa.com"
          />
          <Input
            label="Contraseña"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            placeholder="••••••••"
          />
          {error ? (
            <Text style={[styles.error, { color: colors.error }]}>{error}</Text>
          ) : null}
          <Button
            title="Iniciar Sesión"
            onPress={handleLogin}
            loading={isLoading}
          />
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flex: 1, justifyContent: 'center', padding: 24 },
  title: { fontSize: 32, fontWeight: 'bold', marginBottom: 8, textAlign: 'center' },
  subtitle: { fontSize: 14, marginBottom: 40, textAlign: 'center' },
  form: { gap: 16 },
  error: { fontSize: 14, textAlign: 'center', marginTop: 8 },
});
