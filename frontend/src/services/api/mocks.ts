// Dades sintetiques amb la forma exacta de contracts.md (model multiespai: service_id -> subespais).
// Cap dada real del SAF. Nomes s'usen amb EXPO_PUBLIC_USE_MOCKS=true; el flux principal va contra el backend.
// Els mocks imiten el backend (autoassignacio del primer subespai lliure); l'app real no calcula res d'aixo.

import { ApiError } from './client';

import type {
  CapacityMode,
  Heatmap,
  HeatmapSlot,
  OccupancyLevel,
  Recommendation,
  RecommendationAction,
  RecommendationActionType,
  RecommendationRequest,
  ReservationCancelled,
  ReservationCreated,
  ReservationItem,
  ReservationRequest,
  SafiChatRequest,
  SafiChatResponse,
  Service,
  ServiceAvailabilityWeek,
  ServiceSpace,
  ServiceWeekSlot,
} from './types';

const delay = () => new Promise<void>((resolve) => setTimeout(resolve, 250));

// ---------------------------------------------------------
// Serveis i subespais (recursos). L'usuari tria servei; el recurs l'assigna el backend.
// ---------------------------------------------------------

type MockService = {
  service: Service;
  resources: { space_id: string; name: string }[];
  personCapacity: number | null; // nomes serveis 'people'
  slotMinutes: 75 | 60;
  forecastValidated: boolean;
};

function units(prefix: string, label: string, count: number) {
  return Array.from({ length: count }, (_, i) => ({
    space_id: `${prefix}-${i + 1}`,
    name: `${label} ${i + 1}`,
  }));
}

function mockService(
  id: string,
  name: string,
  description: string,
  resources: { space_id: string; name: string }[],
  mode: CapacityMode,
  personCapacity: number | null,
  slotMinutes: 75 | 60,
  forecastValidated: boolean,
): MockService {
  return {
    service: {
      id,
      name,
      description,
      space_id: resources[0].space_id,
      reservable: true,
      resource_count: resources.length,
      capacity_mode: mode,
    },
    resources,
    personCapacity,
    slotMinutes,
    forecastValidated,
  };
}

const MOCK_SERVICES: MockService[] = [
  mockService('fitness', 'Fitness', 'Sala de fitness i cardio',
    [{ space_id: 'sala-fitnes-sala-cardio', name: 'Sala fitnes + sala cardio' }], 'people', 120, 75, true),
  mockService('pool-25m', 'Piscina 25 m', 'Piscina de 25 metres',
    units('piscina-25-metres-carrer', 'Carrer', 6), 'unit', null, 60, true),
  mockService('pool-16m', 'Piscina 16 m', 'Piscina de 16 metres',
    units('piscina-de-16-metres-carrer', 'Carrer', 4), 'unit', null, 60, true),
  mockService('padel', 'Pàdel', 'Pistes de pàdel', units('pistes-de-padel-pista', 'Pista', 4), 'unit', null, 75, false),
  mockService('tennis', 'Tennis', 'Pistes de tennis', units('tennis-tennis', 'Pista', 5), 'unit', null, 75, false),
  mockService('squash', 'Esquaix', "Pistes d'esquaix", units('esquaix-esquaix', 'Pista', 3), 'unit', null, 75, false),
  mockService('football', 'Futbol', 'Camps de futbol', units('futbol-7-camp', 'Camp', 2), 'unit', null, 60, false),
  mockService('guided-activities', 'Activitats dirigides', "Sales d'activitats dirigides",
    [{ space_id: 'sales-activitats-dirigides-sala-1', name: "Sala d'activitats dirigides" }], 'people', 25, 60, true),
];

function requireService(serviceId: string): MockService {
  const found = MOCK_SERVICES.find((m) => m.service.id === serviceId);
  if (!found) {
    throw new ApiError('INVALID_SERVICE', `Servei desconegut: ${serviceId}`);
  }
  return found;
}

function resourceName(spaceId: string): string {
  for (const m of MOCK_SERVICES) {
    const r = m.resources.find((x) => x.space_id === spaceId);
    if (r) return r.name;
  }
  return spaceId;
}

// ---------------------------------------------------------
// Reserves en memoria (arrenquen buides)
// ---------------------------------------------------------

const reservations: ReservationCreated[] = [];
let nextId = 1;

