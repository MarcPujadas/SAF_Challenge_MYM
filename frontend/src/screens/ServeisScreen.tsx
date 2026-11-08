import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Button, Card, EmptyState, ErrorState, EstatTag, LoadingState, ScreenContainer } from '../components/ui';
import type { RootStackParamList } from '../navigation/types';
import { errorMessage, getServices } from '../services/api';
import type { Service } from '../services/api';
import { colors, spacing, typography } from '../theme/theme';

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
    <ScreenContainer>
      {loading && <LoadingState lines={4} />}
      {error && <ErrorState message={error} onRetry={() => void load()} />}
      {!loading && !error && services && services.length === 0 && (
        <EmptyState title="No hi ha serveis disponibles" icon="🏟️" />
      )}
      {services?.map((s) => (
        <Card key={s.id} style={styles.card}>
          <View style={styles.header}>
            <Text style={styles.name}>{s.name}</Text>
            <EstatTag label={s.reservable ? 'Reservable' : 'No reservable'} tone={s.reservable ? 'success' : 'neutral'} />
          </View>
          <Text style={styles.description}>{s.description}</Text>
          {s.resource_count != null && (
            <Text style={styles.meta}>
              {s.resource_count === 1 ? '1 recurs' : `${s.resource_count} recursos`}
            </Text>
          )}
          <View style={styles.row}>
            <Button
              label="Veure disponibilitat"
              variant="secondary"
              style={styles.flex}
              onPress={() => navigation.navigate('Heatmap', { serviceId: s.id })}
            />
            {s.reservable && (
              <Button
                label="Reservar"
                style={styles.flex}
                onPress={() => navigation.navigate('Reserva', { serviceId: s.id })}
              />
            )}
          </View>
        </Card>
      ))}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  card: { marginBottom: spacing.md },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: spacing.sm },
  name: { ...typography.heading, flex: 1 },
  description: { ...typography.body, color: colors.textMuted, marginTop: spacing.xs },
  meta: { ...typography.caption, marginTop: spacing.xs },
  row: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
  flex: { flex: 1 },
});
