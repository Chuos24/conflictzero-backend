import React, { useState, useEffect } from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity, Alert } from 'react-native';
import { Text } from '../components';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { OfflineStorage } from '../services/offlineStorage';

export function NetworkScreen({ navigation }: any) {
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();
  const { colors } = useTheme();

  useEffect(() => {
    loadNetwork();
  }, []);

  async function loadNetwork() {
    try {
      const response = await fetch('https://api.conflictzero.com/v1/network/suppliers', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setSuppliers(data.items || []);
      // Guardar en cache
      await OfflineStorage.cacheNetwork(data.items || []);
    } catch (error) {
      // Intentar cache
      const cached = await OfflineStorage.getCachedNetwork();
      if (cached) {
        setSuppliers(cached);
        Alert.alert('Sin conexión', 'Mostrando tu red guardada localmente.');
      } else {
        Alert.alert('Error', 'No se pudo cargar la red de proveedores.');
      }
    } finally {
      setLoading(false);
    }
  }

  function renderSupplier({ item }: any) {
    return (
      <TouchableOpacity
        style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}
        onPress={() => navigation.navigate('CompanyDetail', { ruc: item.supplier_ruc_hash })}
      >
        <Text style={[styles.name, { color: colors.text }]}>{item.supplier_company_name || 'Empresa'}</Text>
        <View style={styles.row}>
          <Text style={[styles.meta, { color: colors.textSecondary }}>
            Última verificación: {item.last_verified_at ? new Date(item.last_verified_at).toLocaleDateString() : 'Nunca'}
          </Text>
          {item.is_active && (
            <View style={[styles.badge, { backgroundColor: colors.success + '20' }]}>
              <Text style={[styles.badgeText, { color: colors.success }]}>Activo</Text>
            </View>
          )}
        </View>
      </TouchableOpacity>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Text style={[styles.title, { color: colors.text }]}>Mi Red de Proveedores</Text>
      <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
        {suppliers.length} proveedores monitoreados
      </Text>
      <FlatList
        data={suppliers}
        renderItem={renderSupplier}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 4 },
  subtitle: { fontSize: 14, marginBottom: 16 },
  list: { gap: 12 },
  card: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  name: { fontSize: 16, fontWeight: '600', marginBottom: 8 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  meta: { fontSize: 12 },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 },
  badgeText: { fontSize: 12, fontWeight: '600' },
});
