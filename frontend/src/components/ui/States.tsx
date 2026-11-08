import { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Text, View } from 'react-native';

import { colors, radius, spacing, typography } from '../../theme/theme';
import Button from './Button';

// Estats coherents a totes les pantalles: buit, error (amb reintent) i carrega (esquelet).

export function EmptyState({ title, message, icon = '🗓️' }: { title: string; message?: string; icon?: string }) {
  return (
    <View style={styles.box} accessibilityRole="text">
      <Text style={styles.icon}>{icon}</Text>
      <Text style={[typography.heading, styles.center]}>{title}</Text>
      {message ? <Text style={[typography.caption, styles.center]}>{message}</Text> : null}
    </View>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <View style={[styles.box, styles.errorBox]} accessibilityRole="alert">
      <Text style={styles.icon}>⚠️</Text>
      <Text style={[typography.body, styles.center, { color: colors.danger }]}>{message}</Text>
      <Button label="Tornar-ho a provar" variant="secondary" onPress={onRetry} style={styles.retry} />
    </View>
  );
}

// Esquelet: barres grises que pampalluguegen suaument.
export function LoadingState({ lines = 3 }: { lines?: number }) {
  const pulse = useRef(new Animated.Value(0.45)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 700, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0.45, duration: 700, useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  return (
    <View accessibilityLabel="Carregant" accessibilityRole="progressbar" style={styles.skeletonBox}>
      {Array.from({ length: lines }, (_, i) => (
        <Animated.View
          key={i}
          style={[styles.bar, { opacity: pulse, width: i === lines - 1 ? '60%' : '100%' }]}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    alignItems: 'center',
    padding: spacing.xl,
    gap: spacing.sm,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  errorBox: { backgroundColor: colors.dangerSoft, borderColor: colors.dangerSoft },
  icon: { fontSize: 30 },
  center: { textAlign: 'center' },
  retry: { alignSelf: 'stretch', marginTop: spacing.sm },
  skeletonBox: { gap: spacing.md, paddingVertical: spacing.md },
  bar: { height: 16, borderRadius: radius.sm, backgroundColor: colors.neutralSoft },
});
