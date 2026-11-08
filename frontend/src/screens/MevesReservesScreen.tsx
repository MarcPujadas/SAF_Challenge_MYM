import { useFocusEffect } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  Button,
  Card,
  Chip,
  EmptyState,
  ErrorState,
  EstatTag,
  LoadingState,
  ScreenContainer,
} from '../components/ui';
import type { RootStackParamList } from '../navigation/types';
import {
  cancelReservation,
  errorMessage,
  getReservations,
  getServiceSpaces,
  getServices,
} from '../services/api';
import type { ReservationItem, ReservationStatus } from '../services/api';
import { colors, spacing, typography } from '../theme/theme';

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
    <ScreenContainer>
      <View style={styles.tabs}>
        <Chip label="Actives" selected={mode === 'active'} onPress={() => setMode('active')} style={styles.flex} />
        <Chip label="Historial" selected={mode === 'history'} onPress={() => setMode('history')} style={styles.flex} />
      </View>

      <Text style={styles.help}>
        {mode === 'active'
          ? 'Reserves confirmades actuals.'
          : 'Totes les reserves creades, incloses les cancel·lades.'}
      </Text>

      {loading && <LoadingState lines={3} />}
      {error && <ErrorState message={error} onRetry={() => void load()} />}
      {cancelError && <Text style={styles.error}>{cancelError}</Text>}
      {cancelOk && <Text style={styles.ok}>{cancelOk}</Text>}
      {!loading && !error && items && items.length === 0 && (
        <EmptyState
          title={mode === 'active' ? 'Encara no tens reserves actives' : 'Encara no hi ha historial de reserves'}
          icon="🎟️"
        />
      )}

      {items?.map((reservation) => {
        const busy = cancellingId === reservation.reservation_id;
        return (
          <Card key={reservation.reservation_id} style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.space}>
                {serviceBySpace[reservation.space_id] ?? reservation.space_name}
              </Text>
              <EstatTag
                label={STATUS_LABEL[reservation.status] ?? reservation.status}
                tone={reservation.status === 'confirmed' ? 'success' : 'neutral'}
              />
            </View>
            <Text style={styles.line}>
              {reservation.date} · {reservation.start}-{reservation.end}
            </Text>
            <Text style={styles.sub}>Recurs: {reservation.space_name}</Text>
            <Text style={styles.id}>ID: {reservation.reservation_id}</Text>

            {reservation.status === 'confirmed' && askingId !== reservation.reservation_id && (
              <Button
                label="Cancel·lar"
                variant="danger"
                disabled={cancellingId !== null}
                onPress={() => setAskingId(reservation.reservation_id)}
                style={styles.action}
              />
            )}

            {reservation.status === 'confirmed' && askingId === reservation.reservation_id && (
              <View style={styles.action}>
                <Text style={styles.line}>Segur que vols cancel·lar aquesta reserva?</Text>
                <View style={styles.row}>
                  <Button
                    label={busy ? 'Cancel·lant...' : 'Sí, cancel·lar'}
                    variant="danger"
                    loading={busy}
                    disabled={cancellingId !== null}
                    onPress={() => void cancel(reservation.reservation_id)}
                    style={styles.flex}
                  />
                  <Button
                    label="No"
                    variant="secondary"
                    disabled={cancellingId !== null}
                    onPress={() => setAskingId(null)}
                    style={styles.flex}
                  />
                </View>
              </View>
            )}
          </Card>
        );
      })}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  tabs: { flexDirection: 'row', gap: spacing.sm },
  help: { ...typography.caption, marginVertical: spacing.md },
  error: { color: colors.danger, marginVertical: spacing.sm, fontWeight: '600' },
  ok: { color: colors.primaryDark, marginVertical: spacing.sm, fontWeight: '700' },
  card: { marginBottom: spacing.md },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: spacing.sm },
  space: { ...typography.heading, flex: 1 },
  line: { ...typography.body, marginTop: spacing.sm },
  sub: { ...typography.caption, fontSize: 14, marginTop: spacing.xs },
  id: { ...typography.caption, fontSize: 12, marginTop: spacing.xs },
  action: { marginTop: spacing.md },
  row: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  flex: { flex: 1 },
});
