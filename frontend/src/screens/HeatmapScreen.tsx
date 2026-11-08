import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import HeatmapGrid, { forecastCell, serviceSlotCell } from '../components/HeatmapGrid';
import type { CellValue, HeatmapMode } from '../components/HeatmapGrid';
import { Card, Chip, EmptyState, ErrorState, LoadingState, ScreenContainer } from '../components/ui';
import type { RootStackParamList } from '../navigation/types';
import { errorMessage, getHeatmap, getServiceAvailabilityWeek, getServices } from '../services/api';
import type { Heatmap, Service, ServiceAvailabilityWeek } from '../services/api';
import { colors, radius, spacing, typography } from '../theme/theme';
import { addDays, daysFrom, formatRange, mondayOf, todayDate, weekdayShort } from '../utils/dates';

type Props = NativeStackScreenProps<RootStackParamList, 'Heatmap'>;

export default function HeatmapScreen({ navigation, route }: Props) {
  const [services, setServices] = useState<Service[] | null>(null);
  const [servicesLoading, setServicesLoading] = useState(true);
  const [servicesError, setServicesError] = useState<string | null>(null);
  const [service, setService] = useState<Service | null>(null);

  const [mode, setMode] = useState<HeatmapMode>('availability');
  const [weekStart, setWeekStart] = useState(() => mondayOf(todayDate()));

  const [week, setWeek] = useState<ServiceAvailabilityWeek | null>(null);
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
        const result = await getServiceAvailabilityWeek(service.id, weekStart, weekEnd);
        if (id !== dataReq.current) return;
        setWeek(result);
      } else {
        const result = await getHeatmap(service.id, weekStart, weekEnd);
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
  const { rows, getCell, hasData, isFull, notValidated } = useMemo(() => {
    const set = new Set<string>();
    const cells = new Map<string, CellValue>();
    const full = new Set<string>();
    let anyKnown = false;
    let notValidated = false;
    if (effectiveMode === 'availability' && week) {
      for (const day of week.days) {
        for (const s of day.slots) {
          set.add(s.start);
          cells.set(`${day.date}|${s.start}`, serviceSlotCell(s));
          if (!s.available) full.add(`${day.date}|${s.start}`);
          anyKnown = true;
        }
      }
    } else if (effectiveMode === 'forecast' && forecast) {
      for (const day of forecast.days) {
        for (const s of day.slots) {
          set.add(s.hour);
          cells.set(`${day.date}|${s.hour}`, forecastCell(s));
          // Previsio valida nomes si el backend dona score i nivell coneguts.
          if (s.occupancy_score != null && s.occupancy_level !== 'unknown') anyKnown = true;
          if (s.unavailable_reason === 'aggregated_forecast_not_validated') notValidated = true;
        }
      }
    }
    return {
      rows: Array.from(set).sort(),
      getCell: (date: string, row: string) => cells.get(`${date}|${row}`) ?? null,
      hasData: anyKnown,
      isFull: (date: string, row: string) => full.has(`${date}|${row}`),
      notValidated,
    };
  }, [effectiveMode, week, forecast]);

  const bestForecast = useMemo(() => {
    if (effectiveMode !== 'forecast' || !forecast) return null;
    let best: { date: string; hour: string; score: number } | null = null;
    for (const day of forecast.days) {
      for (const slot of day.slots) {
        if (slot.occupancy_score == null || slot.occupancy_level === 'unknown') continue;
        if (!best || slot.occupancy_score < best.score) {
          best = { date: day.date, hour: slot.hour, score: slot.occupancy_score };
        }
      }
    }
    return best;
  }, [effectiveMode, forecast]);

  function pickCell(date: string, start: string) {
    if (!service) return;
    navigation.navigate('Reserva', { serviceId: service.id, date, start });
  }

  const canBook = !!service?.reservable;
  const loaded = effectiveMode === 'availability' ? week !== null : forecast !== null;

  return (
    <ScreenContainer>
      <Text style={styles.step}>Servei</Text>
      {servicesLoading && <LoadingState lines={2} />}
      {servicesError && <ErrorState message={servicesError} onRetry={loadServices} />}
      <View style={styles.chips}>
        {services?.map((s) => (
          <Chip key={s.id} label={s.name} selected={service?.id === s.id} onPress={() => setService(s)} />
        ))}
      </View>

      {service && (
        <>
          <Text style={[styles.step, styles.stepGap]}>Què vols veure?</Text>
          <View style={styles.chips}>
            <Chip
              label="Disponibilitat"
              selected={effectiveMode === 'availability'}
              disabled={!canBook}
              onPress={() => setMode('availability')}
            />
            <Chip
              label="Previsió SAFi"
              selected={effectiveMode === 'forecast'}
              onPress={() => setMode('forecast')}
            />
          </View>

          {/* Zona etiquetada: que representa el que es veu */}
          <View style={[styles.zone, effectiveMode === 'forecast' && styles.zoneForecast]}>
            <Text style={[styles.zoneTitle, effectiveMode === 'forecast' && styles.zoneTitleForecast]}>
              {effectiveMode === 'availability' ? 'Disponibilitat actual' : 'Previsió SAFi'}
            </Text>
            <Text style={styles.zoneText}>
              {effectiveMode === 'availability'
                ? 'Disponibilitat: reserves actuals.'
                : 'Previsió SAFi: estimació històrica, no és ocupació en temps real.'}
            </Text>
          </View>
          {!canBook && <Text style={styles.notice}>Servei no reservable: només previsió</Text>}
          {bestForecast && (
            <View style={styles.summaryBox}>
              <Text style={styles.summaryTitle}>Millor franja prevista</Text>
              <Text style={styles.summaryText}>
                {weekdayShort(bestForecast.date)} {bestForecast.date} · {bestForecast.hour} · {bestForecast.score}/100
              </Text>
            </View>
          )}

          <View style={styles.weekNav}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Setmana anterior"
              style={({ pressed }) => [styles.weekBtn, pressed && styles.pressed]}
              onPress={() => setWeekStart(addDays(weekStart, -7))}
            >
              <Text style={styles.weekLink}>{'< Setmana anterior'}</Text>
            </Pressable>
            <Text style={styles.weekLabel}>{formatRange(weekStart, weekEnd)}</Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Setmana següent"
              style={({ pressed }) => [styles.weekBtn, pressed && styles.pressed]}
              onPress={() => setWeekStart(addDays(weekStart, 7))}
            >
              <Text style={styles.weekLink}>{'Setmana següent >'}</Text>
            </Pressable>
          </View>

          {loading && <LoadingState lines={5} />}
          {error && <ErrorState message={error} onRetry={loadData} />}
          {!loading && !error && loaded && !hasData && (
            <EmptyState
              icon={effectiveMode === 'forecast' ? '📉' : '🗓️'}
              title={
                effectiveMode === 'forecast'
                  ? notValidated
                    ? 'Sense dades de previsió: encara no hi ha previsió validada per a aquest servei.'
                    : 'Sense dades de previsió'
                  : 'No hi ha franges per a aquesta setmana'
              }
            />
          )}
          {!loading && !error && loaded && hasData && effectiveMode === 'availability' && week && (
            <Text style={styles.muted}>
              {week.capacity_mode === 'people'
                ? 'Cada cel·la mostra les places disponibles del servei.'
                : 'Cada cel·la mostra les unitats lliures sobre el total (p. ex. 3/5).'}
            </Text>
          )}
          {!loading && !error && loaded && hasData && (
            <Card style={styles.gridCard}>
              <HeatmapGrid
                dates={dates}
                rows={rows}
                getCell={getCell}
                mode={effectiveMode}
                onCellPress={canBook ? pickCell : undefined}
                isDisabled={(date, row) => date < today || isFull(date, row)}
              />
            </Card>
          )}
        </>
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  step: { ...typography.heading, marginBottom: spacing.sm },
  stepGap: { marginTop: spacing.xl },
  muted: { ...typography.caption, marginVertical: spacing.sm },
  notice: { color: colors.warning, marginVertical: spacing.sm, fontWeight: '700' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  zone: {
    marginTop: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.primarySoft,
    borderLeftWidth: 4,
    borderLeftColor: colors.primary,
  },
  zoneForecast: { backgroundColor: colors.safiSoft, borderLeftColor: colors.safi },
  zoneTitle: { fontSize: 15, fontWeight: '800', color: colors.primaryDark },
  zoneTitleForecast: { color: colors.safi },
  zoneText: { ...typography.caption, marginTop: 2 },
  summaryBox: {
    marginTop: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.safiSoft,
    borderWidth: 1,
    borderColor: colors.safi,
  },
  summaryTitle: { color: colors.safi, fontWeight: '700' },
  summaryText: { marginTop: 2, fontSize: 15, color: colors.text },
  weekNav: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    marginVertical: spacing.md,
    gap: spacing.xs,
  },
  weekBtn: { minHeight: 44, justifyContent: 'center', paddingHorizontal: spacing.xs },
  weekLink: { color: colors.primary, fontSize: 13, fontWeight: '700' },
  weekLabel: { fontWeight: '800', fontSize: 15, color: colors.text },
  gridCard: { padding: spacing.md },
  pressed: { opacity: 0.6 },
});
