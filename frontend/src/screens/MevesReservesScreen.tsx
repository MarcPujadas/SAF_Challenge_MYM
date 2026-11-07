import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import type { RootStackParamList } from '../navigation/types';
import { cancelReservation, errorMessage, getReservations } from '../services/api';
import type { ReservationItem, ReservationStatus } from '../services/api';

type Props = NativeStackScreenProps<RootStackParamList, 'MevesReserves'>;

const STATUS_LABEL: Record<ReservationStatus, string> = {
  confirmed: 'Confirmada',
  cancelled: 'Cancel·lada',
};

export default function MevesReservesScreen(_props: Props) {
  const [items, setItems] = useState<ReservationItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cancel·lacio: primer toc demana confirmacio, el segon crida l'API.
  const [askingId, setAskingId] = useState<string | null>(null);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [cancelError, setCancelError] = useState<string | null>(null);

  const loadReq = useRef(0);

  const load = useCallback(async () => {
    const id = ++loadReq.current;
    setLoading(true);
    setError(null);
    try {
      const list = await getReservations();
      if (id !== loadReq.current) return;
      setItems(list);
    } catch (err) {
      if (id !== loadReq.current) return;
      setError(errorMessage(err));
    }
    if (id === loadReq.current) setLoading(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function cancel(reservationId: string) {
    if (cancellingId) return;
    setCancellingId(reservationId);
    setCancelError(null);
    try {
      await cancelReservation(reservationId);
      setAskingId(null);
    } catch (err) {
      setCancelError(errorMessage(err));
    }
    setCancellingId(null);
    void load();
  }

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
      {cancelError && <Text style={styles.error}>{cancelError}</Text>}
      {!loading && !error && items && items.length === 0 && (
        <Text style={styles.muted}>Encara no tens reserves</Text>
      )}
      {items?.map((r) => {
        const busy = cancellingId === r.reservation_id;
        return (
          <View key={r.reservation_id} style={styles.card}>
            <Text style={styles.space}>{r.space_name}</Text>
            <Text style={styles.line}>
              {r.date}  ·  {r.start}-{r.end}
            </Text>
            <Text style={r.status === 'confirmed' ? styles.confirmed : styles.cancelled}>
              {STATUS_LABEL[r.status] ?? r.status}
            </Text>

            {r.status === 'confirmed' && askingId !== r.reservation_id && (
              <Pressable
                style={[styles.cancelButton, cancellingId !== null && styles.disabled]}
                disabled={cancellingId !== null}
                onPress={() => setAskingId(r.reservation_id)}
              >
                <Text style={styles.cancelText}>Cancel·lar</Text>
              </Pressable>
            )}

            {r.status === 'confirmed' && askingId === r.reservation_id && (
              <View>
                <Text style={styles.line}>Segur que vols cancel·lar aquesta reserva?</Text>
                <View style={styles.row}>
                  <Pressable
                    style={[styles.cancelButton, styles.flex, busy && styles.disabled]}
                    disabled={cancellingId !== null}
                    onPress={() => void cancel(r.reservation_id)}
                  >
                    <Text style={styles.cancelText}>{busy ? 'Cancel·lant...' : 'Sí, cancel·lar'}</Text>
                  </Pressable>
                  <Pressable
                    style={[styles.keepButton, styles.flex, busy && styles.disabled]}
                    disabled={cancellingId !== null}
                    onPress={() => setAskingId(null)}
                  >
                    <Text style={styles.keepText}>No</Text>
                  </Pressable>
                </View>
              </View>
            )}
          </View>
        );
      })}
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
  space: { fontSize: 18, fontWeight: 'bold' },
  line: { fontSize: 16, marginTop: 4 },
  confirmed: { marginTop: 4, color: '#2e7d32', fontWeight: 'bold' },
  cancelled: { marginTop: 4, color: '#666', fontWeight: 'bold' },
  row: { flexDirection: 'row', gap: 8 },
  flex: { flex: 1 },
  cancelButton: { marginTop: 10, padding: 12, borderRadius: 10, backgroundColor: '#b00020', alignItems: 'center' },
  cancelText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  keepButton: { marginTop: 10, padding: 12, borderRadius: 10, backgroundColor: '#eee', alignItems: 'center' },
  keepText: { fontSize: 16 },
  disabled: { opacity: 0.4 },
});
