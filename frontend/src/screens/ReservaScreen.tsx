import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import HeatmapGrid, { availabilityCell, forecastCell } from '../components/HeatmapGrid';
import type { CellValue, HeatmapMode } from '../components/HeatmapGrid';
import type { RootStackParamList } from '../navigation/types';
import {
  ApiError,
  createReservation,
  errorMessage,
  getAvailability,
  getAvailabilityWeek,
  getHeatmap,
  getServices,
  postRecommendationAction,
  postRecommendations,
} from '../services/api';
import type {
  Availability,
  AvailabilityWeek,
  Heatmap,
  OccupancyLevel,
  Recommendation,
  Service,
  Slot,
} from '../services/api';
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
  const [miniWeek, setMiniWeek] = useState<AvailabilityWeek | null>(null);
  const [miniForecast, setMiniForecast] = useState<Heatmap | null>(null);
  const [miniLoading, setMiniLoading] = useState(false);
  const [miniError, setMiniError] = useState<string | null>(null);
  const miniReq = useRef(0);
  const paramsApplied = useRef(false);

  // Pas 1: servei
  const [services, setServices] = useState<Service[] | null>(null);
  const [servicesLoading, setServicesLoading] = useState(true);
  const [servicesError, setServicesError] = useState<string | null>(null);
  const [service, setService] = useState<Service | null>(null);

  // Pas 2: dia
  const [date, setDate] = useState<string | null>(null);

  // Pas 3: hora
  const [availability, setAvailability] = useState<Availability | null>(null);
  const [availLoading, setAvailLoading] = useState(false);
  const [availError, setAvailError] = useState<string | null>(null);
  const [slot, setSlot] = useState<Slot | null>(null);

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
  const availReq = useRef(0);
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

      // Parametres de navegacio (des del Heatmap): preseleccio de servei, dia i franja.
      const params = route.params;
      if (params?.serviceId && !paramsApplied.current) {
        paramsApplied.current = true;
        const wanted = reservable.find((s) => s.id === params.serviceId);
        if (wanted) {
          setService(wanted);
          if (params.date) {
            setDate(params.date);
            void loadAvailability(
              wanted.space_id,
              params.date,
              params.start ? { service: wanted, start: params.start } : undefined,
            );
          }
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

  // Mini heatmap: es recarrega en canviar servei o mode.
  const loadMini = useCallback(async (s: Service, mode: HeatmapMode) => {
    const id = ++miniReq.current;
    setMiniWeek(null);
    setMiniForecast(null);
    setMiniError(null);
    setMiniLoading(true);
    const from = todayDate();
    const to = addDays(from, 6);
    try {
      if (mode === 'availability') {
        const result = await getAvailabilityWeek(s.space_id, from, to);
        if (id !== miniReq.current) return;
        setMiniWeek(result);
      } else {
        const result = await getHeatmap(s.space_id, from, to);
        if (id !== miniReq.current) return;
        setMiniForecast(result);
      }
    } catch (err) {
      if (id !== miniReq.current) return;
      setMiniError(errorMessage(err));
    }
    if (id === miniReq.current) setMiniLoading(false);
  }, []);

  useEffect(() => {
    if (service) void loadMini(service, miniMode);
  }, [service, miniMode, loadMini]);

  const loadAvailability = useCallback(
    async (spaceId: string, day: string, preselect?: { service: Service; start: string }) => {
    const id = ++availReq.current;
    adviceReq.current++;
    setAdviceDismissed(false);
    setAvailLoading(true);
    setAvailError(null);
    setAvailability(null);
    setSlot(null);
    setAdvice(null);
    setAdviceLoading(false);
    setAdviceFailed(false);
    setAdviceNoData(null);
    try {
      const result = await getAvailability(spaceId, day);
      if (id !== availReq.current) return;
      setAvailability(result);
      // Franja demanada per parametre o per cel·la del heatmap: nomes si esta disponible.
      const wanted = preselect && result.slots.find((s) => s.start === preselect.start && s.available);
      if (wanted && preselect) void pickSlot(wanted, preselect.service, day);
    } catch (err) {
      if (id !== availReq.current) return;
      setAvailError(errorMessage(err));
    }
    if (id === availReq.current) setAvailLoading(false);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  function resetSelection() {
    availReq.current++;
    adviceReq.current++;
    miniReq.current++;
    setService(null);
    setDate(null);
    setAvailability(null);
    setAvailLoading(false);
    setAvailError(null);
    setSlot(null);
    setAdvice(null);
    setAdviceLoading(false);
    setAdviceFailed(false);
    setAdviceNoData(null);
    setAdviceDismissed(false);
    setSubmitError(null);
    setMiniWeek(null);
    setMiniForecast(null);
    setMiniLoading(false);
    setMiniError(null);
  }

  function pickService(s: Service) {
    if (service?.id === s.id) {
      resetSelection();
      return;
    }

    availReq.current++;
    adviceReq.current++;
    setService(s);
    setAdviceDismissed(false);
    setDate(null);
    setAvailability(null);
    setAvailLoading(false);
    setAvailError(null);
    setSlot(null);
    setAdvice(null);
    setAdviceLoading(false);
    setAdviceFailed(false);
    setAdviceNoData(null);
    setSubmitError(null);
  }

  // Cel·la del mini heatmap: selecciona dia i franja automaticament.
  function pickCell(day: string, start: string) {
    if (!service || submitting) return;
    setDate(day);
    setSubmitError(null);
    void loadAvailability(service.space_id, day, { service, start });
  }

  // service/date explicits: pickSlot tambe es crida des de loadAvailability (estat encara no actualitzat).
  async function pickSlot(s: Slot, svc: Service | null = service, day: string | null = date) {
    if (!svc || !day) return;
    const id = ++adviceReq.current;
    setAdviceDismissed(false);
    setSlot(s);
    setAdvice(null);
    setAdviceFailed(false);
    setAdviceNoData(null);
    setAdviceLoading(true);
    setSubmitError(null);
    try {
      const rec = await postRecommendations({
        space_id: svc.space_id,
        date: day,
        preferred_start: s.start,
        preferred_end: s.end,
      });
      if (id !== adviceReq.current) return;
      if (rec.recommendation_available === false) {
        setAdvice(null);
        setAdviceNoData(null);
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
      const reservation = await createReservation({
        space_id: service.space_id,
        date,
        start: slot.start,
        end: slot.end,
      });
      setSubmitting(false);
      sendRecommendationAction(advice, 'ignored');
      navigation.navigate('Confirmacion', { reservation, spaceName: service.name });
    } catch (err) {
      setSubmitting(false);
      setSubmitError(errorMessage(err));
      if (err instanceof ApiError && err.code === 'SLOT_NOT_AVAILABLE') {
        void loadAvailability(service.space_id, date);
      }
    }
  }

  // Mini heatmap: files i cel·les vénen del backend; res es calcula aqui.
  const mini = useMemo(() => {
    const rowSet = new Set<string>();
    const cells = new Map<string, CellValue>();
    const full = new Set<string>();
    let hasData = false;
    if (miniMode === 'availability' && miniWeek) {
      for (const day of miniWeek.days) {
        for (const s of day.slots) {
          rowSet.add(s.start);
          cells.set(`${day.date}|${s.start}`, availabilityCell(s));
          if (!s.available) full.add(`${day.date}|${s.start}`);
          hasData = true;
        }
      }
    } else if (miniMode === 'forecast' && miniForecast) {
      for (const day of miniForecast.days) {
        for (const s of day.slots) {
          rowSet.add(s.hour);
          cells.set(`${day.date}|${s.hour}`, forecastCell(s));
          if (s.occupancy_level !== 'unknown') hasData = true;
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

  // Alternativa recomanada pel backend: nomes si ja esta a la llista carregada i disponible.
  const recommended = advice?.recommended_slot ?? null;
  const altSlot =
    recommended && slot && recommended.start !== slot.start
      ? availability?.slots.find((s) => s.start === recommended.start && s.available)
      : undefined;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* 1. Servei */}
      <Text style={styles.step}>1. Servei</Text>
      {servicesLoading && <ActivityIndicator />}
      {servicesError && <ErrorBox text={servicesError} onRetry={loadServices} />}
      {(service ? [service] : services)?.map((s) => (
        <Option
          key={s.id}
          label={s.name}
          selected={service?.id === s.id}
          disabled={submitting}
          onPress={() => pickService(s)}
        />
      ))}
      {service && (
        <Text style={styles.muted}>
          Toca de nou el servei seleccionat per canviar d'esport.
        </Text>
      )}

      {/* 2. Mini heatmap */}
      {service && (
        <>
          <Text style={styles.step}>2. Disponibilitat i previsió</Text>
          <View style={styles.modeRow}>
            <Option
              label="Disponibilitat"
              selected={miniMode === 'availability'}
              disabled={submitting}
              onPress={() => setMiniMode('availability')}
            />
            <Option
              label="Previsió SAFi"
              selected={miniMode === 'forecast'}
              disabled={submitting}
              onPress={() => setMiniMode('forecast')}
            />
          </View>
          <Text style={styles.muted}>
            {miniMode === 'availability'
              ? 'Disponibilitat: reserves actuals. Toca una cel·la per triar-la.'
              : 'Previsió SAFi: estimació històrica, no és ocupació en temps real.'}
          </Text>
          {miniLoading && <ActivityIndicator />}
          {miniError && <ErrorBox text={miniError} onRetry={() => loadMini(service, miniMode)} />}
          {!miniLoading && !miniError && mini.loaded && !mini.hasData && (
            <Text style={styles.muted}>
              {miniMode === 'forecast' ? 'Sense dades de previsió' : 'No hi ha franges per a aquests dies'}
            </Text>
          )}
          {!miniLoading && !miniError && mini.loaded && mini.hasData && (
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
          )}

          {availLoading && <ActivityIndicator />}
          {availError && date && (
            <ErrorBox
              text={availError}
              onRetry={() =>
                loadAvailability(
                  service.space_id,
                  date,
                  slot ? { service, start: slot.start } : undefined,
                )
              }
            />
          )}
          <Text style={styles.muted}>
            Selecciona el dia i l'hora directament al heatmap.
          </Text>
        </>
      )}

      {date && slot && (
        <View style={styles.selectionBox}>
          <Text style={styles.selectionLabel}>Reserva seleccionada</Text>
          <Text style={styles.selectionMain}>
            {service?.name} · {weekdayLong(date)} {date} · {slot.start}-{slot.end}
          </Text>
        </View>
      )}

      {/* Franja seleccionada: dos blocs separats */}
      {slot && (
        <View style={styles.infoRow}>
          <View style={styles.infoBox}>
            <Text style={styles.infoTitle}>Disponibilitat actual</Text>
            <Text style={styles.infoMain}>{slot.available ? 'Disponible' : 'No disponible'}</Text>
            <Text style={styles.infoSub}>
              {slot.remaining_capacity != null
                ? `${slot.remaining_capacity} places`
                : 'Places: desconegudes'}
            </Text>
          </View>
          <View style={styles.infoBox}>
            <Text style={styles.infoTitle}>Previsió SAFi</Text>
            <Text style={styles.infoMain}>Ocupació {LEVEL_LABEL[slot.occupancy_level]}</Text>
            <Text style={styles.infoSub}>
              {slot.occupancy_score != null ? `${slot.occupancy_score} / 100` : 'Puntuació desconeguda'}
            </Text>
          </View>
        </View>
      )}

      {/* 3. Avis SAFi + 4. Confirmar */}
      {slot && (
        <>
          <Text style={styles.step}>3. SAFi</Text>
          {adviceLoading && <ActivityIndicator />}
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
                <Pressable
                  style={styles.altButton}
                  disabled={submitting}
                  onPress={() => {
                    sendRecommendationAction(advice, 'accepted');
                    setSlot(altSlot);
                    setAdvice(null);
                    setAdviceNoData(null);
                    setAdviceFailed(false);
                  }}
                >
                  <Text style={styles.altButtonText}>Canviar a {altSlot.start}</Text>
                </Pressable>
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

          <Text style={styles.step}>4. Confirmar</Text>
          {submitError && <Text style={styles.error}>{submitError}</Text>}
          <Pressable
            style={[styles.confirmButton, submitting && styles.disabled]}
            disabled={submitting}
            onPress={() => void confirm()}
          >
            <Text style={styles.confirmText}>
              {submitting ? 'Reservant...' : `Confirmar ${slot.start}`}
            </Text>
          </Pressable>
        </>
      )}
    </ScrollView>
  );
}

function Option(props: { label: string; selected: boolean; disabled: boolean; onPress: () => void }) {
  return (
    <Pressable
      style={[styles.option, props.selected && styles.optionSelected, props.disabled && styles.disabled]}
      disabled={props.disabled}
      onPress={props.onPress}
    >
      <Text style={styles.optionText}>{props.label}</Text>
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
  step: { fontSize: 18, fontWeight: 'bold', marginTop: 20, marginBottom: 8 },
  muted: { color: '#666', marginVertical: 8 },
  error: { color: '#b00020', marginVertical: 8 },
  option: { padding: 14, borderRadius: 10, borderWidth: 1, borderColor: '#ccc', marginBottom: 8 },
  optionSelected: { borderColor: '#1565c0', backgroundColor: '#e3f0ff' },
  optionText: { fontSize: 16 },
  disabled: { opacity: 0.4 },
  retryButton: { padding: 12, borderRadius: 10, backgroundColor: '#eee', alignItems: 'center' },
  retryText: { fontSize: 16 },
  safiBox: { padding: 14, borderRadius: 12, backgroundColor: '#f3e8ff', borderWidth: 1, borderColor: '#9c27b0' },
  dismiss: { position: 'absolute', top: 8, right: 10, zIndex: 1 },
  dismissText: { fontSize: 18, color: '#6a1b9a' },
  modeRow: { flexDirection: 'row', gap: 8 },
  selectionBox: { marginTop: 16, padding: 12, borderRadius: 10, backgroundColor: '#e3f0ff' },
  selectionLabel: { fontSize: 12, color: '#555' },
  selectionMain: { marginTop: 3, fontSize: 16, fontWeight: 'bold' },
  infoRow: { flexDirection: 'row', gap: 8, marginTop: 10 },
  infoBox: { flex: 1, padding: 12, borderRadius: 10, borderWidth: 1, borderColor: '#ccc' },
  infoTitle: { fontSize: 12, color: '#666', marginBottom: 4 },
  infoMain: { fontSize: 15, fontWeight: 'bold' },
  infoSub: { fontSize: 14, color: '#444', marginTop: 2 },
  safiTitle: { fontWeight: 'bold', color: '#6a1b9a', marginBottom: 4 },
  safiText: { fontSize: 16 },
  altButton: { marginTop: 12, padding: 12, borderRadius: 10, backgroundColor: '#9c27b0', alignItems: 'center' },
  altButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  confirmButton: { padding: 18, borderRadius: 12, backgroundColor: '#1565c0', alignItems: 'center' },
  confirmText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});
