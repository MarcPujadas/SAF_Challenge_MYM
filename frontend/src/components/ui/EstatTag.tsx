import { StyleSheet, Text, View } from 'react-native';

import { colors, radius, spacing } from '../../theme/theme';

export type TagTone = 'success' | 'danger' | 'warning' | 'neutral' | 'info';

const BG: Record<TagTone, string> = {
  success: colors.primarySoft,
  danger: colors.dangerSoft,
  warning: colors.warningSoft,
  neutral: colors.neutralSoft,
  info: colors.infoSoft,
};
const FG: Record<TagTone, string> = {
  success: colors.primaryDark,
  danger: colors.danger,
  warning: colors.warning,
  neutral: colors.textMuted,
  info: colors.info,
};

// Etiqueta d'estat (Confirmada, Cancel·lada, Reservable…). Sempre text, no nomes color.
export default function EstatTag({ label, tone = 'neutral' }: { label: string; tone?: TagTone }) {
  return (
    <View style={[styles.tag, { backgroundColor: BG[tone] }]}>
      <Text style={[styles.text, { color: FG[tone] }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  tag: {
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 1,
    borderRadius: radius.pill,
  },
  text: { fontSize: 12, fontWeight: '700' },
});
