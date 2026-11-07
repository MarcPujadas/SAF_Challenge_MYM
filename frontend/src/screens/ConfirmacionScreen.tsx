import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { RootStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<RootStackParamList, 'Confirmacion'>;

const STATUS_LABEL: Record<string, string> = {
  confirmed: 'confirmada',
  cancelled: 'cancel·lada',
};

export default function ConfirmacionScreen({ navigation, route }: Props) {
  const { reservation, spaceName } = route.params;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Reserva creada</Text>

      <View style={styles.card}>
        <Row label="Espai" value={spaceName} />
        <Row label="Data" value={reservation.date} />
        <Row label="Hora" value={`${reservation.start}-${reservation.end}`} />
        <Row label="Reserva" value={reservation.reservation_id} />
        <Row label="Estat" value={STATUS_LABEL[reservation.status] ?? reservation.status} />
      </View>

      <Pressable style={styles.button} onPress={() => navigation.popToTop()}>
        <Text style={styles.buttonText}>Tornar a l'inici</Text>
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
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 24, textAlign: 'center' },
  card: { borderRadius: 12, borderWidth: 1, borderColor: '#ddd', padding: 16, marginBottom: 32 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  label: { color: '#666', fontSize: 16 },
  value: { fontSize: 16, fontWeight: '600' },
  button: { paddingVertical: 16, borderRadius: 12, backgroundColor: '#1565c0', alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});
