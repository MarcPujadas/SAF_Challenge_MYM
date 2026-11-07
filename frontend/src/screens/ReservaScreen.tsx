import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import type { RootStackParamList } from '../navigation/types';
import {
  ApiError,
  createReservation,
  errorMessage,
  getAvailability,
  getServices,
  postRecommendationAction,
  postRecommendations,
} from '../services/api';
import type { Availability, OccupancyLevel, Recommendation, Service, Slot } from '../services/api';

type Props = NativeStackScreenProps<RootStackParamList, 'Reserva'>;

const DAY_NAMES = ['Diumenge', 'Dilluns', 'Dimarts', 'Dimecres', 'Dijous', 'Divendres', 'Dissabte'];

const LEVEL_LABEL: Record<OccupancyLevel, string> = {
  low: 'baixa',
  medium: 'mitjana',
  high: 'alta',
  very_high: 'molt alta',
  unknown: 'desconeguda',
};

type Day = { date: string; name: string };

const pad = (n: number) => String(n).padStart(2, '0');

// Data LOCAL en format YYYY-MM-DD (no toISOString, que dona UTC).
function nextDays(): Day[] {
  const now = new Date();
  const days: Day[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + i);
    days.push({
      date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
      name: DAY_NAMES[d.getDay()],
    });
  }
  return days;
}

export default function ReservaScreen({ navigation }: Props) {
  const days = useMemo(nextDays, []);

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
    if (!rec || !rec.recommended_slot) return;
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
      setServices(list.filter((s) => s.reservable));
    } catch (err) {
      if (id !== servicesReq.current) return;
      setServicesError(errorMessage(err));
    }
    if (id === servicesReq.current) setServicesLoading(false);
  }, []);

  useEffect(() => {
    void loadServices();
  }, [loadServices]);

  const loadAvailability = useCallback(async (spaceId: string, day: string) => {
    const id = ++availReq.current;
    adviceReq.current++;
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
    } catch (err) {
      if (id !== availReq.current) return;
      setAvailError(errorMessage(err));
    }
    if (id === availReq.current) setAvailLoading(false);
  }, []);

  function pickService(s: Service) {
    availReq.current++;
    adviceReq.current++;
    setService(s);
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

  function pickDay(day: string) {
    if (!service) return;
    setDate(day);
    setSubmitError(null);
    void loadAvailability(service.space_id, day);
  }

  async function pickSlot(s: Slot) {
    if (!service || !date) return;
    const id = ++adviceReq.current;
    setSlot(s);
    setAdvice(null);
    setAdviceFailed(false);
    setAdviceNoData(null);
    setAdviceLoading(true);
    setSubmitError(null);
    try {
      const rec = await postRecommendations({
        space_id: service.space_id,
        date,
        preferred_start: s.start,
        preferred_end: s.end,
      });
      if (id !== adviceReq.current) return;
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
      if (
        err instanceof ApiError &&
        (err.code === 'SLOT_NOT_AVAILABLE' || err.code === 'RESERVATION_CONFLICT')
      ) {
        void loadAvailability(service.space_id, date);
      }
    }
  }

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
      {services?.map((s) => (
        <Option
          key={s.id}
          label={s.name}
          selected={service?.id === s.id}
          disabled={submitting}
          onPress={() => pickService(s)}
        />
      ))}

      {/* 2. Dia */}
      {service && (
        <>
          <Text style={styles.step}>2. Dia</Text>
          {days.map((d) => (
            <Option
              key={d.date}
              label={`${d.name} ${d.date}`}
              selected={date === d.date}
              disabled={submitting}
              onPress={() => pickDay(d.date)}
            />
          ))}
        </>
      )}

      {/* 3. Hora */}
      {service && date && (
        <>
          <Text style={styles.step}>3. Hora</Text>
          {availLoading && <ActivityIndicator />}
          {availError && (
            <ErrorBox text={availError} onRetry={() => loadAvailability(service.space_id, date)} />
          )}
          {availability && availability.slots.length === 0 && (
            <Text style={styles.muted}>No hi ha franges disponibles</Text>
          )}
          {availability?.slots.map((s) => (
            <Option
              key={`${s.start}-${s.end}`}
              label={`${s.start}-${s.end}  ·  ocupació ${LEVEL_LABEL[s.occupancy_level]}${
                s.available ? '' : '  ·  no disponible'
              }`}
              selected={slot?.start === s.start && slot?.end === s.end}
              disabled={!s.available || submitting}
              onPress={() => void pickSlot(s)}
            />
          ))}
        </>
      )}

      {/* 4. Avis SAFi + 5. Confirmar */}
      {slot && (
        <>
          <Text style={styles.step}>4. SAFi</Text>
          {adviceLoading && <ActivityIndicator />}
          {advice && (
            <View style={styles.safiBox}>
              <Text style={styles.safiTitle}>SAFi</Text>
              <Text style={styles.safiText}>{advice.message}</Text>
              {altSlot && (
                <Pressable
                  style={styles.altButton}
                  disabled={submitting}
                  onPress={() => {
                    sendRecommendationAction(advice, 'accepted');
                    void pickSlot(altSlot);
                  }}
                >
                  <Text style={styles.altButtonText}>Canviar a {altSlot.start}</Text>
                </Pressable>
              )}
            </View>
          )}
          {adviceNoData && (
            <View style={styles.safiBox}>
              <Text style={styles.safiTitle}>SAFi</Text>
              <Text style={styles.safiText}>{adviceNoData}</Text>
            </View>
          )}
          {adviceFailed && (
            <Text style={styles.muted}>SAFi no està disponible ara mateix. Pots confirmar igualment.</Text>
          )}

          <Text style={styles.step}>5. Confirmar</Text>
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
  safiTitle: { fontWeight: 'bold', color: '#6a1b9a', marginBottom: 4 },
  safiText: { fontSize: 16 },
  altButton: { marginTop: 12, padding: 12, borderRadius: 10, backgroundColor: '#9c27b0', alignItems: 'center' },
  altButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  confirmButton: { padding: 18, borderRadius: 12, backgroundColor: '#1565c0', alignItems: 'center' },
  confirmText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});
