import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';

export default function ServicesScreen() {
  const servicesList = [
    { id: 1, name: 'Piscina Coberta', info: 'Lliure i cursets', status: 'Disponible' },
    { id: 2, name: 'Sala de Fitness', info: 'Màquines i pes lliure', status: 'Ocupació Mitjana' },
    { id: 3, name: 'Pistes de Tennis', info: 'Reserva prèvia obligatòria', status: 'Lliure' },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.headerTitle}>Serveis del SAF</Text>
      
      <ScrollView>
        {servicesList.map(service => (
          <View key={service.id} style={styles.card}>
            <View>
              <Text style={styles.serviceName}>{service.name}</Text>
              <Text style={styles.serviceInfo}>{service.info}</Text>
              <Text style={styles.serviceStatus}>{service.status}</Text>
            </View>
            <TouchableOpacity style={styles.reserveButton}>
              <Text style={styles.reserveButtonText}>Reservar</Text>
            </TouchableOpacity>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212', padding: 15 },
  headerTitle: { color: '#FFF', fontSize: 22, fontWeight: 'bold', marginBottom: 15, textAlign: 'center' },
  card: { backgroundColor: '#1E1E1E', padding: 15, borderRadius: 10, marginBottom: 12, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  serviceName: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
  serviceInfo: { color: '#AAA', fontSize: 13, marginVertical: 4 },
  serviceStatus: { color: '#4CAF50', fontSize: 12, fontWeight: '600' },
  reserveButton: { backgroundColor: '#007AFF', paddingVertical: 8, paddingHorizontal: 12, borderRadius: 6 },
  reserveButtonText: { color: '#FFF', fontWeight: 'bold', fontSize: 13 }
});