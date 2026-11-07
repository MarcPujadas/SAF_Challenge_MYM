import { useFocusEffect } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import type { RootStackParamList } from '../navigation/types';
import { getReservations } from '../services/api';
import type { ReservationItem } from '../services/api';
import { todayDate } from '../utils/dates';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'>;

export default function HomeScreen({ navigation }: Props) {
  const [nextReservation, setNextReservation] = useState<ReservationItem | null>(null);
  const [loading, setLoading] = useState(true);

  const loadNextReservation = useCallback(async () => {
    setLoading(true);
    try {
      const reservations = await getReservations();
      const today = todayDate();
      const next =
        reservations
          .filter((item) => item.status === 'confirmed' && item.date >= today)
          .sort((a, b) =>
            `${a.date} ${a.start}`.localeCompare(`${b.date} ${b.start}`),
          )[0] ?? null;
      setNextReservation(next);
    } catch {
      setNextReservation(null);
    }
    setLoading(false);
  }, []);

  useFocusEffect(
    useCallback(() => {
      void loadNextReservation();
    }, [loadNextReservation]),
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>SAFi</Text>
      <Text style={styles.subtitle}>Reserva millor i evita les hores més plenes.</Text>

      <View style={styles.nextCard}>
        <Text style={styles.cardLabel}>Pròxima reserva</Text>
        {loading ? (
          <ActivityIndicator />
        ) : nextReservation ? (
          <>
            <Text style={styles.cardTitle}>{nextReservation.space_name}</Text>
            <Text style={styles.cardText}>
              {nextReservation.date} · {nextReservation.start}-{nextReservation.end}
            </Text>
            <Pressable onPress={() => navigation.navigate('MevesReserves')}>
              <Text style={styles.link}>Veure totes les reserves</Text>
            </Pressable>
          </>
        ) : (
          <Text style={styles.cardText}>No tens cap reserva pròxima.</Text>
        )}
      </View>

      <Pressable style={styles.button} onPress={() => navigation.navigate('Reserva')}>
        <Text style={styles.buttonText}>RESERVAR</Text>
      </Pressable>

      <Pressable style={styles.safiButton} onPress={() => navigation.navigate('Heatmap')}>
        <Text style={styles.safiButtonTitle}>Quan és millor anar?</Text>
        <Text style={styles.safiButtonText}>Compara disponibilitat i previsió SAFi.</Text>
      </Pressable>

      <View style={styles.row}>
        <Pressable style={styles.secondary} onPress={() => navigation.navigate('MevesReserves')}>
          <Text style={styles.secondaryText}>Reserves</Text>
        </Pressable>
        <Pressable style={styles.secondary} onPress={() => navigation.navigate('SafiChat')}>
          <Text style={styles.secondaryText}>SAFi Chat</Text>
        </Pressable>
      </View>

      <View style={styles.row}>
        <Pressable style={styles.secondary} onPress={() => navigation.navigate('Serveis')}>
          <Text style={styles.secondaryText}>Serveis</Text>
        </Pressable>
        <Pressable style={styles.secondary} onPress={() => navigation.navigate('Heatmap')}>
          <Text style={styles.secondaryText}>Heatmap</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, justifyContent: 'center' },
  title: { fontSize: 32, fontWeight: 'bold', textAlign: 'center' },
  subtitle: { fontSize: 16, color: '#666', textAlign: 'center', marginTop: 6, marginBottom: 20 },
  nextCard: { borderWidth: 1, borderColor: '#ddd', borderRadius: 14, padding: 14, marginBottom: 18 },
  cardLabel: { fontSize: 12, color: '#666', marginBottom: 4 },
  cardTitle: { fontSize: 18, fontWeight: 'bold' },
  cardText: { fontSize: 15, color: '#444', marginTop: 3 },
  link: { color: '#1565c0', fontWeight: 'bold', marginTop: 8 },
  button: { paddingVertical: 22, borderRadius: 16, backgroundColor: '#1565c0', alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 25, fontWeight: 'bold' },
  safiButton: { marginTop: 12, padding: 14, borderRadius: 14, backgroundColor: '#f3e8ff', borderWidth: 1, borderColor: '#9c27b0' },
  safiButtonTitle: { fontSize: 17, fontWeight: 'bold', color: '#6a1b9a' },
  safiButtonText: { fontSize: 14, color: '#555', marginTop: 2 },
  row: { flexDirection: 'row', gap: 10, marginTop: 10 },
  secondary: { flex: 1, paddingVertical: 13, borderRadius: 12, borderWidth: 1, borderColor: '#1565c0', alignItems: 'center' },
  secondaryText: { color: '#1565c0', fontSize: 15, fontWeight: 'bold' },
});
