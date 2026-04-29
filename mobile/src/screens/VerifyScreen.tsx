import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, ScrollView } from 'react-native';
import { Text } from '../components';
import { useTheme } from '../context/ThemeContext';

export function VerifyScreen({ navigation }: any) {
  const [ruc, setRuc] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const { colors } = useTheme();

  async function verifyRuc() {
    if (ruc.length !== 11) return;
    setLoading(true);
    try {
      const response = await fetch(`https://api.conflictzero.com/v1/verify/${ruc}`);
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.content}>
        <Text style={[styles.title, { color: colors.text }]}>Verificar Proveedor</Text>
        <Text style={[styles.description, { color: colors.textSecondary }]}>
          Ingresa el RUC de 11 dígitos para verificar una empresa peruana.
        </Text>

        <View style={[styles.inputContainer, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <TextInput
            style={[styles.input, { color: colors.text }]}
            placeholder="20100012345"
            placeholderTextColor={colors.textSecondary}
            value={ruc}
            onChangeText={setRuc}
            keyboardType="numeric"
            maxLength={11}
          />
          <TouchableOpacity
            style={[styles.button, { backgroundColor: colors.primary, opacity: ruc.length === 11 ? 1 : 0.5 }]}
            onPress={verifyRuc}
            disabled={ruc.length !== 11 || loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Verificar</Text>
            )}
          </TouchableOpacity>
        </View>

        {result && (
          <TouchableOpacity
            style={[styles.resultCard, { backgroundColor: colors.surface }]}
            onPress={() => navigation.navigate('CompanyDetail', { ruc })}
          >
            <Text style={[styles.companyName, { color: colors.text }]}>{result.company_name || 'Empresa no encontrada'}</Text>
            <View style={styles.row}>
              <Text style={[styles.label, { color: colors.textSecondary }]}>Riesgo:</Text>
              <Text style={[styles.value, { color: getRiskColor(result.risk_level, colors) }]}>
                {result.risk_level || 'N/A'}
              </Text>
            </View>
            <View style={styles.row}>
              <Text style={[styles.label, { color: colors.textSecondary }]}>Score:</Text>
              <Text style={[styles.value, { color: colors.text }]}>{result.risk_score || 'N/A'}</Text>
            </View>
            <Text style={[styles.tapHint, { color: colors.textSecondary }]}>Toca para ver detalles →</Text>
          </TouchableOpacity>
        )}
      </View>
    </ScrollView>
  );
}

function getRiskColor(level: string, colors: any) {
  switch (level?.toLowerCase()) {
    case 'bajo': return colors.success;
    case 'medio': return colors.warning;
    case 'alto':
    case 'crítico': return colors.error;
    default: return colors.textSecondary;
  }
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 8 },
  description: { fontSize: 14, marginBottom: 24 },
  inputContainer: {
    flexDirection: 'row',
    borderWidth: 1,
    borderRadius: 12,
    padding: 4,
    marginBottom: 20,
  },
  input: { flex: 1, fontSize: 16, padding: 12 },
  button: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  resultCard: {
    padding: 16,
    borderRadius: 12,
    marginTop: 8,
  },
  companyName: { fontSize: 18, fontWeight: 'bold', marginBottom: 12 },
  row: { flexDirection: 'row', marginBottom: 6 },
  label: { fontSize: 14, width: 60 },
  value: { fontSize: 14, fontWeight: '600' },
  tapHint: { fontSize: 12, marginTop: 12, fontStyle: 'italic' },
});