// ---------------------------------------------------------
// Helpers de dates, franges i valors fixos
// ---------------------------------------------------------

const pad = (n: number) => String(n).padStart(2, '0');

function addMinutes(hhmm: string, minutes: number): string {
  const [h, m] = hhmm.split(':').map(Number);
  const total = h * 60 + m + minutes;
  return `${pad(Math.floor(total / 60))}:${pad(total % 60)}`;
}

// Dates YYYY-MM-DD en local (mai toISOString).
function rangeDates(from: string, to: string): string[] {
  const out: string[] = [];
  const [y, mo, d] = from.split('-').map(Number);
  const cur = new Date(y, mo - 1, d);
  for (let i = 0; i < 31; i++) {
    const s = `${cur.getFullYear()}-${pad(cur.getMonth() + 1)}-${pad(cur.getDate())}`;
    if (s > to) break;
    out.push(s);
    cur.setDate(cur.getDate() + 1);
  }
  return out;
}

// Franges per dia de la setmana (0 = diumenge), patro del backend.
const WEEKDAY_75 = ['07:15', '08:30', '09:45', '11:00', '12:15', '13:30', '14:45', '16:00', '17:15', '18:30', '19:45'];
const SLOTS_75: Record<number, string[]> = {
  1: WEEKDAY_75,
  2: WEEKDAY_75,
  3: WEEKDAY_75,
  4: WEEKDAY_75,
  5: WEEKDAY_75,
  6: ['08:30', '09:45', '11:00', '12:15', '13:30', '14:45', '16:00', '17:15', '18:30'],
  0: ['09:45', '11:00', '12:15'],
};
const OPENING: Record<number, [number, number]> = {
  1: [7, 21], 2: [7, 21], 3: [7, 21], 4: [7, 21], 5: [7, 21], 6: [8, 20], 0: [9, 14],
};

function slotsFor(m: MockService, date: string): { start: string; end: string }[] {
  const [y, mo, d] = date.split('-').map(Number);
  const weekday = new Date(y, mo - 1, d).getDay();
  if (m.slotMinutes === 75) {
    return (SLOTS_75[weekday] ?? []).map((start) => ({ start, end: addMinutes(start, 75) }));
  }
  const [open, close] = OPENING[weekday];
  const out: { start: string; end: string }[] = [];
  for (let h = open; h < close; h++) {
    const start = `${pad(h)}:00`;
    out.push({ start, end: addMinutes(start, 60) });
  }
  return out;
}

function mockNumber(key: string): number {
  let h = 0;
  for (const c of key) h = (h * 31 + c.charCodeAt(0)) % 9973;
  return h;
}

function confirmedAt(serviceId: string, date: string, start: string, spaceId?: string) {
  return reservations.filter(
    (r) =>
      r.status === 'confirmed' &&
      r.service_id === serviceId &&
      r.date === date &&
      r.start === start &&
      (spaceId === undefined || r.space_id === spaceId),
  );
}

// Disponibilitat d'una franja (imita el backend: fixa per franja + reserves en memoria).
function weekSlot(m: MockService, date: string, s: { start: string; end: string }): ServiceWeekSlot {
  const id = m.service.id;
  if (m.service.capacity_mode === 'people') {
    const capacity = m.personCapacity ?? 0;
    const base = mockNumber(`${id}|${date}|${s.start}`) % (capacity + 1);
    const taken = confirmedAt(id, date, s.start).reduce((n, r) => n + (r.participants_count ?? 1), 0);
    const remaining = Math.max(0, capacity - base - taken);
    return {
      ...s,
      available: remaining > 0,
      capacity_mode: 'people',
      available_units: null,
      total_units: null,
      remaining_people_capacity: remaining,
      spaces: m.resources.map((r) => ({ space_id: r.space_id, available: remaining > 0 })),
    };
  }
  const spaces = m.resources.map((r) => ({
    space_id: r.space_id,
    available:
      mockNumber(`${r.space_id}|${date}|${s.start}`) % 4 !== 0 &&
      confirmedAt(id, date, s.start, r.space_id).length === 0,
  }));
  const availableUnits = spaces.filter((x) => x.available).length;
  return {
    ...s,
    available: availableUnits > 0,
    capacity_mode: 'unit',
    available_units: availableUnits,
    total_units: spaces.length,
    remaining_people_capacity: null,
    spaces,
  };
}

