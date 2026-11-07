import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import HeatmapGrid, { availabilityCell, forecastCell } from '../components/HeatmapGrid';
import type { CellValue, HeatmapMode } from '../components/HeatmapGrid';
import type { RootStackParamList } from '../navigation/types';
import { errorMessage, getAvailabilityWeek, getHeatmap, getServices } from '../services/api';
import type { AvailabilityWeek, Heatmap, Service } from '../services/api';
import { addDays, daysFrom, formatRange, mondayOf, todayDate } from '../utils/dates';

type Props = NativeStackScreenProps<RootStackParamList, 'Heatmap'>;

export default function HeatmapScreen({ navigation, route }: Props) {
  const [services, setServices] = useState<Service[] | null>(null);
  const [servicesLoading, setServicesLoading] = useState(true);
  const [servicesError, setServicesError] = useState<string | null>(null);
  const [service, setService] = useState<Service | null>(null);

  const [mode, setMode] = useState<HeatmapMode>('availability');
  const [weekStart, setWeekStart] = useState(() => mondayOf(todayDate()));

  const [week, setWeek] = useState<AvailabilityWeek | null>(null);
  const [forecast, setForecast] = useState<Heatmap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const servicesReq = useRef(0);
  const dataReq = useRef(0);

  const today = todayDate();
  const weekEnd = addDays(weekStart, 6);
  const dates = useMemo(() => daysFrom(weekStart, 7), [weekStart]);

  // Sense reserva possible nomes es veu la previsio.
  const effectiveMode: HeatmapMode = service && !service.reservable ? 'forecast' : mode;

  const loadServices = useCallback(async () => {
    const id = ++servicesReq.current;
    setServicesLoading(true);
    setServicesError(null);
    try {
      const list = await getServices();
      if (id !== servicesReq.current) return;
      setServices(list);
      const wanted = route.params?.serviceId;
      setService((prev) => prev ?? list.find((s) => s.id === wanted) ?? list[0] ?? null);
    } catch (err) {
      if (id !== servicesReq.current) return;
      setServicesError(errorMessage(err));
    }
    if (id === servicesReq.current) setServicesLoading(false);
  }, [route.params?.serviceId]);

  useEffect(() => {
    void loadServices();
  }, [loadServices]);

  const loadData = useCallback(async () => {
    const id = ++dataReq.current;
    setWeek(null);
    setForecast(null);
    setError(null);
    if (!service) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      if (effectiveMode === 'availability') {
        const result = await getAvailabilityWeek(service.space_id, weekStart, weekEnd);
        if (id !== dataReq.current) return;
        setWeek(result);
      } else {
        const result = await getHeatmap(service.space_id, weekStart, weekEnd);
        if (id !== dataReq.current) return;
        setForecast(result);
      }
    } catch (err) {
      if (id !== dataReq.current) return;
      setError(errorMessage(err));
    }
    if (id === dataReq.current) setLoading(false);
  }, [service, effectiveMode, weekStart, weekEnd]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  // Files i cel·les: tot ve del backend; si un dia no hi es, la cel·la mostra "—".
  const { rows, getCell, hasData } = useMemo(() => {
    const set = new Set<string>();
    const cells = new Map<string, CellValue>();
    let anyKnown = false;
    if (effectiveMode === 'availability' && week) {
      for (const day of week.days) {
        for (const s of day.slots) {
          set.add(s.start);
          cells.set(`${day.date}|${s.start}`, availabilityCell(s));
          anyKnown = true;
        }
      }
    } else if (effectiveMode === 'forecast' && forecast) {
      for (const day of forecast.days) {
        for (const s of day.slots) {
          set.add(s.hour);
          cells.set(`${day.date}|${s.hour}`, forecastCell(s));
          if (s.occupancy_level !== 'unknown') anyKnown = true;
        }
      }
    }
    return {
      rows: Array.from(set).sort(),
      getCell: (date: string, row: string) => cells.get(`${date}|${row}`) ?? null,
      hasData: anyKnown,
    };
  }, [effectiveMode, week, forecast]);

  function pickCell(date: string, start: string) {
    if (!service) return;
    navigation.navigate('Reserva', { serviceId: service.id, date, start });
  }

  const canBook = !!service?.reservable;
  const loaded = effectiveMode === 'availability' ? week !== null : forecast !== null;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.step}>Servei</Text>
      {servicesLoading && <ActivityIndicator />}
      {servicesError && <ErrorBox text={servicesError} onRetry={loadServices} />}
      <View style={styles.chips}>
        {services?.map((s) => (
          <Pressable
            key={s.id}
            style={[styles.chip, service?.id === s.id && styles.chipSelected]}
            onPress={() => setService(s)}
          >
            <Text style={styles.chipText}>{s.name}</Text>
          </Pressable>
        ))}
      </View>

      {service && (
        <>
          <View style={styles.chips}>
            <ModeButton
              label="Disponibilitat"
              selected={effectiveMode === 'availability'}
              disabled={!canBook}
              onPress={() => setMode('availability')}
            />
            <ModeButton
              label="Previsió SAFi"
              selected={effectiveMode === 'forecast'}
              onPress={() => setMode('forecast')}
            />
          </View>
          <Text style={styles.muted}>
            {effectiveMode === 'availability'
              ? 'Disponibilitat: reserves actuals.'
              : 'Previsió SAFi: estimació històrica, no és ocupació en temps real.'}
          </Text>
          {!canBook && <Text style={styles.notice}>Servei no reservable: només previsió</Text>}

          <View style={styles.weekNav}>
            <Pressable onPress={() => setWeekStart(addDays(weekStart, -7))}>
              <Text style={styles.weekLink}>{'< Setmana anterior'}</Text>
            </Pressable>
            <Text style={styles.weekLabel}>{formatRange(weekStart, weekEnd)}</Text>
            <Pressable onPress={() => setWeekStart(addDays(weekStart, 7))}>
              <Text style={styles.weekLink}>{'Setmana següent >'}</Text>
            </Pressable>
          </View>

          {loading && <ActivityIndicator />}
          {error && <ErrorBox text={error} onRetry={loadData} />}
          {!loading && !error && loaded && !hasData && (
            <Text style={styles.muted}>
              {effectiveMode === 'forecast'
                ? 'Sense dades de previsió'
                : 'No hi ha franges per a aquesta setmana'}
            </Text>
          )}
          {!loading && !error && loaded && hasData && (
            <HeatmapGrid
              dates={dates}
              rows={rows}
              getCell={getCell}
              mode={effectiveMode}
              onCellPress={canBook ? pickCell : undefined}
              isDisabled={(date) => date < today}
            />
          )}
        </>
      )}
    </ScrollView>
  );
}

