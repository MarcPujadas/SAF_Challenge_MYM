import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { StyleSheet, Text, View } from 'react-native';

import { Button, Card, ScreenContainer } from '../components/ui';
import type { RootStackParamList } from '../navigation/types';
import { colors, radius, spacing, typography } from '../theme/theme';

type Props = NativeStackScreenProps<RootStackParamList, 'Confirmacion'>;

export default function ConfirmacionScreen({ navigation, route }: Props) {
  const { reservation, serviceName } = route.params;

  return (
    <ScreenContainer>
      <View style={styles.check}>
        <Text style={styles.checkMark}>✓</Text>
      </View>
      <Text style={styles.title}>Reserva confirmada</Text>
      <Text style={styles.subtitle}>La reserva s'ha guardat correctament.</Text>

      <Card style={styles.card}>
        <Row label="Servei" value={serviceName} />
        <Row label="Recurs assignat" value={reservation.space_name || reservation.space_id} />
        <Row label="Data" value={reservation.date} />
        <Row label="Hora" value={`${reservation.start}-${reservation.end}`} />
        <Row label="Estat" value={reservation.status === 'confirmed' ? 'Confirmada' : 'Cancel·lada'} />
        <Row label="ID" value={reservation.reservation_id} />
      </Card>

      <Button label="Veure les meves reserves" onPress={() => navigation.navigate('MevesReserves')} />
      <Button
        label="Tornar a l'inici"
        variant="secondary"
        style={styles.second}
        onPress={() => navigation.popToTop()}
      />
    </ScreenContainer>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  check: {
    alignSelf: 'center',
    width: 72,
    height: 72,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.lg,
  },
  checkMark: { fontSize: 38, color: colors.white, fontWeight: '800' },
  title: { ...typography.title, textAlign: 'center', marginTop: spacing.md },
  subtitle: { ...typography.body, color: colors.textMuted, textAlign: 'center', marginTop: spacing.xs, marginBottom: spacing.xl },
  card: { marginBottom: spacing.xl },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.sm, gap: spacing.md },
  label: { ...typography.caption, fontSize: 14 },
  value: { flex: 1, textAlign: 'right', fontSize: 15, fontWeight: '600', color: colors.text },
  second: { marginTop: spacing.md },
});
