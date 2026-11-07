import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import type { RootStackParamList } from '../navigation/types';
import { errorMessage, getServices } from '../services/api';
import type { Service } from '../services/api';

type Props = NativeStackScreenProps<RootStackParamList, 'Serveis'>;

// Nomes mostra els camps que retorna GET /services (contracts.md).
export default function ServeisScreen({ navigation }: Props) {
  const [services, setServices] = useState<Service[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const req = useRef(0);

  const load = useCallback(async () => {
    const id = ++req.current;
    setLoading(true);
    setError(null);
    try {
      const list = await getServices();
      if (id !== req.current) return;
      setServices(list);
    } catch (err) {
      if (id !== req.current) return;
      setError(errorMessage(err));
    }
    if (id === req.current) setLoading(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {loading && <ActivityIndicator />}
      {error && (
        <View>
          <Text style={styles.error}>{error}</Text>
          <Pressable style={styles.retryButton} onPress={() => void load()}>
            <Text style={styles.retryText}>Tornar-ho a provar</Text>
          </Pressable>
        </View>
      )}
      {!loading && !error && services && services.length === 0 && (
        <Text style={styles.muted}>No hi ha serveis disponibles</Text>
      )}
      {services?.map((s) => (
        <View key={s.id} style={styles.card}>
          <Text style={styles.name}>{s.name}</Text>
          <Text style={styles.description}>{s.description}</Text>
          <Text style={s.reservable ? styles.reservable : styles.notReservable}>
            {s.reservable ? 'Reservable' : 'No reservable'}
          </Text>
          <View style={styles.row}>
            <Pressable
              style={[styles.secondary, styles.flex]}
              onPress={() => navigation.navigate('Heatmap', { serviceId: s.id })}
            >
              <Text style={styles.secondaryText}>Veure disponibilitat</Text>
            </Pressable>
            {s.reservable && (
              <Pressable
                style={[styles.primary, styles.flex]}
                onPress={() => navigation.navigate('Reserva', { serviceId: s.id })}
              >
                <Text style={styles.primaryText}>Reservar</Text>
              </Pressable>
            )}
          </View>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, paddingBottom: 48 },
  muted: { color: '#666', marginVertical: 8, textAlign: 'center' },
  error: { color: '#b00020', marginVertical: 8 },
  retryButton: { padding: 12, borderRadius: 10, backgroundColor: '#eee', alignItems: 'center' },
  retryText: { fontSize: 16 },
  card: { padding: 14, borderRadius: 12, borderWidth: 1, borderColor: '#ccc', marginBottom: 12 },
  name: { fontSize: 18, fontWeight: 'bold' },
  description: { fontSize: 15, color: '#444', marginTop: 4 },
  reservable: { marginTop: 6, color: '#2e7d32', fontWeight: 'bold' },
  notReservable: { marginTop: 6, color: '#666', fontWeight: 'bold' },
  row: { flexDirection: 'row', gap: 8, marginTop: 10 },
  flex: { flex: 1 },
  secondary: {
    padding: 12,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#1565c0',
    alignItems: 'center',
  },
  secondaryText: { color: '#1565c0', fontSize: 15, fontWeight: 'bold' },
  primary: { padding: 12, borderRadius: 10, backgroundColor: '#1565c0', alignItems: 'center' },
  primaryText: { color: '#fff', fontSize: 15, fontWeight: 'bold' },
});
