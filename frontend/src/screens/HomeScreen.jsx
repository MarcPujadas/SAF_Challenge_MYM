import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';

export default function HomeScreen() {
  return (
    <ScrollView style={styles.container}>
      {/* Título de la app */}
      <Text style={styles.headerTitle}>SAF Hack</Text>

      {/* 1. BOTÓN GRANDE DE RESERVAR */}
      <TouchableOpacity 
        style={styles.reserveButton} 
        onPress={() => alert('Iniciar procés de reserva')}
      >
        <Text style={styles.reserveButtonText}>RESERVAR</Text>
      </TouchableOpacity>

      {/* 2. ZONA DE DISPONIBILITAT */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Disponibilitat</Text>
        <Text style={styles.infoText}>📍 Sala Fitness: Ocupació mitjana actualment</Text>
      </View>

      {/* 3. COMPONENT HEATMAP */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Heatmap d'ocupació</Text>
        <View style={styles.heatmapRow}>
          <View style={[styles.badge, { backgroundColor: '#4CAF50' }]}>
            <Text style={styles.badgeText}>09:00 - Baixa</Text>
          </View>
          <View style={[styles.badge, { backgroundColor: '#FFEB3B' }]}>
            <Text style={[styles.badgeText, { color: '#000' }]}>12:00 - Mitjana</Text>
          </View>
          <View style={[styles.badge, { backgroundColor: '#F44336' }]}>
            <Text style={styles.badgeText}>18:00 - Molt Alta</Text>
          </View>
        </View>
      </View>

      {/* 4. ACCESSOS A SERVEIS, SAFI I MAPA */}
      <View style={styles.navigationRow}>
        <TouchableOpacity style={styles.navButton} onPress={() => alert('Anar a Serveis')}>
          <Text style={styles.navButtonText}>🏋️ Serveis</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.navButton} onPress={() => alert('Anar a SAFi')}>
          <Text style={styles.navButtonText}>🤖 SAFi</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.navButton} onPress={() => alert('Anar a Mapa')}>
          <Text style={styles.navButtonText}>🗺️ Mapa</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212', padding: 20 },
  headerTitle: { fontSize: 28, fontWeight: 'bold', color: '#FFF', textAlign: 'center', marginVertical: 15 },
  reserveButton: { backgroundColor: '#007AFF', paddingVertical: 20, borderRadius: 12, alignItems: 'center', marginBottom: 20 },
  reserveButtonText: { color: '#FFF', fontSize: 22, fontWeight: 'bold' },
  sectionCard: { backgroundColor: '#1E1E1E', padding: 15, borderRadius: 10, marginBottom: 15 },
  sectionTitle: { color: '#FFF', fontSize: 18, fontWeight: '600', marginBottom: 10 },
  infoText: { color: '#BBB', fontSize: 14 },
  heatmapRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 5 },
  badge: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 6 },
  badgeText: { color: '#FFF', fontSize: 12, fontWeight: 'bold' },
  navigationRow: { flexDirection: 'row', justifyContent: 'space-around', marginTop: 10, marginBottom: 30 },
  navButton: { backgroundColor: '#2C2C2E', padding: 12, borderRadius: 8, width: '30%', alignItems: 'center' },
  navButtonText: { color: '#FFF', fontSize: 14, fontWeight: '500' }
});