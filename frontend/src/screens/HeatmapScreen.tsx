import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { errorMessage, getHeatmap, getServices } from '../services/api';
import type { Heatmap, OccupancyLevel, Service } from '../services/api';

const LEVEL_LABEL: Record<OccupancyLevel, string> = {
  low: 'baixa',
  medium: 'mitjana',
  high: 'alta',
  very_high: 'molt alta',
  unknown: 'desconeguda',
};

const LEVEL_COLOR: Record<OccupancyLevel, string> = {
  low: '#c8e6c9',
  medium: '#fff9c4',
  high: '#ffcc80',
  very_high: '#ef9a9a',
  unknown: '#e0e0e0',
};

const pad = (n: number) => String(n).padStart(2, '0');

// Data LOCAL en format YYYY-MM-DD (no toISOString, que dona UTC).
function localDate(offsetDays: number): string {
  const now = new Date();
  const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + offsetDays);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export default function HeatmapScreen() {
  // Els 7 dies des d'avui.
  const from = useMemo(() => localDate(0), []);
  const to = useMemo(() => localDate(6), []);

  const [services, setServices] = useState<Service[] | null>(null);
  const [servicesLoading, setServicesLoading] = useState(true);
  const [servicesError, setServicesError] = useState<string | null>(null);
  const [service, setService] = useState<Service | null>(null);

  const [heatmap, setHeatmap] = useState<Heatmap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const servicesReq = useRef(0);
  const heatmapReq = useRef(0);

  const loadServices = useCallback(async () => {
    const id = ++servicesReq.current;
    setServicesLoading(true);
    setServicesError(null);
    try {
      const list = await getServices();
      if (id !== servicesReq.current) return;
      setServices(list);
    } catch (err) {
      if (id !== servicesReq.current) return;
      setServicesError(errorMessage(err));
    }
    if (id === servicesReq.current) setServicesLoading(false);
  }, []);

  useEffect(() => {
    void loadServices();
  }, [loadServices]);

  const loadHeatmap = useCallback(
    async (spaceId: string) => {
      const id = ++heatmapReq.current;
      setLoading(true);
      setError(null);
      setHeatmap(null);
      try {
        const result = await getHeatmap(spaceId, from, to);
        if (id !== heatmapReq.current) return;
        setHeatmap(result);
      } catch (err) {
        if (id !== heatmapReq.current) return;
        setError(errorMessage(err));
      }
      if (id === heatmapReq.current) setLoading(false);
    },
    [from, to],
  );

  function pickService(s: Service) {
    setService(s);
    void loadHeatmap(s.space_id);
  }

  // Columnes de la graella: les hores que retorna el backend (sense calcular ocupacio).
  const hours = useMemo(() => {
    const set = new Set<string>();
    heatmap?.days.forEach((day) => day.slots.forEach((slot) => set.add(slot.hour)));
    return Array.from(set).sort();
  }, [heatmap]);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.step}>1. Servei</Text>
      {servicesLoading && <ActivityIndicator />}
      {servicesError && <ErrorBox text={servicesError} onRetry={loadServices} />}
      {services?.map((s) => (
        <Pressable
          key={s.id}
          style={[styles.option, service?.id === s.id && styles.optionSelected]}
          onPress={() => pickService(s)}
        >
          <Text style={styles.optionText}>{s.name}</Text>
        </Pressable>
      ))}

      {service && (
        <>
          <Text style={styles.step}>
            2. Ocupació ({from} a {to})
          </Text>
          {loading && <ActivityIndicator />}
          {error && <ErrorBox text={error} onRetry={() => loadHeatmap(service.space_id)} />}
          {heatmap && heatmap.days.length === 0 && (
            <Text style={styles.muted}>No hi ha dades per a aquest període</Text>
          )}
          {heatmap && heatmap.days.length > 0 && (
            <ScrollView horizontal>
              <View>
                <View style={styles.row}>
                  <Text style={[styles.dayCell, styles.header]}>Dia</Text>
                  {hours.map((h) => (
                    <Text key={h} style={[styles.cell, styles.header]}>
                      {h}
                    </Text>
                  ))}
                </View>
                {heatmap.days.map((day) => (
                  <View key={day.date} style={styles.row}>
                    <Text style={styles.dayCell}>{day.date.slice(5)}</Text>
                    {hours.map((h) => {
                      const slot = day.slots.find((s) => s.hour === h);
                      const level = slot?.occupancy_level ?? 'unknown';
                      return (
                        <View
                          key={h}
                          style={[styles.cell, { backgroundColor: LEVEL_COLOR[level] }]}
                        >
                          <Text style={styles.cellText}>{LEVEL_LABEL[level]}</Text>
                          {slot?.occupancy_score != null && (
                            <Text style={styles.cellScore}>{slot.occupancy_score}</Text>
                          )}
                        </View>
                      );
                    })}
                  </View>
                ))}
              </View>
            </ScrollView>
          )}
        </>
      )}
    </ScrollView>
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
  retryButton: { padding: 12, borderRadius: 10, backgroundColor: '#eee', alignItems: 'center' },
  retryText: { fontSize: 16 },
  row: { flexDirection: 'row' },
  header: { fontWeight: 'bold', textAlign: 'center' },
  dayCell: { width: 56, padding: 6, fontSize: 13 },
  cell: { width: 72, padding: 6, borderWidth: 1, borderColor: '#fff', alignItems: 'center' },
  cellText: { fontSize: 12 },
  cellScore: { fontSize: 11, color: '#444' },
});
