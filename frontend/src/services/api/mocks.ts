// Dades sintetiques amb la forma exacta de contracts.md. Cap dada real del SAF.
// No calculen res: nomes retornen dades fixes i guarden les reserves en memoria.
import { ApiError } from './client';
import type {
  Availability,
  Recommendation,
  RecommendationRequest,
  ReservationCreated,
  ReservationItem,
  ReservationRequest,
  Service,
  Slot,
} from './types';

const delay = () => new Promise<void>((resolve) => setTimeout(resolve, 250));

const SPACE_NAMES: Record<string, string> = {
  fitness: 'Sala Fitness',
  piscina: 'Piscina',
  padel_1: 'Pista de pàdel 1',
};

const SERVICES: Service[] = [
  {
    id: 'fitness',
    name: 'Fitness',
    description: 'Sala de fitness del SAF',
    space_id: 'fitness',
    reservable: true,
  },
  {
    id: 'piscina',
    name: 'Piscina',
    description: 'Piscina coberta',
    space_id: 'piscina',
    reservable: true,
  },
  {
    id: 'padel',
    name: 'Pàdel',
    description: 'Pista de pàdel',
    space_id: 'padel_1',
    reservable: true,
  },
];

// Franges per espai (inclou low, medium, high, very_high, unknown i una sense disponibilitat).
const SLOTS: Record<string, Slot[]> = {
  fitness: [
    { start: '09:00', end: '10:15', available: true, remaining_capacity: 90, occupancy_level: 'low', occupancy_score: 28 },
    { start: '10:15', end: '11:30', available: true, remaining_capacity: null, occupancy_level: 'unknown', occupancy_score: null },
    { start: '12:30', end: '13:45', available: true, remaining_capacity: 6, occupancy_level: 'very_high', occupancy_score: 91 },
    { start: '13:45', end: '15:00', available: false, remaining_capacity: 0, occupancy_level: 'very_high', occupancy_score: 100 },
    { start: '17:00', end: '18:15', available: true, remaining_capacity: 30, occupancy_level: 'high', occupancy_score: 82 },
    { start: '19:00', end: '20:15', available: true, remaining_capacity: 64, occupancy_level: 'medium', occupancy_score: 51 },
  ],
  piscina: [
    { start: '08:00', end: '09:00', available: true, remaining_capacity: 20, occupancy_level: 'low', occupancy_score: 22 },
    { start: '13:00', end: '14:00', available: true, remaining_capacity: 9, occupancy_level: 'high', occupancy_score: 78 },
    { start: '19:00', end: '20:00', available: true, remaining_capacity: null, occupancy_level: 'unknown', occupancy_score: null },
  ],
  padel_1: [
    { start: '17:00', end: '18:30', available: true, remaining_capacity: 1, occupancy_level: 'medium', occupancy_score: 55 },
    { start: '18:30', end: '20:00', available: false, remaining_capacity: 0, occupancy_level: 'very_high', occupancy_score: 100 },
  ],
};

// Reserves en memoria. La primera serveix per provar RESERVATION_CONFLICT:
// reservar fitness, 2026-11-09, 17:00-18:15 retorna aquest error.
const reservations: ReservationCreated[] = [
  {
    reservation_id: 'res_mock_0',
    status: 'confirmed',
    user_id: 'demo-user',
    space_id: 'fitness',
    date: '2026-11-09',
    start: '17:00',
    end: '18:15',
  },
];
let nextId = 1;

function requireSpace(spaceId: string): void {
  if (!(spaceId in SPACE_NAMES)) {
    throw new ApiError('INVALID_SPACE', `Espai desconegut: ${spaceId}`);
  }
}

export async function getServices(): Promise<Service[]> {
  await delay();
  return SERVICES;
}

export async function getAvailability(spaceId: string, date: string): Promise<Availability> {
  await delay();
  requireSpace(spaceId);
  return { space_id: spaceId, date, slots: SLOTS[spaceId] ?? [] };
}

// Resposta fixa del contracte: 18:00 very_high -> 19:00 medium.
export async function postRecommendations(req: RecommendationRequest): Promise<Recommendation> {
  await delay();
  requireSpace(req.space_id);
  return {
    requested_slot: { start: '18:00', occupancy_score: 89, occupancy_level: 'very_high' },
    recommended_slot: { start: '19:00', occupancy_score: 52, occupancy_level: 'medium' },
    message: 'Les 19:00 acostumen a tenir menys ocupació que les 18:00.',
    confidence: 'medium',
    basis: {
      space: SPACE_NAMES[req.space_id],
      weekday: 'Tuesday',
      historical_period: 'comparable recent months',
    },
  };
}

export async function createReservation(req: ReservationRequest): Promise<ReservationCreated> {
  await delay();
  requireSpace(req.space_id);
  if (!/^\d{2}:\d{2}$/.test(req.start) || !/^\d{2}:\d{2}$/.test(req.end)) {
    throw new ApiError('INVALID_TIME', 'Hora no valida.');
  }
  const taken = reservations.some(
    (r) =>
      r.space_id === req.space_id &&
      r.date === req.date &&
      r.start === req.start &&
      r.status === 'confirmed',
  );
  if (taken) {
    throw new ApiError('RESERVATION_CONFLICT', 'Ja hi ha una reserva en aquesta franja.');
  }
  const created: ReservationCreated = {
    reservation_id: `res_mock_${nextId++}`,
    status: 'confirmed',
    user_id: req.user_id,
    space_id: req.space_id,
    date: req.date,
    start: req.start,
    end: req.end,
  };
  reservations.push(created);
  return created;
}

export async function getReservations(userId: string): Promise<ReservationItem[]> {
  await delay();
  return reservations
    .filter((r) => r.user_id === userId)
    .map((r) => ({
      reservation_id: r.reservation_id,
      space_id: r.space_id,
      space_name: SPACE_NAMES[r.space_id] ?? r.space_id,
      date: r.date,
      start: r.start,
      end: r.end,
      status: r.status,
    }));
}
