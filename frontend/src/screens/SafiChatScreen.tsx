import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useRef, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import type { RootStackParamList } from '../navigation/types';
import { chatSafi, errorMessage } from '../services/api';

type Props = NativeStackScreenProps<RootStackParamList, 'SafiChat'>;
type ChatMessage = { id: number; from: 'user' | 'safi'; text: string };

const SUGGESTIONS = [
  'Quan hi ha menys gent al fitness?',
  'Quina hora em recomanes demà?',
  'Tinc alguna reserva?',
];

export default function SafiChatScreen(_props: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nextId = useRef(1);

  async function sendMessage(rawText: string) {
    const text = rawText.trim();
    if (!text || sending) return;
    setMessages((prev) => [...prev, { id: nextId.current++, from: 'user', text }]);
    setInput('');
    setError(null);
    setSending(true);
    try {
      const res = await chatSafi(text);
      setMessages((prev) => [...prev, { id: nextId.current++, from: 'safi', text: res.message }]);
    } catch (err) {
      setError(errorMessage(err));
    }
    setSending(false);
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      <ScrollView contentContainerStyle={styles.list}>
        {messages.length === 0 && (
          <>
            <Text style={styles.intro}>Pregunta a SAFi sobre ocupació, disponibilitat o les teves reserves.</Text>
            <View style={styles.suggestions}>
              {SUGGESTIONS.map((suggestion) => (
                <Pressable
                  key={suggestion}
                  style={styles.suggestion}
                  disabled={sending}
                  onPress={() => void sendMessage(suggestion)}
                >
                  <Text style={styles.suggestionText}>{suggestion}</Text>
                </Pressable>
              ))}
            </View>
          </>
        )}

        {messages.map((message) => (
          <View
            key={message.id}
            style={[styles.bubble, message.from === 'user' ? styles.user : styles.safi]}
          >
            {message.from === 'safi' && <Text style={styles.safiTitle}>SAFi</Text>}
            <Text style={styles.text}>{message.text}</Text>
          </View>
        ))}

        {sending && (
          <View style={styles.loadingRow}>
            <ActivityIndicator />
            <Text style={styles.muted}>  SAFi està pensant...</Text>
          </View>
        )}
        {error && <Text style={styles.error}>{error}</Text>}
      </ScrollView>

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Escriu la teva pregunta"
          editable={!sending}
          onSubmitEditing={() => void sendMessage(input)}
          returnKeyType="send"
        />
        <Pressable
          style={[styles.sendButton, (sending || !input.trim()) && styles.disabled]}
          disabled={sending || !input.trim()}
          onPress={() => void sendMessage(input)}
        >
          <Text style={styles.sendText}>Enviar</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  list: { padding: 16, paddingBottom: 24 },
  intro: { color: '#555', marginBottom: 10, fontSize: 16 },
  suggestions: { gap: 8, marginBottom: 18 },
  suggestion: { padding: 12, borderRadius: 12, borderWidth: 1, borderColor: '#9c27b0', backgroundColor: '#faf5ff' },
  suggestionText: { color: '#6a1b9a', fontWeight: '600' },
  muted: { color: '#666', marginVertical: 8 },
  error: { color: '#b00020', marginVertical: 8 },
  bubble: { padding: 12, borderRadius: 12, marginBottom: 8, maxWidth: '85%' },
  user: { alignSelf: 'flex-end', backgroundColor: '#e3f0ff' },
  safi: { alignSelf: 'flex-start', backgroundColor: '#f3e8ff', borderWidth: 1, borderColor: '#9c27b0' },
  safiTitle: { fontWeight: 'bold', color: '#6a1b9a', marginBottom: 4 },
  text: { fontSize: 16 },
  loadingRow: { flexDirection: 'row', alignItems: 'center' },
  inputRow: { flexDirection: 'row', padding: 12, gap: 8, borderTopWidth: 1, borderColor: '#ddd' },
  input: { flex: 1, borderWidth: 1, borderColor: '#ccc', borderRadius: 10, paddingHorizontal: 12, fontSize: 16 },
  sendButton: { paddingHorizontal: 16, justifyContent: 'center', borderRadius: 10, backgroundColor: '#9c27b0' },
  sendText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  disabled: { opacity: 0.4 },
});
