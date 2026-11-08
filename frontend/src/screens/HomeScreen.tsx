import { useFocusEffect } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Button, Card, LoadingState, ScreenContainer } from '../components/ui';
import type { RootStackParamList } from '../navigation/types';
import { getReservations } from '../services/api';
import type { ReservationItem } from '../services/api';
import { colors, radius, shadow, spacing, typography } from '../theme/theme';
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
    <ScreenContainer>
      <Text style={styles.brand}>SAFi</Text>
      <Text style={styles.subtitle}>Reserva millor i evita les hores més plenes.</Text>

      <Card style={styles.nextCard}>
        <Text style={typography.caption}>Pròxima reserva</Text>
        {loading ? (
          <LoadingState lines={2} />
        ) : nextReservation ? (
          <>
            <Text style={styles.cardTitle}>{nextReservation.space_name}</Text>
            <Text style={styles.cardText}>
              {nextReservation.date} · {nextReservation.start}-{nextReservation.end}
            </Text>
            <Pressable
              onPress={() => navigation.navigate('MevesReserves')}
              style={({ pressed }) => [styles.linkBox, pressed && styles.pressed]}
            >
              <Text style={styles.link}>Veure totes les reserves</Text>
            </Pressable>
          </>
        ) : (
          <Text style={styles.cardText}>No tens cap reserva pròxima.</Text>
        )}
      </Card>

      <Button label="RESERVAR" onPress={() => navigation.navigate('Reserva')} style={styles.reserve} />

      <Pressable
        accessibilityRole="button"
        onPress={() => navigation.navigate('Heatmap')}
        style={({ pressed }) => [styles.safiCard, pressed && styles.pressed]}
      >
        <Text style={styles.safiIcon}>✨</Text>
        <View style={styles.flex}>
          <Text style={styles.safiTitle}>Quan és millor anar?</Text>
          <Text style={styles.safiText}>Compara disponibilitat i previsió SAFi.</Text>
        </View>
      </Pressable>

      <View style={styles.grid}>
        <Tile icon="🎟️" label="Reserves" onPress={() => navigation.navigate('MevesReserves')} />
        <Tile icon="💬" label="SAFi Chat" onPress={() => navigation.navigate('SafiChat')} />
        <Tile icon="🏟️" label="Serveis" onPress={() => navigation.navigate('Serveis')} />
        <Tile icon="📊" label="Heatmap" onPress={() => navigation.navigate('Heatmap')} />
      </View>
    </ScreenContainer>
  );
}

function Tile({ icon, label, onPress }: { icon: string; label: string; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      style={({ pressed }) => [styles.tile, pressed && styles.pressed]}
    >
      <Text style={styles.tileIcon}>{icon}</Text>
      <Text style={styles.tileLabel}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  brand: { ...typography.title, fontSize: 34, color: colors.primary },
  subtitle: { ...typography.body, color: colors.textMuted, marginTop: spacing.xs, marginBottom: spacing.xl },
  nextCard: { marginBottom: spacing.lg },
  cardTitle: { ...typography.heading, marginTop: spacing.xs },
  cardText: { ...typography.body, color: colors.textMuted, marginTop: spacing.xs },
  linkBox: { minHeight: 44, justifyContent: 'center', marginTop: spacing.xs },
  link: { color: colors.primary, fontWeight: '700', fontSize: 15 },
  reserve: { minHeight: 68, borderRadius: radius.lg },
  safiCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginTop: spacing.lg,
    padding: spacing.lg,
    borderRadius: radius.lg,
    backgroundColor: colors.safiSoft,
    borderWidth: 1,
    borderColor: colors.safi,
  },
  safiIcon: { fontSize: 26 },
  safiTitle: { fontSize: 17, fontWeight: '700', color: colors.safi },
  safiText: { fontSize: 14, color: colors.textMuted, marginTop: 2 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, marginTop: spacing.lg },
  tile: {
    flexGrow: 1,
    flexBasis: '45%',
    minHeight: 88,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadow.card,
  },
  tileIcon: { fontSize: 26 },
  tileLabel: { fontSize: 15, fontWeight: '700', color: colors.primaryDark },
  pressed: { opacity: 0.8, transform: [{ scale: 0.98 }] },
});
