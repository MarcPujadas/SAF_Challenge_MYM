import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function SafiAdviceBanner({ message, alternative }) {
  if (!message) return null;

  return (
    <View style={styles.container}>
      <Text style={styles.icon}>🤖</Text>
      <View style={styles.textContainer}>
        <Text style={styles.title}>Avís de SAFi</Text>
        <Text style={styles.message}>{message}</Text>
        {alternative && (
          <Text style={styles.alternative}>💡 Recomanació: {alternative}</Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: '#2C2C2E',
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
    padding: 12,
    borderRadius: 8,
    marginVertical: 10,
    alignItems: 'center',
  },
  icon: {
    fontSize: 24,
    marginRight: 10,
  },
  textContainer: {
    flex: 1,
  },
  title: {
    color: '#007AFF',
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 2,
    textTransform: 'uppercase',
  },
  message: {
    color: '#FFFFFF',
    fontSize: 13,
    marginBottom: 4,
  },
  alternative: {
    color: '#4CAF50',
    fontSize: 12,
    fontWeight: '600',
  },
});