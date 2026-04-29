import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Text, TouchableOpacity, Alert } from 'react-native';
import { BarCodeScanner } from 'expo-barcode-scanner';
import { useTheme } from '../context/ThemeContext';

export function ScanScreen({ navigation }: any) {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanned, setScanned] = useState(false);
  const { colors } = useTheme();

  useEffect(() => {
    (async () => {
      const { status } = await BarCodeScanner.requestPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  function handleBarCodeScanned({ data }: { data: string }) {
    setScanned(true);
    // Validar RUC (11 dígitos)
    const rucMatch = data.match(/\b\d{11}\b/);
    if (rucMatch) {
      navigation.navigate('CompanyDetail', { ruc: rucMatch[0] });
    } else {
      Alert.alert('Código no válido', 'No se encontró un RUC de 11 dígitos en el código escaneado.');
      setScanned(false);
    }
  }

  if (hasPermission === null) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text style={{ color: colors.text }}>Solicitando permiso de cámara...</Text>
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text style={{ color: colors.text }}>Sin acceso a la cámara</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <BarCodeScanner
        onBarCodeScanned={scanned ? undefined : handleBarCodeScanned}
        style={StyleSheet.absoluteFillObject}
      />
      <View style={styles.overlay}>
        <View style={styles.scanArea}>
          <View style={[styles.corner, styles.cornerTL]} />
          <View style={[styles.corner, styles.cornerTR]} />
          <View style={[styles.corner, styles.cornerBL]} />
          <View style={[styles.corner, styles.cornerBR]} />
        </View>
        <Text style={styles.hint}>Escanea un código QR con un RUC</Text>
        {scanned && (
          <TouchableOpacity style={styles.rescanButton} onPress={() => setScanned(false)}>
            <Text style={styles.rescanText}>Escanear de nuevo</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.3)',
  },
  scanArea: {
    width: 250,
    height: 250,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: '#e94560',
    borderWidth: 3,
  },
  cornerTL: { top: 0, left: 0, borderBottomWidth: 0, borderRightWidth: 0 },
  cornerTR: { top: 0, right: 0, borderBottomWidth: 0, borderLeftWidth: 0 },
  cornerBL: { bottom: 0, left: 0, borderTopWidth: 0, borderRightWidth: 0 },
  cornerBR: { bottom: 0, right: 0, borderTopWidth: 0, borderLeftWidth: 0 },
  hint: {
    color: '#fff',
    fontSize: 16,
    marginTop: 24,
    fontWeight: '500',
  },
  rescanButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#e94560',
    borderRadius: 8,
  },
  rescanText: { color: '#fff', fontWeight: '600' },
});
