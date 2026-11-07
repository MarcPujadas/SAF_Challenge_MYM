import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Button, StyleSheet, Text, View } from 'react-native';

import type { RootStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<RootStackParamList, 'Reserva'>;

export default function ReservaScreen({ navigation }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Reserva</Text>
      <Button title="Ir a Confirmacion" onPress={() => navigation.navigate('Confirmacion')} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  title: { fontSize: 20, marginBottom: 32 },
});