function ModeButton(props: {
  label: string;
  selected: boolean;
  disabled?: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      style={[styles.chip, props.selected && styles.chipSelected, props.disabled && styles.disabled]}
      disabled={props.disabled}
      onPress={props.onPress}
    >
      <Text style={styles.chipText}>{props.label}</Text>
    </Pressable>
  );
}

function ErrorBox({ text, onRetry }: { text: string; onRetry: () => void }) {
  return (
    <View>
      <Text style={styles.error}>{text}</Text>
      <Pressable style={styles.retryButton} onPress={onRetry}>
        <Text style={styles.retryText}>Tornar-ho a provar</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, paddingBottom: 48 },
  step: { fontSize: 18, fontWeight: 'bold', marginBottom: 8 },
  muted: { color: '#666', marginVertical: 8 },
  notice: { color: '#8a5a00', marginVertical: 4, fontWeight: 'bold' },
  error: { color: '#b00020', marginVertical: 8 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  chip: { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 10, borderWidth: 1, borderColor: '#ccc' },
  chipSelected: { borderColor: '#1565c0', backgroundColor: '#e3f0ff' },
  chipText: { fontSize: 15 },
  disabled: { opacity: 0.4 },
  weekNav: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 14,
  },
  weekLink: { color: '#1565c0', fontSize: 13 },
  weekLabel: { fontWeight: 'bold', fontSize: 15 },
  retryButton: { padding: 12, borderRadius: 10, backgroundColor: '#eee', alignItems: 'center' },
  retryText: { fontSize: 16 },
});
