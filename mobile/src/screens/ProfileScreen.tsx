import React from 'react';
import { View, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Text } from '../components';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

export function ProfileScreen({ navigation }: any) {
  const { user, logout } = useAuth();
  const { colors } = useTheme();

  async function handleLogout() {
    await logout();
    navigation.replace('Login');
  }

  const menuItems = [
    { label: 'Mis Certificados', icon: '📜' },
    { label: 'Configuración', icon: '⚙️' },
    { label: 'Notificaciones', icon: '🔔' },
    { label: 'Ayuda y Soporte', icon: '❓' },
  ];

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.header}>
        <View style={[styles.avatar, { backgroundColor: colors.primary }]}>
          <Text style={styles.avatarText}>{user?.company_name?.[0] || '?'}</Text>
        </View>
        <Text style={[styles.name, { color: colors.text }]}>{user?.company_name || 'Usuario'}</Text>
        <Text style={[styles.email, { color: colors.textSecondary }]}>{user?.email}</Text>
        <View style={[styles.planBadge, { backgroundColor: colors.secondary + '30' }]}>
          <Text style={[styles.planText, { color: colors.primary }]}>Plan {user?.plan_tier || 'Free'}</Text>
        </View>
      </View>

      <View style={styles.menu}>
        {menuItems.map((item, index) => (
          <TouchableOpacity
            key={index}
            style={[styles.menuItem, { backgroundColor: colors.surface, borderColor: colors.border }]}
          >
            <Text style={styles.menuIcon}>{item.icon}</Text>
            <Text style={[styles.menuLabel, { color: colors.text }]}>{item.label}</Text>
            <Text style={[styles.chevron, { color: colors.textSecondary }]}>›</Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity
        style={[styles.logoutButton, { backgroundColor: colors.error + '15' }]}
        onPress={handleLogout}
      >
        <Text style={[styles.logoutText, { color: colors.error }]}>Cerrar Sesión</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { alignItems: 'center', padding: 24 },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: { fontSize: 32, fontWeight: 'bold', color: '#fff' },
  name: { fontSize: 20, fontWeight: 'bold', marginBottom: 4 },
  email: { fontSize: 14, marginBottom: 12 },
  planBadge: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  planText: { fontSize: 12, fontWeight: '600' },
  menu: { padding: 16, gap: 8 },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  menuIcon: { fontSize: 20, marginRight: 12 },
  menuLabel: { fontSize: 15, flex: 1 },
  chevron: { fontSize: 20 },
  logoutButton: {
    margin: 16,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  logoutText: { fontSize: 15, fontWeight: '600' },
});
