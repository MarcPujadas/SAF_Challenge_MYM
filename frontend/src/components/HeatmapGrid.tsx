import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import type { OccupancyLevel, ServiceWeekSlot } from '../services/api';
import { parseDate, weekdayShort } from '../utils/dates';

// Presentacio pura: no calcula ocupacio ni disponibilitat, nomes pinta el que rep.

export type Tone = 'good' | 'warn' | 'high' | 'bad' | 'unknown';
export type CellValue = { tone: Tone; text: string; sub?: string };
export type HeatmapMode = 'availability' | 'forecast';

const TONE_COLOR: Record<Tone, string> = {
  good: '#a5d6a7',
  warn: '#fff59d',
  high: '#ffcc80',
  bad: '#ef9a9a',
  unknown: '#e0e0e0',
};

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
  const cellW = compact ? 40 : 46;
  const cellH = compact ? 34 : 44;
  const hourW = compact ? 42 : 48;

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
                    style={[
                      styles.cell,
                      { width: cellW, height: cellH },
                      value ? { backgroundColor: TONE_COLOR[value.tone] } : styles.empty,
                      off && styles.pastCell,
                      isSel && styles.selected,
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
  head: { textAlign: 'center', fontWeight: 'bold', fontSize: 13 },
  headDay: { textAlign: 'center', fontSize: 11, color: '#666', marginBottom: 4 },
  hour: { fontSize: 12, color: '#444', textAlignVertical: 'center', paddingTop: 10 },
  cell: {
    borderWidth: 1,
    borderColor: '#fff',
    borderRadius: 4,
    alignItems: 'center',
    justifyContent: 'center',
  },
  empty: { backgroundColor: '#f5f5f5' },
  pastCell: { opacity: 0.4 },
  selected: { borderColor: '#1565c0', borderWidth: 3 },
  cellText: { fontSize: 11, fontWeight: '600' },
  cellTextSmall: { fontSize: 10 },
  cellSub: { fontSize: 10, color: '#444' },
  legend: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 10, gap: 10 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legendDot: { width: 12, height: 12, borderRadius: 3 },
  legendText: { fontSize: 12, color: '#444' },
});
