import { createStackNavigator } from '@react-navigation/stack';

import ConfirmacionScreen from '../screens/ConfirmacionScreen';
import HeatmapScreen from '../screens/HeatmapScreen';
import HomeScreen from '../screens/HomeScreen';
import MevesReservesScreen from '../screens/MevesReservesScreen';
import ReservaScreen from '../screens/ReservaScreen';
import SafiChatScreen from '../screens/SafiChatScreen';
import ServeisScreen from '../screens/ServeisScreen';
import type { RootStackParamList } from './types';
import { colors } from '../theme/theme';

const Stack = createStackNavigator<RootStackParamList>();

export default function RootNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="Home"
      screenOptions={{
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: colors.textOnPrimary,
        headerTitleStyle: { fontWeight: '700' },
        cardStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen
        name="Home"
        component={HomeScreen}
        options={{ title: 'SAF Hack' }}
      />
      <Stack.Screen name="Reserva" component={ReservaScreen} />
      <Stack.Screen name="Confirmacion" component={ConfirmacionScreen} />
      <Stack.Screen
        name="MevesReserves"
        component={MevesReservesScreen}
        options={{ title: 'Les meves reserves' }}
      />
      <Stack.Screen
        name="SafiChat"
        component={SafiChatScreen}
        options={{ title: 'SAFi' }}
      />
      <Stack.Screen
        name="Serveis"
        component={ServeisScreen}
        options={{ title: 'Serveis' }}
      />
      <Stack.Screen
        name="Heatmap"
        component={HeatmapScreen}
        options={{ title: 'Disponibilitat' }}
      />
    </Stack.Navigator>
  );
}