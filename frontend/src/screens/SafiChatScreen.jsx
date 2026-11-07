import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';

export default function SafiChatScreen() {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'safi', text: 'Hola! Soc SAFi. Com et puc ajudar avui amb les teves reserves al SAF?' }
  ]);
  const [inputText, setInputText] = useState('');

  const handleSend = () => {
    if (!inputText.trim()) return;

    // Afegir missatge de l'usuari
    const userMsg = { id: Date.now(), sender: 'user', text: inputText };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');

    // Simulació de resposta de SAFi (preparat per connectar amb POST /safi/chat)
    setTimeout(() => {
      const safiResponse = {
        id: Date.now() + 1,
        sender: 'safi',
        text: 'He rebut la teva consulta. Et recomano reservar a les hores de menys ocupació!'
      };
      setMessages(prev => [...prev, safiResponse]);
    }, 1000);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.headerTitle}>Assistents SAFi</Text>
      
      <ScrollView style={styles.chatArea}>
        {messages.map(msg => (
          <View 
            key={msg.id} 
            style={[
              styles.messageBubble, 
              msg.sender === 'user' ? styles.userBubble : styles.safiBubble
            ]}
          >
            <Text style={styles.messageText}>{msg.text}</Text>
          </View>
        ))}
      </ScrollView>

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Escriu a SAFi..."
          placeholderTextColor="#888"
        />
        <TouchableOpacity style={styles.sendButton} onPress={handleSend}>
          <Text style={styles.sendButtonText}>Enviar</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212', padding: 15 },
  headerTitle: { color: '#FFF', fontSize: 22, fontWeight: 'bold', marginBottom: 15, textAlign: 'center' },
  chatArea: { flex: 1, marginBottom: 15 },
  messageBubble: { padding: 12, borderRadius: 10, marginVertical: 4, maxWidth: '80%' },
  userBubble: { backgroundColor: '#007AFF', alignSelf: 'flex-end' },
  safiBubble: { backgroundColor: '#2C2C2E', alignSelf: 'flex-start' },
  messageText: { color: '#FFF', fontSize: 14 },
  inputRow: { flexDirection: 'row', alignItems: 'center' },
  input: { flex: 1, backgroundColor: '#1E1E1E', color: '#FFF', padding: 12, borderRadius: 8, marginRight: 10 },
  sendButton: { backgroundColor: '#007AFF', padding: 12, borderRadius: 8 },
  sendButtonText: { color: '#FFF', fontWeight: 'bold' }
});