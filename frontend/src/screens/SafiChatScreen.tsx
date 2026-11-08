import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useEffect, useRef, useState } from 'react';
import {
  Animated,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import type { ScrollViewInstance } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import type { RootStackParamList } from '../navigation/types';
import { chatSafi, errorMessage } from '../services/api';
import { colors, radius, spacing, typography } from '../theme/theme';

type Props = NativeStackScreenProps<RootStackParamList, 'SafiChat'>;
type ChatMessage = { id: number; from: 'user' | 'safi'; text: string; noAnswer?: boolean };

const SUGGESTIONS = [
  'Quan hi ha menys gent a la piscina de 25 m?',
  'Quina hora em recomanes demà?',
  'Tinc alguna reserva?',
];

function plainText(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .trim();
}

export default function SafiChatScreen(_props: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nextId = useRef(1);
  const insets = useSafeAreaInsets();
  const listRef = useRef<ScrollViewInstance>(null);

  async function sendMessage(rawText: string) {
    const text = rawText.trim();
    if (!text || sending) return;
    setMessages((prev) => [...prev, { id: nextId.current++, from: 'user', text }]);
    setInput('');
    setError(null);
    setSending(true);
    try {
      const res = await chatSafi(text);
      setMessages((prev) => [
        ...prev,
        // Resposta del backend tal qual; can_answer=false s'indica clarament.
        { id: nextId.current++, from: 'safi', text: plainText(res.message), noAnswer: !res.can_answer },
      ]);
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
      <ScrollView
        ref={listRef}
        keyboardShouldPersistTaps="handled"
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
        contentContainerStyle={styles.list}
      >
        {messages.length === 0 && (
          <>
            <View style={styles.introRow}>
              <Avatar />
              <Text style={styles.intro}>
                Pregunta a SAFi sobre ocupació, disponibilitat o les teves reserves.
              </Text>
            </View>
            <View style={styles.suggestions}>
              {SUGGESTIONS.map((suggestion) => (
                <Pressable
                  key={suggestion}
                  style={({ pressed }) => [
                    styles.suggestion,
                    sending && styles.disabled,
                    pressed && styles.pressed,
                  ]}
                  disabled={sending}
                  onPress={() => void sendMessage(suggestion)}
                >
                  <Text style={styles.suggestionText}>{suggestion}</Text>
                </Pressable>
              ))}
            </View>
          </>
        )}

        {messages.map((message) =>
          message.from === 'user' ? (
            <View key={message.id} style={[styles.bubble, styles.user]}>
              <Text style={styles.userText}>{message.text}</Text>
            </View>
          ) : (
            <View key={message.id} style={styles.safiRow}>
              <Avatar />
              <View style={[styles.bubble, styles.safi, message.noAnswer && styles.safiNoAnswer]}>
                <Text style={styles.text}>{message.text}</Text>
                {message.noAnswer && (
                  <Text style={styles.noAnswer}>SAFi no té prou dades per respondre amb seguretat.</Text>
                )}
              </View>
            </View>
          ),
        )}

        {sending && (
          <View style={styles.safiRow}>
            <Avatar />
            <View style={[styles.bubble, styles.safi]}>
              <TypingDots />
            </View>
          </View>
        )}
        {error && (
          <View style={styles.errorBox} accessibilityRole="alert">
            <Text style={styles.error}>{error}</Text>
          </View>
        )}
      </ScrollView>

      <View style={[styles.inputRow, { paddingBottom: spacing.md + insets.bottom }]}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Escriu la teva pregunta"
          placeholderTextColor={colors.textMuted}
          editable={!sending}
          onSubmitEditing={() => void sendMessage(input)}
          returnKeyType="send"
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Enviar"
          style={({ pressed }) => [
            styles.sendButton,
            (sending || !input.trim()) && styles.disabled,
            pressed && styles.pressed,
          ]}
          disabled={sending || !input.trim()}
          onPress={() => void sendMessage(input)}
        >
          <Text style={styles.sendText}>Enviar</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

function Avatar() {
  return (
    <View style={styles.avatar} accessibilityLabel="SAFi">
      <Text style={styles.avatarText}>S</Text>
    </View>
  );
}

// Indicador "escrivint…" amb tres punts que pampalluguegen.
function TypingDots() {
  const dots = useRef([0, 1, 2].map(() => new Animated.Value(0.3))).current;
  useEffect(() => {
    const loops = dots.map((v, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(i * 160),
          Animated.timing(v, { toValue: 1, duration: 320, useNativeDriver: true }),
          Animated.timing(v, { toValue: 0.3, duration: 320, useNativeDriver: true }),
        ]),
      ),
    );
    loops.forEach((l) => l.start());
    return () => loops.forEach((l) => l.stop());
  }, [dots]);
  return (
    <View style={styles.typing} accessibilityLabel="SAFi està escrivint">
      <Text style={styles.typingText}>escrivint</Text>
      {dots.map((v, i) => (
        <Animated.View key={i} style={[styles.dot, { opacity: v }]} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  list: { padding: spacing.lg, paddingBottom: spacing.xl, flexGrow: 1 },
  introRow: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm, marginBottom: spacing.md },
  intro: { ...typography.body, color: colors.textMuted, flex: 1 },
  suggestions: { gap: spacing.sm, marginBottom: spacing.lg },
  suggestion: {
    minHeight: 44,
    justifyContent: 'center',
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.safi,
    backgroundColor: colors.safiSoft,
  },
  suggestionText: { color: colors.safi, fontWeight: '600' },
  bubble: { padding: spacing.md, borderRadius: radius.lg, marginBottom: spacing.sm, maxWidth: '85%' },
  user: { alignSelf: 'flex-end', backgroundColor: colors.primary, borderBottomRightRadius: radius.sm },
  userText: { fontSize: 16, color: colors.textOnPrimary },
  safiRow: { flexDirection: 'row', alignItems: 'flex-end', gap: spacing.sm, maxWidth: '100%' },
  safi: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderBottomLeftRadius: radius.sm,
    flexShrink: 1,
  },
  safiNoAnswer: { backgroundColor: colors.warningSoft, borderColor: colors.warningSoft },
  text: { fontSize: 16, color: colors.text },
  noAnswer: { marginTop: spacing.sm, fontSize: 13, color: colors.warning, fontWeight: '700' },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: radius.pill,
    backgroundColor: colors.safi,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  avatarText: { color: colors.white, fontWeight: '800' },
  typing: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  typingText: { fontSize: 14, color: colors.textMuted, marginRight: 2 },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: colors.safi },
  errorBox: {
    backgroundColor: colors.dangerSoft,
    borderRadius: radius.md,
    padding: spacing.md,
    marginTop: spacing.sm,
  },
  error: { color: colors.danger, fontWeight: '600' },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: spacing.md,
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
    borderTopWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  input: {
    flex: 1,
    minHeight: 46,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.lg,
    fontSize: 16,
    color: colors.text,
    backgroundColor: colors.background,
  },
  sendButton: {
    minHeight: 46,
    paddingHorizontal: spacing.lg,
    justifyContent: 'center',
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
  },
  sendText: { color: colors.textOnPrimary, fontSize: 16, fontWeight: '700' },
  disabled: { opacity: 0.4 },
  pressed: { opacity: 0.8, transform: [{ scale: 0.98 }] },
});
