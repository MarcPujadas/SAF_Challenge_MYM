import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { RootStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<RootStackParamList, 'Confirmacion'>;

export default function ConfirmacionScreen({ navigation, route }: Props) {
  const { reservation, serviceName } = route.params;

  return (
    <View style={styles.container}>
      <Text style={styles.check}>✓</Text>
      <Text style={styles.title}>Reserva confirmada</Text>
      <Text style={styles.subtitle}>La reserva s'ha guardat correctament.</Text>

      <View style={styles.card}>
        <Row label="Servei" value={serviceName} />
        <Row label="Recurs assignat" value={reservation.space_name || reservation.space_id} />
        <Row label="Data" value={reservation.date} />
        <Row label="Hora" value={`${reservation.start}-${reservation.end}`} />
        <Row label="Estat" value={reservation.status === 'confirmed' ? 'Confirmada' : 'Cancel·lada'} />
        <Row label="ID" value={reservation.reservation_id} />
      </View>

      <Pressable style={styles.button} onPress={() => navigation.navigate('MevesReserves')}>
        <Text style={styles.buttonText}>Veure les meves reserves</Text>
      </Pressable>
      <Pressable style={styles.secondary} onPress={() => navigation.popToTop()}>
        <Text style={styles.secondaryText}>Tornar a l'inici</Text>
      </Pressable>
    </View>
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
  container: { flex: 1, padding: 24, justifyContent: 'center' },
  check: { fontSize: 52, color: '#2e7d32', textAlign: 'center', fontWeight: 'bold' },
  title: { fontSize: 26, fontWeight: 'bold', marginTop: 6, textAlign: 'center' },
  subtitle: { fontSize: 16, color: '#666', textAlign: 'center', marginTop: 4, marginBottom: 24 },
  card: { borderRadius: 12, borderWidth: 1, borderColor: '#ddd', padding: 16, marginBottom: 20 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, gap: 12 },
  label: { color: '#666', fontSize: 15 },
  value: { flex: 1, textAlign: 'right', fontSize: 15, fontWeight: '600' },
  button: { paddingVertical: 16, borderRadius: 12, backgroundColor: '#1565c0', alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
  secondary: { marginTop: 10, paddingVertical: 14, borderRadius: 12, borderWidth: 1, borderColor: '#1565c0', alignItems: 'center' },
  secondaryText: { color: '#1565c0', fontSize: 16, fontWeight: 'bold' },
});
