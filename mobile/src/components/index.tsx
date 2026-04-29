import React from 'react';
import { Text as RNText, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';

export function Text({ style, children, ...props }: any) {
  return <RNText style={style} {...props}>{children}</RNText>;
}

export function Input({ label, style, ...props }: any) {
  return (
    <>
      {label && <RNText style={styles.label}>{label}</RNText>}
      <TextInput
        style={[styles.input, style]}
        placeholderTextColor="#8b9bb4"
        {...props}
      />
    </>
  );
}

export function Button({ title, onPress, loading, style }: any) {
  return (
    <TouchableOpacity
      style={[styles.button, style]}
      onPress={onPress}
      disabled={loading}
    >
      {loading ? (
        <ActivityIndicator color="#fff" />
      ) : (
        <RNText style={styles.buttonText}>{title}</RNText>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  label: { fontSize: 14, fontWeight: '500', color: '#8b9bb4', marginBottom: 6 },
  input: {
    borderWidth: 1,
    borderColor: '#2a2a4a',
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    color: '#ffffff',
    backgroundColor: '#1a1a2e',
  },
  button: {
    backgroundColor: '#e94560',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: { color: '#fff', fontSize: 15, fontWeight: '600' },
});
