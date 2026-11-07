import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Button, StyleSheet, Text, View } from 'react-native';

import type { RootStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<RootStackParamList, 'Confirmacion'>;

export default function ConfirmacionScreen({ navigation }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Confirmacion</Text>
      <Button title="Volver al inicio" onPress={() => navigation.popToTop()} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  title: { fontSize: 20, marginBottom: 32 },
});
