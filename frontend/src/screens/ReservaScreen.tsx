import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import HeatmapGrid, { forecastCell, serviceSlotCell } from '../components/HeatmapGrid';
import type { CellValue, HeatmapMode } from '../components/HeatmapGrid';
import { Button, Card, Chip, EmptyState, ErrorState, LoadingState, ScreenContainer } from '../components/ui';
import type { RootStackParamList } from '../navigation/types';
import {
  ApiError,
  createReservation,
  errorMessage,
  getHeatmap,
  getServiceAvailabilityWeek,
  getServices,
  postRecommendationAction,
  postRecommendations,
} from '../services/api';
import type {
  Heatmap,
  OccupancyLevel,
  Recommendation,
  Service,
  ServiceAvailabilityWeek,
  ServiceWeekSlot,
} from '../services/api';
import { colors, radius, spacing, typography } from '../theme/theme';
import { capacityText } from '../utils/capacity';
import { addDays, todayDate, weekdayLong } from '../utils/dates';

type Props = NativeStackScreenProps<RootStackParamList, 'Reserva'>;

const LEVEL_LABEL: Record<OccupancyLevel, string> = {
  low: 'baixa',
  medium: 'mitjana',
  high: 'alta',
  very_high: 'molt alta',
  unknown: 'desconeguda',
};

