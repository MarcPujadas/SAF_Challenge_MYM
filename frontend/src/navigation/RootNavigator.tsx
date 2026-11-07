import { createNativeStackNavigator } from '@react-navigation/native-stack';

import ConfirmacionScreen from '../screens/ConfirmacionScreen';
import HomeScreen from '../screens/HomeScreen';
import MevesReservesScreen from '../screens/MevesReservesScreen';
import ReservaScreen from '../screens/ReservaScreen';
import SafiChatScreen from '../screens/SafiChatScreen';
import type { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function RootNavigator() {
  return (
    <Stack.Navigator initialRouteName="Home">
      <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'SAF Hack' }} />
      <Stack.Screen name="Reserva" component={ReservaScreen} />
      <Stack.Screen name="Confirmacion" component={ConfirmacionScreen} />
      <Stack.Screen
        name="MevesReserves"
        component={MevesReservesScreen}
        options={{ title: 'Les meves reserves' }}
      />
      <Stack.Screen name="SafiChat" component={SafiChatScreen} options={{ title: 'SAFi' }} />
    </Stack.Navigator>
  );
}
