import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, SafeAreaView } from 'react-native';

// Importa tus pantallas existentes
import HomeScreen from './src/screens/HomeScreen';
import ServicesScreen from './src/screens/ServicesScreen';
import SafiChatScreen from './src/screens/SafiChatScreen';

export default function App() {
  // Estado para controlar qué pantalla se muestra actualmente
  const [currentScreen, setCurrentScreen] = useState('Home');

  // Función para renderizar la pantalla activa
  const renderScreen = () => {
    switch (currentScreen) {
      case 'Home':
        return <HomeScreen />;
      case 'Services':
        return <ServicesScreen />;
      case 'Safi':
        return <SafiChatScreen />;
      default:
        return <HomeScreen />;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Contenido de la pantalla activa */}
      <View style={styles.screenContainer}>
        {renderScreen()}
      </View>

      {/* Menú de navegación inferior rápido para pruebas */}
      <View style={styles.navBar}>
        <TouchableOpacity 
          style={[styles.navButton, currentScreen === 'Home' && styles.activeButton]} 
          onPress={() => setCurrentScreen('Home')}
        >
          <Text style={styles.navText}>Inici</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.navButton, currentScreen === 'Services' && styles.activeButton]} 
          onPress={() => setCurrentScreen('Services')}
        >
          <Text style={styles.navText}>Serveis</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.navButton, currentScreen === 'Safi' && styles.activeButton]} 
          onPress={() => setCurrentScreen('Safi')}
        >
          <Text style={styles.navText}>SAFi</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212', // Manteniendo el fondo oscuro que ya usas en tus estilos
  },
  screenContainer: {
    flex: 1,
  },
  navBar: {
    flexDirection: 'row',
    height: 60,
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E',
    backgroundColor: '#1E1E1E',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  navButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  activeButton: {
    backgroundColor: '#007AFF',
  },
  navText: {
    color: '#FFF',
    fontWeight: '600',
    fontSize: 14,
  },
});