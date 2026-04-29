import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { Text } from '../components';
import { useTheme } from '../context/ThemeContext';

export function CompanyDetailScreen({ route }: any) {
  const { ruc } = route.params;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { colors } = useTheme();

  useEffect(() => {
    loadCompany();
  }, [ruc]);

  async function loadCompany() {
    try {
      const response = await fetch(`https://api.conflictzero.com/v1/verify/${ruc}`);
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background, justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!data) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text style={{ color: colors.text }}>No se encontró información para el RUC {ruc}</Text>
      </View>
    );
  }

  const riskColor = data.risk_level === 'bajo' ? colors.success :
    data.risk_level === 'medio' ? colors.warning : colors.error;

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.content}>
        <Text style={[styles.ruc, { color: colors.textSecondary }]}>RUC: {ruc}</Text>
        <Text style={[styles.name, { color: colors.text }]}>{data.company_name}</Text>

        <View style={[styles.scoreCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <View style={styles.scoreCircle}>
            <Text style={[styles.scoreValue, { color: riskColor }]}>{data.risk_score}</Text>
            <Text style={[styles.scoreLabel, { color: colors.textSecondary }]}>/100</Text>
          </View>
          <View style={styles.scoreInfo}>
            <Text style={[styles.riskLevel, { color: riskColor }]}>{data.risk_level?.toUpperCase()}</Text>
            <Text style={[styles.scoreDescription, { color: colors.textSecondary }]}>
              {data.risk_level === 'bajo' ? 'Empresa confiable con buen historial.' :
               data.risk_level === 'medio' ? 'Riesgo moderado, recomendada precaución.' :
               'Riesgo alto, se recomienda revisión profunda.'}
            </Text>
          </View>
        </View>

        <View style={[styles.section, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Información General</Text>
          <InfoRow label="Estado" value={data.status} colors={colors} />
          <InfoRow label="Deuda SUNAT" value={`S/ ${data.sunat_debt || 0}`} colors={colors} />
          <InfoRow label="Sanciones OSCE" value={data.osce_sanctions_count || 0} colors={colors} />
          <InfoRow label="Sanciones TCE" value={data.tce_sanctions_count || 0} colors={colors} />
        </View>

        <View style={[styles.section, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Dirección</Text>
          <Text style={{ color: colors.textSecondary }}>{data.address || 'No disponible'}</Text>
        </View>
      </View>
    </ScrollView>
  );
}

function InfoRow({ label, value, colors }: any) {
  return (
    <View style={styles.row}>
      <Text style={[styles.label, { color: colors.textSecondary }]}>{label}</Text>
      <Text style={[styles.value, { color: colors.text }]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 20 },
  ruc: { fontSize: 14, marginBottom: 4 },
  name: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
  scoreCard: {
    flexDirection: 'row',
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 20,
  },
  scoreCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 3,
    borderColor: '#e94560',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  scoreValue: { fontSize: 28, fontWeight: 'bold' },
  scoreLabel: { fontSize: 12 },
  scoreInfo: { flex: 1, justifyContent: 'center' },
  riskLevel: { fontSize: 18, fontWeight: 'bold', marginBottom: 4 },
  scoreDescription: { fontSize: 13, lineHeight: 18 },
  section: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  sectionTitle: { fontSize: 16, fontWeight: '600', marginBottom: 12 },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  label: { fontSize: 14 },
  value: { fontSize: 14, fontWeight: '600' },
});
