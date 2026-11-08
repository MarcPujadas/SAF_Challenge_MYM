import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';
import type { StyleProp, ViewStyle } from 'react-native';

import { MIN_TOUCH, colors, radius, spacing, typography } from '../../theme/theme';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost';

type Props = {
  label: string;
  onPress: () => void;
  variant?: Variant;
  disabled?: boolean;
  loading?: boolean;
  style?: StyleProp<ViewStyle>;
  accessibilityLabel?: string;
};

const BG: Record<Variant, string> = {
  primary: colors.primary,
  secondary: colors.surface,
  danger: colors.danger,
  ghost: 'transparent',
};
const FG: Record<Variant, string> = {
  primary: colors.textOnPrimary,
  secondary: colors.primary,
  danger: colors.white,
  ghost: colors.primary,
};

// Resposta visual en prémer (opacitat + escala lleugera). Desactivat/carregant: atenuat i sense accio.
export default function Button({
  label,
  onPress,
  variant = 'primary',
  disabled,
  loading,
  style,
  accessibilityLabel,
}: Props) {
  const off = !!disabled || !!loading;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ disabled: off, busy: !!loading }}
      disabled={off}
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        { backgroundColor: BG[variant] },
        variant === 'secondary' && styles.secondaryBorder,
        off && styles.off,
        pressed && styles.pressed,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={FG[variant]} />
      ) : (
        <Text style={[typography.button, { color: FG[variant] }]}>{label}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: MIN_TOUCH + 4,
    paddingHorizontal: spacing.lg,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryBorder: { borderWidth: 1.5, borderColor: colors.primary },
  off: { opacity: 0.45 },
  pressed: { opacity: 0.85, transform: [{ scale: 0.98 }] },
});