export default function ReservaScreen({ navigation, route }: Props) {
  const dayDates = useMemo(
    () => Array.from({ length: 7 }, (_, index) => addDays(todayDate(), index)),
    [],
  );

  // Mini heatmap (pas 2): propers 7 dies.
  const [miniMode, setMiniMode] = useState<HeatmapMode>('availability');
  // La disponibilitat (GET /services/{id}/availability/week) i la previsio (heatmap per service_id)
  // es carreguen juntes; el selector nomes canvia quina de les dues es veu.
  const [miniWeek, setMiniWeek] = useState<ServiceAvailabilityWeek | null>(null);
  const [miniForecast, setMiniForecast] = useState<Heatmap | null>(null);
  const [forecastFailed, setForecastFailed] = useState(false);
  const [miniLoading, setMiniLoading] = useState(false);
  const [miniError, setMiniError] = useState<string | null>(null);
  const miniReq = useRef(0);
  const forecastRef = useRef<Heatmap | null>(null); // per a pickSlot (callbacks memoitzats)
  const paramsApplied = useRef(false);
  // Preseleccio demanada per parametres de navegacio: s'aplica quan arriba la disponibilitat.
  const pendingSelect = useRef<{ date: string; start: string } | null>(null);

  // Pas 1: servei
  const [services, setServices] = useState<Service[] | null>(null);
  const [servicesLoading, setServicesLoading] = useState(true);
  const [servicesError, setServicesError] = useState<string | null>(null);
  const [service, setService] = useState<Service | null>(null);

  // Pas 2: dia
  const [date, setDate] = useState<string | null>(null);

  // Pas 3: franja triada (ve de la disponibilitat agregada del servei)
  const [slot, setSlot] = useState<ServiceWeekSlot | null>(null);

  // Pas 4: avis SAFi
  const [advice, setAdvice] = useState<Recommendation | null>(null);
  const [adviceLoading, setAdviceLoading] = useState(false);
  const [adviceFailed, setAdviceFailed] = useState(false);
  const [adviceNoData, setAdviceNoData] = useState<string | null>(null);
  const [adviceDismissed, setAdviceDismissed] = useState(false);

  // Pas 5: confirmar
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Comptadors per ignorar respostes antigues.
  const servicesReq = useRef(0);
  const adviceReq = useRef(0);

  // recommendation_id que ja tenen una accio enviada (maxim una per recomanacio).
  const actedRecs = useRef(new Set<string>());

  // Envia l'accio en segon pla: no bloqueja ni mostra errors a l'usuari.
  function sendRecommendationAction(rec: Recommendation | null, action: 'accepted' | 'ignored') {
    if (!rec || !rec.recommended_slot || !rec.recommendation_id) return;
    if (actedRecs.current.has(rec.recommendation_id)) return;
    actedRecs.current.add(rec.recommendation_id);
    postRecommendationAction(rec.recommendation_id, action).catch(() => {});
  }

  const loadServices = useCallback(async () => {
    const id = ++servicesReq.current;
    setServicesLoading(true);
    setServicesError(null);
    try {
      const list = await getServices();
      if (id !== servicesReq.current) return;
      const reservable = list.filter((s) => s.reservable);
      setServices(reservable);

      // Parametres de navegacio (Heatmap/Serveis): preseleccio de servei, dia i franja.
      const params = route.params;
      if (params?.serviceId && !paramsApplied.current) {
        paramsApplied.current = true;
        const wanted = reservable.find((s) => s.id === params.serviceId);
        if (wanted) {
          if (params.date && params.start && params.date >= todayDate()) {
            pendingSelect.current = { date: params.date, start: params.start };
          }
          setService(wanted);
        }
      }
    } catch (err) {
      if (id !== servicesReq.current) return;
      setServicesError(errorMessage(err));
    }
    if (id === servicesReq.current) setServicesLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    void loadServices();
  }, [loadServices]);

  // Mini heatmap: es recarrega en canviar de servei.
  const loadMini = useCallback(async (s: Service) => {
    const id = ++miniReq.current;
    setMiniWeek(null);
    setMiniForecast(null);
    forecastRef.current = null;
    setForecastFailed(false);
    setMiniError(null);
    setMiniLoading(true);
    const from = todayDate();
    const to = addDays(from, 6);
    // La previsio es opcional: si falla, la disponibilitat i la reserva continuen funcionant.
    const [weekRes, forecastRes] = await Promise.allSettled([
      getServiceAvailabilityWeek(s.id, from, to),
      getHeatmap(s.id, from, to),
    ]);
    if (id !== miniReq.current) return;
    if (forecastRes.status === 'fulfilled') {
      forecastRef.current = forecastRes.value;
      setMiniForecast(forecastRes.value);
    } else {
      setForecastFailed(true);
    }
    if (weekRes.status === 'fulfilled') {
      setMiniWeek(weekRes.value);
      // Franja demanada per parametre: nomes si existeix i esta lliure.
      const pending = pendingSelect.current;
      pendingSelect.current = null;
      const found = pending
        ? weekRes.value.days
            .find((d) => d.date === pending.date)
            ?.slots.find((x) => x.start === pending.start && x.available)
        : undefined;
      if (found && pending) {
        setDate(pending.date);
        void pickSlot(found, s, pending.date);
      }
    } else {
      setMiniError(errorMessage(weekRes.reason));
    }
    setMiniLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (service) void loadMini(service);
  }, [service, loadMini]);

  function resetSelection() {
    adviceReq.current++;
    miniReq.current++;
    setService(null);
    setDate(null);
    setSlot(null);
    setAdvice(null);
    setAdviceLoading(false);
    setAdviceFailed(false);
    setAdviceNoData(null);
    setAdviceDismissed(false);
    setSubmitError(null);
    setMiniWeek(null);
    setMiniForecast(null);
    forecastRef.current = null;
    setForecastFailed(false);
    setMiniLoading(false);
    setMiniError(null);
  }

  function pickService(s: Service) {
    if (service?.id === s.id) {
      resetSelection();
      return;
    }

    adviceReq.current++;
    setService(s);
    setAdviceDismissed(false);
    setDate(null);
    setSlot(null);
    setAdvice(null);
    setAdviceLoading(false);
    setAdviceFailed(false);
    setAdviceNoData(null);
    setSubmitError(null);
  }

  // Cel·la del mini heatmap: selecciona dia i franja lliure (dades de la disponibilitat agregada).
  function pickCell(day: string, start: string) {
    if (!service || submitting || day < todayDate()) return;
    const found = miniWeek?.days.find((d) => d.date === day)?.slots.find((x) => x.start === start);
    if (!found || !found.available) return;
    setDate(day);
    void pickSlot(found, service, day);
  }

  // service/date explicits: pickSlot tambe es crida des de loadMini (estat encara no actualitzat).
  async function pickSlot(s: ServiceWeekSlot, svc: Service | null = service, day: string | null = date) {
    if (!svc || !day) return;
    const id = ++adviceReq.current;
    setAdviceDismissed(false);
    setSlot(s);
    setAdvice(null);
    setAdviceFailed(false);
    setAdviceNoData(null);
    setSubmitError(null);

    // Nomes es demana recomanacio si hi ha previsio valida per a la franja. Si el backend ja ha dit
    // que no hi ha previsio (pistes, serveis sense forecast validat), no es crida ni es mostra SAFi.
    const forecast = forecastRef.current;
    if (forecast) {
      const f = forecast.days.find((d) => d.date === day)?.slots.find((x) => x.hour === s.start);
      if (!f || f.occupancy_score == null || f.occupancy_level === 'unknown') {
        setAdviceLoading(false);
        return;
      }
    }

    setAdviceLoading(true);
    try {
      const rec = await postRecommendations({
        service_id: svc.id,
        date: day,
        preferred_start: s.start,
        preferred_end: s.end,
      });
      if (id !== adviceReq.current) return;
      if (rec.recommendation_available === false) {
        // Sense recomanacio valida: no hi ha targeta SAFi.
        setAdvice(null);
        setAdviceNoData(null);
        setAdviceLoading(false);
        return;
      }
      setAdvice(rec);
    } catch (err) {
      if (id !== adviceReq.current) return;
      // SAFi no bloqueja la reserva en cap cas.
      if (err instanceof ApiError && err.code === 'OCCUPANCY_DATA_UNAVAILABLE') {
        setAdviceNoData(errorMessage(err));
      } else {
        setAdviceFailed(true);
      }
    }
    if (id === adviceReq.current) setAdviceLoading(false);
  }

  async function confirm() {
    if (!service || !date || !slot || submitting) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      // Reserva per servei: space_id omes, el backend autoassigna el recurs.
      const reservation = await createReservation({
        service_id: service.id,
        space_id: null,
        date,
        start: slot.start,
        end: slot.end,
      });
      setSubmitting(false);
      sendRecommendationAction(advice, 'ignored');
      navigation.navigate('Confirmacion', { reservation, serviceName: service.name });
    } catch (err) {
      setSubmitting(false);
      setSubmitError(errorMessage(err));
      if (err instanceof ApiError && err.code === 'SLOT_NOT_AVAILABLE') {
        // La franja s'ha ocupat: es treu la seleccio i es recarrega la disponibilitat des de l'API.
        adviceReq.current++;
        setSlot(null);
        setAdvice(null);
        setAdviceLoading(false);
        void loadMini(service);
      }
    }
  }

  // Mini heatmap: files i cel·les venen del backend; res es calcula aqui.
  const mini = useMemo(() => {
    const rowSet = new Set<string>();
    const cells = new Map<string, CellValue>();
    const full = new Set<string>();
    let hasData = false;
    if (miniMode === 'availability' && miniWeek) {
      for (const day of miniWeek.days) {
        for (const s of day.slots) {
          rowSet.add(s.start);
          cells.set(`${day.date}|${s.start}`, serviceSlotCell(s));
          if (!s.available) full.add(`${day.date}|${s.start}`);
          hasData = true;
        }
      }
    } else if (miniMode === 'forecast' && miniForecast) {
      for (const day of miniForecast.days) {
        for (const s of day.slots) {
          rowSet.add(s.hour);
          cells.set(`${day.date}|${s.hour}`, forecastCell(s));
          if (s.occupancy_score != null && s.occupancy_level !== 'unknown') hasData = true;
        }
      }
    }
    return {
      loaded: miniMode === 'availability' ? miniWeek !== null : miniForecast !== null,
      hasData,
      rows: Array.from(rowSet).sort(),
      getCell: (d: string, r: string) => cells.get(`${d}|${r}`) ?? null,
      isFull: (d: string, r: string) => full.has(`${d}|${r}`),
    };
  }, [miniMode, miniWeek, miniForecast]);

  // Previsio de la franja triada (heatmap per servei). Sense score valid -> "Sense dades de previsió".
  const slotForecast =
    date && slot
      ? miniForecast?.days.find((d) => d.date === date)?.slots.find((x) => x.hour === slot.start)
      : undefined;
  const forecastValid =
    !!slotForecast && slotForecast.occupancy_score != null && slotForecast.occupancy_level !== 'unknown';

  // Alternativa recomanada pel backend: nomes si ja es a la disponibilitat carregada i esta lliure.
  const recommended = advice?.recommended_slot ?? null;
  const altSlot =
    recommended && slot && date && recommended.start !== slot.start
      ? miniWeek?.days
          .find((d) => d.date === date)
          ?.slots.find((x) => x.start === recommended.start && x.available)
      : undefined;

  // La seccio SAFi nomes apareix si hi ha alguna cosa de SAFi per mostrar.
  const hasSafi =
    adviceLoading ||
    (!!advice && !adviceDismissed) ||
    (!!adviceNoData && !adviceDismissed) ||
    adviceFailed;

  return (
    <ScreenContainer>
      {/* 1. Servei */}
      <Text style={styles.step}>1. Servei</Text>
      {servicesLoading && <LoadingState lines={2} />}
      {servicesError && <ErrorState message={servicesError} onRetry={loadServices} />}
      <View style={styles.chips}>
        {(service ? [service] : services)?.map((s) => (
          <Chip
            key={s.id}
            label={s.name}
            selected={service?.id === s.id}
            disabled={submitting}
            onPress={() => pickService(s)}
          />
        ))}
      </View>
      {service && (
        <Text style={styles.muted}>
          Toca de nou el servei seleccionat per canviar d'esport.
        </Text>
      )}

      {/* 2. Mini heatmap */}
      {service && (
        <>
          <Text style={styles.step}>2. Dia i hora</Text>
          <View style={styles.chips}>
            <Chip
              label="Disponibilitat"
              selected={miniMode === 'availability'}
              disabled={submitting}
              onPress={() => setMiniMode('availability')}
            />
            <Chip
              label="Previsió SAFi"
              selected={miniMode === 'forecast'}
              disabled={submitting}
              onPress={() => setMiniMode('forecast')}
            />
          </View>
          <View style={[styles.zone, miniMode === 'forecast' && styles.zoneForecast]}>
            <Text style={[styles.zoneTitle, miniMode === 'forecast' && styles.zoneTitleForecast]}>
              {miniMode === 'availability' ? 'Disponibilitat actual' : 'Previsió SAFi'}
            </Text>
            <Text style={styles.zoneText}>
              {miniMode === 'availability'
                ? 'Disponibilitat: reserves actuals. Toca una cel·la per triar-la.'
                : 'Previsió SAFi: estimació històrica, no és ocupació en temps real.'}
            </Text>
          </View>
          {miniLoading && <LoadingState lines={4} />}
          {miniError && <ErrorState message={miniError} onRetry={() => loadMini(service)} />}
          {!miniLoading && !miniError && mini.loaded && !mini.hasData && (
            <EmptyState
              icon={miniMode === 'forecast' ? '📉' : '🗓️'}
              title={
                miniMode === 'forecast'
                  ? forecastFailed
                    ? "No s'ha pogut carregar la previsió"
                    : 'Sense dades de previsió'
                  : 'No hi ha franges per a aquests dies'
              }
            />
          )}
          {!miniLoading && !miniError && mini.loaded && mini.hasData && (
            <Card style={styles.gridCard}>
              <HeatmapGrid
                compact
                dates={dayDates}
                rows={mini.rows}
                getCell={mini.getCell}
                mode={miniMode}
                onCellPress={pickCell}
                isDisabled={mini.isFull}
                selected={date && slot ? { date, row: slot.start } : null}
              />
            </Card>
          )}

          <Text style={styles.muted}>
            Selecciona el dia i l'hora directament al heatmap. El recurs (pista, carril…) l'assigna el sistema en confirmar.
          </Text>
        </>
      )}

      {date && slot && (
        <View style={styles.selectionBox} accessibilityLiveRegion="polite">
          <Text style={styles.selectionLabel}>Reserva seleccionada</Text>
          <Text style={styles.selectionMain}>
            {service?.name} · {weekdayLong(date)} {date} · {slot.start}-{slot.end}
          </Text>
        </View>
      )}

      {/* Franja seleccionada: dos blocs separats */}
      {slot && service && (
        <View style={styles.infoRow}>
          <View style={styles.infoBox}>
            <Text style={styles.infoTitle}>Disponibilitat actual</Text>
            <Text style={styles.infoMain}>{slot.available ? 'Disponible' : 'Plena'}</Text>
            <Text style={styles.infoSub}>{capacityText(service.id, slot)}</Text>
          </View>
          <View style={[styles.infoBox, styles.infoBoxForecast]}>
            <Text style={[styles.infoTitle, styles.infoTitleForecast]}>Previsió SAFi</Text>
            {forecastValid && slotForecast ? (
              <>
                <Text style={styles.infoMain}>Ocupació {LEVEL_LABEL[slotForecast.occupancy_level]}</Text>
                <Text style={styles.infoSub}>{slotForecast.occupancy_score} / 100</Text>
              </>
            ) : (
              <Text style={styles.infoMain}>
                {forecastFailed ? 'Previsió no disponible' : 'Sense dades de previsió'}
              </Text>
            )}
          </View>
        </View>
      )}

      {/* 3. Avis SAFi + 4. Confirmar */}
      {slot && (
        <>
          {hasSafi && <Text style={styles.step}>3. SAFi</Text>}
          {adviceLoading && <LoadingState lines={2} />}
          {advice && !adviceDismissed && (
            <View style={styles.safiBox}>
              <Pressable
                style={styles.dismiss}
                hitSlop={10}
                accessibilityLabel="Tancar l'avís de SAFi"
                onPress={() => setAdviceDismissed(true)}
              >
                <Text style={styles.dismissText}>✕</Text>
              </Pressable>
              <Text style={styles.safiTitle}>SAFi</Text>
              <Text style={styles.safiText}>{advice.message}</Text>
              {altSlot && (
                <Button
                  label={`Canviar a ${altSlot.start}`}
                  disabled={submitting}
                  style={styles.altButton}
                  onPress={() => {
                    sendRecommendationAction(advice, 'accepted');
                    setSlot(altSlot);
                    setAdvice(null);
                    setAdviceNoData(null);
                    setAdviceFailed(false);
                  }}
                />
              )}
            </View>
          )}
          {adviceNoData && !adviceDismissed && (
            <View style={styles.safiBox}>
              <Pressable
                style={styles.dismiss}
                hitSlop={10}
                accessibilityLabel="Tancar l'avís de SAFi"
                onPress={() => setAdviceDismissed(true)}
              >
                <Text style={styles.dismissText}>✕</Text>
              </Pressable>
              <Text style={styles.safiTitle}>SAFi</Text>
              <Text style={styles.safiText}>{adviceNoData}</Text>
            </View>
          )}
          {adviceFailed && (
            <Text style={styles.muted}>SAFi no està disponible ara mateix. Pots confirmar igualment.</Text>
          )}

          <Text style={styles.step}>{hasSafi ? '4. Confirmar' : '3. Confirmar'}</Text>
          {submitError && (
            <View style={styles.errorBox} accessibilityRole="alert">
              <Text style={styles.error}>{submitError}</Text>
            </View>
          )}
          <Button
            label={submitting ? 'Reservant...' : `Confirmar ${slot.start}`}
            disabled={submitting}
            onPress={() => void confirm()}
            style={styles.confirm}
          />
        </>
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  step: { ...typography.heading, marginTop: spacing.xl, marginBottom: spacing.sm },
  muted: { ...typography.caption, marginVertical: spacing.sm },
  error: { color: colors.danger, fontWeight: '600' },
  errorBox: { backgroundColor: colors.dangerSoft, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.sm },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  zone: {
    marginTop: spacing.md,
    marginBottom: spacing.sm,
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
  gridCard: { padding: spacing.md },
  safiBox: {
    padding: spacing.lg,
    borderRadius: radius.lg,
    backgroundColor: colors.safiSoft,
    borderWidth: 1,
    borderColor: colors.safi,
  },
  dismiss: { position: 'absolute', top: 0, right: 0, width: 44, height: 44, alignItems: 'center', justifyContent: 'center', zIndex: 1 },
  dismissText: { fontSize: 18, color: colors.safi },
  selectionBox: {
    marginTop: spacing.lg,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.primarySoft,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  selectionLabel: { ...typography.caption },
  selectionMain: { marginTop: 3, fontSize: 16, fontWeight: '800', color: colors.primaryDark },
  infoRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
  infoBox: {
    flex: 1,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  infoBoxForecast: { backgroundColor: colors.safiSoft, borderColor: colors.safiSoft },
  infoTitle: { ...typography.caption, fontSize: 12, marginBottom: spacing.xs },
  infoTitleForecast: { color: colors.safi, fontWeight: '700' },
  infoMain: { fontSize: 15, fontWeight: '700', color: colors.text },
  infoSub: { fontSize: 14, color: colors.textMuted, marginTop: 2 },
  safiTitle: { fontWeight: '800', color: colors.safi, marginBottom: spacing.xs },
  safiText: { fontSize: 16, color: colors.text, paddingRight: spacing.xl },
  altButton: { marginTop: spacing.md },
  confirm: { minHeight: 56 },
});