// ---------------------------------------------------------
// GET /services i GET /services/{service_id}/spaces
// ---------------------------------------------------------

export async function getServices(): Promise<Service[]> {
  await delay();
  return MOCK_SERVICES.map((m) => m.service);
}

export async function getServiceSpaces(serviceId: string): Promise<ServiceSpace[]> {
  await delay();
  const m = requireService(serviceId);
  return m.resources.map((r) => ({
    service_id: serviceId,
    space_id: r.space_id,
    resource_label: r.name,
    person_capacity: m.personCapacity,
    reservation_capacity: m.service.capacity_mode === 'unit' ? 1 : null,
    capacity_mode: m.service.capacity_mode === 'unit' ? 'resource_units' : 'people',
    is_active: true,
    is_virtual: false,
    reservable: true,
  }));
}

// ---------------------------------------------------------
// GET /services/{service_id}/availability/week
// ---------------------------------------------------------

export async function getServiceAvailabilityWeek(
  serviceId: string,
  from: string,
  to: string,
): Promise<ServiceAvailabilityWeek> {
  await delay();
  const m = requireService(serviceId);
  if (from > to) {
    throw new ApiError('INVALID_DATE_RANGE', 'Rang de dates incorrecte.');
  }
  return {
    service_id: serviceId,
    from,
    to,
    capacity_mode: m.service.capacity_mode ?? 'unit',
    days: rangeDates(from, to).map((date) => ({
      date,
      slots: slotsFor(m, date).map((s) => weekSlot(m, date, s)),
    })),
  };
}

// ---------------------------------------------------------
// GET /availability/heatmap?service_id=
// Serveis sense forecast validat: score null, unknown i unavailable_reason.
// ---------------------------------------------------------

export async function getHeatmap(serviceId: string, from: string, to: string): Promise<Heatmap> {
  await delay();
  const m = requireService(serviceId);
  if (from > to) {
    throw new ApiError('INVALID_DATE_RANGE', 'Rang de dates incorrecte.');
  }
  const days = rangeDates(from, to).map((date) => ({
    date,
    slots: slotsFor(m, date).map((s): HeatmapSlot => {
      if (!m.forecastValidated) {
        return {
          hour: s.start,
          occupancy_score: null,
          occupancy_level: 'unknown',
          unavailable_reason: 'aggregated_forecast_not_validated',
        };
      }
      const n = mockNumber(`${serviceId}|${date}|${s.start}`);
      if (n % 11 === 0) return { hour: s.start, occupancy_score: null, occupancy_level: 'unknown' };
      const score = n % 100;
      const level: OccupancyLevel =
        score < 35 ? 'low' : score < 65 ? 'medium' : score < 85 ? 'high' : 'very_high';
      return { hour: s.start, occupancy_score: score, occupancy_level: level };
    }),
  }));
  return {
    service_id: serviceId,
    aggregate: true,
    source: 'historical_usage',
    occupancy_ratio_available: m.forecastValidated,
    days,
  };
}

// ---------------------------------------------------------
// POST /recommendations (per service_id)
// ---------------------------------------------------------

export async function postRecommendations(
  req: RecommendationRequest,
): Promise<Recommendation> {
  await delay();
  const m = requireService(req.service_id);

  // Pistes i serveis sense forecast validat: HTTP 200 sense recomanacio.
  if (!m.forecastValidated) {
    return {
      recommendation_id: null,
      requested_slot: { start: req.preferred_start, occupancy_score: null, occupancy_level: 'unknown' },
      recommended_slot: null,
      message: 'No ho sé amb les dades disponibles.',
      confidence: 'low',
      basis: { service_id: req.service_id, weekday: '', historical_period: null },
      recommendation_available: false,
      unavailable_reason: 'unsupported_space_type',
    };
  }

  const alternative = addMinutes(req.preferred_start, m.slotMinutes);
  return {
    recommendation_id: `rec_mock_${Date.now().toString(16)}`,
    requested_slot: { start: req.preferred_start, occupancy_score: 89, occupancy_level: 'very_high' },
    recommended_slot: { start: alternative, occupancy_score: 52, occupancy_level: 'medium' },
    message: `Les ${alternative} acostumen a tenir menys ocupació que les ${req.preferred_start}.`,
    confidence: 'medium',
    basis: {
      service_id: req.service_id,
      weekday: 'Tuesday',
      historical_period: '2026-04-01 to 2026-10-31',
    },
  };
}

