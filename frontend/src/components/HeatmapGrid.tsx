import { Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';

import type { OccupancyLevel, ServiceWeekSlot } from '../services/api';
import { colors, heatTones, radius, spacing } from '../theme/theme';
import { parseDate, weekdayShort } from '../utils/dates';

// Presentacio pura: no calcula ocupacio ni disponibilitat, nomes pinta el que rep.

export type Tone = 'good' | 'warn' | 'high' | 'bad' | 'unknown';
export type CellValue = { tone: Tone; text: string; sub?: string };
export type HeatmapMode = 'availability' | 'forecast';

const TONE_COLOR: Record<Tone, string> = heatTones;

const LEVEL_TONE: Record<OccupancyLevel, Tone> = {
  low: 'good',
  medium: 'warn',
  high: 'high',
  very_high: 'bad',
  unknown: 'unknown',
};

const LEVEL_LABEL: Record<OccupancyLevel, string> = {
  low: 'Baixa',
  medium: 'Mitjana',
  high: 'Alta',
  very_high: 'Molt alta',
  unknown: 'Desc.',
};

export function forecastCell(slot: {
  occupancy_level: OccupancyLevel;
  occupancy_score: number | null;
}): CellValue {
  return {
    tone: LEVEL_TONE[slot.occupancy_level],
    text: LEVEL_LABEL[slot.occupancy_level],
    sub: slot.occupancy_score != null ? String(slot.occupancy_score) : undefined,
  };
}

// Cel·la de disponibilitat agregada d'un servei (GET /services/{id}/availability/week).
// unit: "3/5" (unitats lliures / totals) · people: "47 pl." (places restants). Tot ve del backend.
export function serviceSlotCell(slot: ServiceWeekSlot): CellValue {
  if (!slot.available) return { tone: 'bad', text: 'Plena' };
  let sub: string | undefined;
  if (slot.capacity_mode === 'people') {
    if (slot.remaining_people_capacity != null) sub = `${slot.remaining_people_capacity} pl.`;
  } else if (slot.available_units != null && slot.total_units != null) {
    sub = `${slot.available_units}/${slot.total_units}`;
  }
  return { tone: 'good', text: 'Lliure', sub };
}

type Props = {
  dates: string[]; // eix X
  rows: string[]; // eix Y (hores, venen del backend)
  getCell: (date: string, row: string) => CellValue | null; // null -> "—"
  mode: HeatmapMode;
  onCellPress?: (date: string, row: string) => void;
  isDisabled?: (date: string, row: string) => boolean;
  selected?: { date: string; row: string } | null;
  compact?: boolean;
};

export default function HeatmapGrid({
  dates,
  rows,
  getCell,
  mode,
  onCellPress,
  isDisabled,
  selected,
  compact,
}: Props) {
  // Amplada de cel·la adaptada a la pantalla (7 dies visibles quan hi caben), amb scroll horitzontal si no.
  const { width } = useWindowDimensions();
  const hourW = compact ? 44 : 50;
  const fit = Math.floor((width - spacing.lg * 2 - hourW - 4) / Math.max(dates.length, 1));
  const cellW = Math.max(compact ? 40 : 44, Math.min(fit, 64));
  const cellH = compact ? 36 : 46;

  return (
    <View>
      <ScrollView horizontal>
        <View>
          <View style={styles.row}>
            <View style={{ width: hourW }} />
            {dates.map((d) => (
              <View key={d} style={{ width: cellW }}>
                <Text style={styles.head}>{weekdayShort(d)}</Text>
                <Text style={styles.headDay}>{parseDate(d).getDate()}</Text>
              </View>
            ))}
          </View>
          {rows.map((r) => (
            <View key={r} style={styles.row}>
              <Text style={[styles.hour, { width: hourW, height: cellH }]}>{r}</Text>
              {dates.map((d) => {
                const value = getCell(d, r);
                const off = isDisabled?.(d, r) ?? false;
                const isSel = selected?.date === d && selected?.row === r;
                return (
                  <Pressable
                    key={d}
                    disabled={!value || !onCellPress || off}
                    onPress={() => onCellPress?.(d, r)}
                    accessibilityLabel={
                      value ? `${d} ${r}: ${value.text}${value.sub ? ` ${value.sub}` : ''}` : `${d} ${r}: sense franja`
                    }
                    style={({ pressed }) => [
                      styles.cell,
                      { width: cellW, height: cellH },
                      value ? { backgroundColor: TONE_COLOR[value.tone] } : styles.empty,
                      off && styles.pastCell,
                      isSel && styles.selected,
                      pressed && styles.pressed,
                    ]}
                  >
                    <Text style={[styles.cellText, compact && styles.cellTextSmall]} numberOfLines={1}>
                      {value ? value.text : '—'}
                    </Text>
                    {!compact && value?.sub ? <Text style={styles.cellSub}>{value.sub}</Text> : null}
                  </Pressable>
                );
              })}
            </View>
          ))}
        </View>
      </ScrollView>
      <HeatmapLegend mode={mode} />
    </View>
  );
}

export function HeatmapLegend({ mode }: { mode: HeatmapMode }) {
  const items: [Tone, string][] =
    mode === 'availability'
      ? [
          ['good', 'Lliure'],
          ['bad', 'Plena'],
          ['unknown', 'Desconegut'],
        ]
      : [
          ['good', 'Baixa'],
          ['warn', 'Mitjana'],
          ['high', 'Alta'],
          ['bad', 'Molt alta'],
          ['unknown', 'Desconeguda'],
        ];
  return (
    <View style={styles.legend}>
      {items.map(([tone, label]) => (
        <View key={label} style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: TONE_COLOR[tone] }]} />
          <Text style={styles.legendText}>{label}</Text>
        </View>
      ))}
      <Text style={styles.legendText}>— sense franja</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row' },
  head: { textAlign: 'center', fontWeight: '700', fontSize: 13, color: colors.text },
  headDay: { textAlign: 'center', fontSize: 12, color: colors.textMuted, marginBottom: spacing.xs },
  hour: { fontSize: 12, color: colors.textMuted, textAlignVertical: 'center', paddingTop: 12 },
  cell: {
    borderWidth: 1,
    borderColor: colors.surface,
    borderRadius: radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  empty: { backgroundColor: colors.surfaceMuted },
  pastCell: { opacity: 0.4 },
  pressed: { opacity: 0.75 },
  selected: { borderColor: colors.primaryDark, borderWidth: 3 },
  cellText: { fontSize: 12, fontWeight: '700', color: colors.text },
  cellTextSmall: { fontSize: 11 },
  cellSub: { fontSize: 11, color: colors.text },
  legend: { flexDirection: 'row', flexWrap: 'wrap', marginTop: spacing.md, gap: spacing.md },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  legendDot: { width: 14, height: 14, borderRadius: 4, borderWidth: 1, borderColor: colors.border },
  legendText: { fontSize: 12, color: colors.textMuted },
});
