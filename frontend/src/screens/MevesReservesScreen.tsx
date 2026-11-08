import { useFocusEffect } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import type { RootStackParamList } from '../navigation/types';
import {
  cancelReservation,
  errorMessage,
  getReservations,
  getServiceSpaces,
  getServices,
} from '../services/api';
import type { ReservationItem, ReservationStatus } from '../services/api';

type Props = NativeStackScreenProps<RootStackParamList, 'MevesReserves'>;
type ViewMode = 'active' | 'history';

const STATUS_LABEL: Record<ReservationStatus, string> = {
  confirmed: 'Confirmada',
  cancelled: 'Cancel·lada',
};

export default function MevesReservesScreen(_props: Props) {
  const [mode, setMode] = useState<ViewMode>('active');
  const [items, setItems] = useState<ReservationItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [askingId, setAskingId] = useState<string | null>(null);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [cancelError, setCancelError] = useState<string | null>(null);
  const [cancelOk, setCancelOk] = useState<string | null>(null);
  // GET /reservations nomes retorna space_id/space_name; el servei s'obte creuant amb
  // GET /services/{id}/spaces (opcional: si falla, es mostra nomes el recurs).
  const [serviceBySpace, setServiceBySpace] = useState<Record<string, string>>({});
  const loadReq = useRef(0);
  const namesReq = useRef(0);

  const loadServiceNames = useCallback(async () => {
    const id = ++namesReq.current;
    try {
      const services = await getServices();
      const lists = await Promise.allSettled(services.map((svc) => getServiceSpaces(svc.id)));
      if (id !== namesReq.current) return;
      const map: Record<string, string> = {};
      lists.forEach((res, i) => {
        if (res.status !== 'fulfilled') return;
        for (const space of res.value) map[space.space_id] = services[i].name;
      });
      setServiceBySpace(map);
    } catch {
      // Sense noms de servei: la llista mostra el recurs igualment.
    }
  }, []);

  const load = useCallback(async () => {
    const id = ++loadReq.current;
    setLoading(true);
    setError(null);
    try {
      const list = await getReservations(undefined, mode === 'history');
      if (id !== loadReq.current) return;
      setItems(mode === 'active' ? list.filter((r) => r.status === 'confirmed') : list);
    } catch (err) {
      if (id !== loadReq.current) return;
      setError(errorMessage(err));
    }
    if (id === loadReq.current) setLoading(false);
  }, [mode]);

  useFocusEffect(
    useCallback(() => {
      setCancelOk(null);
      setCancelError(null);
      void load();
      void loadServiceNames();
    }, [load, loadServiceNames]),
  );

  async function cancel(reservationId: string) {
    if (cancellingId) return;
    setCancellingId(reservationId);
    setCancelError(null);
    setCancelOk(null);
    try {
      await cancelReservation(reservationId);
      setAskingId(null);
      setCancelOk('Reserva cancel·lada.');
      await load();
    } catch (err) {
      setCancelError(errorMessage(err));
    }
    setCancellingId(null);
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.tabs}>
        <Pressable
          style={[styles.tab, mode === 'active' && styles.tabSelected]}
          onPress={() => setMode('active')}
        >
          <Text style={styles.tabText}>Actives</Text>
        </Pressable>
        <Pressable
          style={[styles.tab, mode === 'history' && styles.tabSelected]}
          onPress={() => setMode('history')}
        >
          <Text style={styles.tabText}>Historial</Text>
        </Pressable>
      </View>

      <Text style={styles.help}>
        {mode === 'active'
          ? 'Reserves confirmades actuals.'
          : 'Totes les reserves creades, incloses les cancel·lades.'}
      </Text>

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
      {cancelOk && <Text style={styles.ok}>{cancelOk}</Text>}
      {!loading && !error && items && items.length === 0 && (
        <Text style={styles.muted}>
          {mode === 'active' ? 'Encara no tens reserves actives' : 'Encara no hi ha historial de reserves'}
        </Text>
      )}

      {items?.map((reservation) => {
        const busy = cancellingId === reservation.reservation_id;
        return (
          <View key={reservation.reservation_id} style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.space}>
                {serviceBySpace[reservation.space_id] ?? reservation.space_name}
              </Text>
              <Text style={reservation.status === 'confirmed' ? styles.confirmed : styles.cancelled}>
                {STATUS_LABEL[reservation.status] ?? reservation.status}
              </Text>
            </View>
            <Text style={styles.line}>
              {reservation.date} · {reservation.start}-{reservation.end}
            </Text>
            <Text style={styles.line}>Recurs: {reservation.space_name}</Text>
            <Text style={styles.id}>ID: {reservation.reservation_id}</Text>

            {reservation.status === 'confirmed' && askingId !== reservation.reservation_id && (
              <Pressable
                style={[styles.cancelButton, cancellingId !== null && styles.disabled]}
                disabled={cancellingId !== null}
                onPress={() => setAskingId(reservation.reservation_id)}
              >
                <Text style={styles.cancelText}>Cancel·lar</Text>
              </Pressable>
            )}

            {reservation.status === 'confirmed' && askingId === reservation.reservation_id && (
              <View>
                <Text style={styles.line}>Segur que vols cancel·lar aquesta reserva?</Text>
                <View style={styles.row}>
                  <Pressable
                    style={[styles.cancelButton, styles.flex, busy && styles.disabled]}
                    disabled={cancellingId !== null}
                    onPress={() => void cancel(reservation.reservation_id)}
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
  tabs: { flexDirection: 'row', gap: 8 },
  tab: { flex: 1, padding: 12, borderRadius: 10, borderWidth: 1, borderColor: '#ccc', alignItems: 'center' },
  tabSelected: { borderColor: '#1565c0', backgroundColor: '#e3f0ff' },
  tabText: { fontWeight: 'bold' },
  help: { color: '#666', marginVertical: 10 },
  muted: { color: '#666', marginVertical: 8, textAlign: 'center' },
  error: { color: '#b00020', marginVertical: 8 },
  ok: { color: '#2e7d32', marginVertical: 8, fontWeight: 'bold' },
  retryButton: { padding: 12, borderRadius: 10, backgroundColor: '#eee', alignItems: 'center' },
  retryText: { fontSize: 16 },
  card: { padding: 14, borderRadius: 12, borderWidth: 1, borderColor: '#ccc', marginBottom: 12 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  space: { flex: 1, fontSize: 18, fontWeight: 'bold' },
  line: { fontSize: 16, marginTop: 4 },
  id: { fontSize: 12, color: '#777', marginTop: 5 },
  confirmed: { color: '#2e7d32', fontWeight: 'bold' },
  cancelled: { color: '#666', fontWeight: 'bold' },
  row: { flexDirection: 'row', gap: 8 },
  flex: { flex: 1 },
  cancelButton: { marginTop: 10, padding: 12, borderRadius: 10, backgroundColor: '#b00020', alignItems: 'center' },
  cancelText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  keepButton: { marginTop: 10, padding: 12, borderRadius: 10, backgroundColor: '#eee', alignItems: 'center' },
  keepText: { fontSize: 16 },
  disabled: { opacity: 0.4 },
});
