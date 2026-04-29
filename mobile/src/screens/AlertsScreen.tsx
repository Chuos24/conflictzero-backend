import React, { useState, useEffect } from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { Text } from '../components';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

export function AlertsScreen() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();
  const { colors } = useTheme();

  useEffect(() => {
    loadAlerts();
  }, []);

  async function loadAlerts() {
    try {
      const response = await fetch('https://api.conflictzero.com/v1/monitoring/alerts', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setAlerts(data.items || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  async function markAsRead(alertId: string) {
    try {
      await fetch(`https://api.conflictzero.com/v1/monitoring/alerts/${alertId}/read`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'read' } : a));
    } catch (error) {
      console.error(error);
    }
  }

  function getSeverityColor(severity: string) {
    switch (severity) {
      case 'critical': return colors.error;
      case 'warning': return colors.warning;
      default: return colors.textSecondary;
    }
  }

  function renderAlert({ item }: any) {
    const isUnread = item.status === 'pending' || item.status === 'sent';
    return (
      <TouchableOpacity
        style={[styles.card, {
          backgroundColor: colors.surface,
          borderColor: isUnread ? colors.primary : colors.border,
          borderLeftWidth: isUnread ? 4 : 1,
        }]}
        onPress={() => isUnread && markAsRead(item.id)}
      >
        <View style={styles.header}>
          <View style={[styles.severityDot, { backgroundColor: getSeverityColor(item.severity) }]} />
          <Text style={[styles.title, { color: colors.text }]}>{item.title}</Text>
          {isUnread && <View style={[styles.unreadBadge, { backgroundColor: colors.primary }]} />}
        </View>
        <Text style={[styles.message, { color: colors.textSecondary }]} numberOfLines={2}>
          {item.message}
        </Text>
        <Text style={[styles.time, { color: colors.textSecondary }]}>
          {new Date(item.created_at).toLocaleString()}
        </Text>
      </TouchableOpacity>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Text style={[styles.screenTitle, { color: colors.text }]}>Alertas</Text>
      <FlatList
        data={alerts}
        renderItem={renderAlert}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  screenTitle: { fontSize: 24, fontWeight: 'bold', marginBottom: 16 },
  list: { gap: 12 },
  card: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  header: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  severityDot: { width: 8, height: 8, borderRadius: 4 },
  title: { fontSize: 14, fontWeight: '600', flex: 1 },
  unreadBadge: { width: 8, height: 8, borderRadius: 4 },
  message: { fontSize: 13, marginBottom: 8 },
  time: { fontSize: 11 },
});
