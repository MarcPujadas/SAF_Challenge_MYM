import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

// Mapeig de nivells d'ocupació segons contracts.md / tasks.md
const OCCUPANCY_COLORS = {
  low: '#4CAF50',        // Verd - Baixa
  medium: '#FFC107',     // Groc - Mitjana
  high: '#FF9800',       // Taronja - Alta
  very_high: '#F44336'   // Vermell - Molt Alta
};

export default function HeatmapComponent() {
  // Dades d'exemple preparades per quan es connecti l'endpoint GET /availability/heatmap
  const heatmapData = [
    { hour: '08:00', level: 'low', label: 'Baixa' },
    { hour: '11:00', level: 'medium', label: 'Mitjana' },
    { hour: '15:00', level: 'high', label: 'Alta' },
    { hour: '19:00', level: 'very_high', label: 'Molt Alta' },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Heatmap d'Ocupació per Hores</Text>
      
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.scrollRow}>
        {heatmapData.map((item, index) => (
          <View key={index} style={[styles.card, { borderColor: OCCUPANCY_COLORS[item.level] }]}>
            <Text style={styles.hourText}>{item.hour}</Text>
            <View style={[styles.badge, { backgroundColor: OCCUPANCY_COLORS[item.level] }]}>
              <Text style={styles.badgeText}>{item.label}</Text>
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1E1E1E',
    padding: 15,
    borderRadius: 10,
    marginVertical: 10,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  scrollRow: {
    flexDirection: 'row',
  },
  card: {
    backgroundColor: '#2C2C2E',
    padding: 12,
    borderRadius: 8,
    marginRight: 10,
    alignItems: 'center',
    borderWidth: 1,
    minWidth: 90,
  },
  hourText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 6,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeText: {
    color: '#000000',
    fontSize: 11,
    fontWeight: 'bold',
  },
});