export async function postRecommendationAction(
  recommendationId: string,
  action: RecommendationActionType,
): Promise<RecommendationAction> {
  await delay();
  return { recommendation_id: recommendationId, action };
}

// ---------------------------------------------------------
// POST /reservations (service_id, space_id omes -> autoassignacio)
// ---------------------------------------------------------

export async function createReservation(req: ReservationRequest): Promise<ReservationCreated> {
  await delay();
  const m = requireService(req.service_id);

  if (!/^\d{2}:\d{2}$/.test(req.start) || !/^\d{2}:\d{2}$/.test(req.end)) {
    throw new ApiError('INVALID_TIME', 'Hora no valida.');
  }

  const slot = slotsFor(m, req.date).find((s) => s.start === req.start && s.end === req.end);
  if (!slot) {
    throw new ApiError('INVALID_TIME', 'Franja no valida.');
  }

  // Conflicte: l'usuari ja te una reserva confirmada que se solapa.
  const overlaps = reservations.some(
    (r) =>
      r.status === 'confirmed' &&
      r.user_id === req.user_id &&
      r.date === req.date &&
      r.start < req.end &&
      req.start < r.end,
  );
  if (overlaps) {
    throw new ApiError('RESERVATION_CONFLICT', 'Ja hi ha una reserva en aquesta franja.');
  }

  const info = weekSlot(m, req.date, slot);
  if (!info.available) {
    throw new ApiError('SLOT_NOT_AVAILABLE', 'La franja ja no esta disponible.');
  }
  const assigned =
    req.space_id ??
    info.spaces.find((x) => x.available)?.space_id ??
    m.resources[0].space_id;

  const created: ReservationCreated = {
    reservation_id: `res_mock_${nextId++}`,
    status: 'confirmed',
    user_id: req.user_id,
    service_id: req.service_id,
    space_id: assigned,
    space_name: resourceName(assigned),
    participants_count: req.participants_count ?? null,
    date: req.date,
    start: req.start,
    end: req.end,
  };
  reservations.push(created);
  return created;
}

// ---------------------------------------------------------
// GET /reservations i DELETE /reservations/{id}
// ---------------------------------------------------------

export async function getReservations(
  userId: string,
  includeCancelled = false,
): Promise<ReservationItem[]> {
  await delay();
  return reservations
    .filter(
      (r) => r.user_id === userId && (includeCancelled || r.status === 'confirmed'),
    )
    .map((r) => ({
      reservation_id: r.reservation_id,
      space_id: r.space_id,
      space_name: r.space_name,
      date: r.date,
      start: r.start,
      end: r.end,
      status: r.status,
    }));
}

// Mateixos codis d'error que el backend (RESERVATION_NOT_FOUND, RESERVATION_ALREADY_CANCELLED).
export async function cancelReservation(reservationId: string): Promise<ReservationCancelled> {
  await delay();
  const found = reservations.find((r) => r.reservation_id === reservationId);
  if (!found) {
    throw new ApiError('RESERVATION_NOT_FOUND', 'Reserva no trobada.');
  }
  if (found.status === 'cancelled') {
    throw new ApiError('RESERVATION_ALREADY_CANCELLED', 'La reserva ja estava cancel·lada.');
  }
  found.status = 'cancelled';
  return { reservation_id: found.reservation_id, status: found.status };
}

// ---------------------------------------------------------
// POST /safi/chat: respostes fixes (una amb dades i "no ho se" per a la resta)
// ---------------------------------------------------------

export async function chatSafi(req: SafiChatRequest): Promise<SafiChatResponse> {
  await delay();
  if (req.message.toLowerCase().includes('fitness')) {
    return {
      message:
        'Segons les dades disponibles, les 19:45 tenen menys ocupació prevista que les 18:30.',
      sources: [{ type: 'historical_occupancy', service_id: 'fitness', date_reference: 'dimarts' }],
      can_answer: true,
    };
  }
  return { message: 'No ho sé amb les dades disponibles.', sources: [], can_answer: false };
}
