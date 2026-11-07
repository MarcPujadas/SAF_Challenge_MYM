import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { RootStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'>;

export default function HomeScreen({ navigation }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Home</Text>
      <Pressable style={styles.button} onPress={() => navigation.navigate('Reserva')}>
        <Text style={styles.buttonText}>RESERVAR</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  title: { fontSize: 20, marginBottom: 32 },
  button: {
    width: '100%',
    paddingVertical: 28,
    borderRadius: 16,
    backgroundColor: '#1565c0',
    alignItems: 'center',
  },
  buttonText: { color: '#fff', fontSize: 28, fontWeight: 'bold' },
});
