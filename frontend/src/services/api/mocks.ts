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

const delay = () =>
  new Promise<void>((resolve) =>
    setTimeout(resolve, 250),
  );


// ---------------------------------------------------------
// IDs reals dels espais del backend
// ---------------------------------------------------------

const FITNESS_SPACE_ID = 'sala-fitnes-sala-cardio';
const POOL_25M_SPACE_ID = 'piscina-25-metres-carrer-1';
const PADEL_SPACE_ID = 'pistes-de-padel-pista-1';


// ---------------------------------------------------------
// Noms dels espais
// ---------------------------------------------------------

const SPACE_NAMES: Record<string, string> = {
  [FITNESS_SPACE_ID]: 'Sala Fitness',
  [POOL_25M_SPACE_ID]: 'Piscina 25 m',
  [PADEL_SPACE_ID]: 'Pista de pàdel 1',
};


// ---------------------------------------------------------
// Serveis
//
// IMPORTANT:
// id = identificador del servei
// space_id = identificador real de l'espai al backend
// ---------------------------------------------------------

const SERVICES: Service[] = [
  {
    id: 'fitness',
    name: 'Fitness',
    description: 'Sala de fitness i cardio',
    space_id: FITNESS_SPACE_ID,
    reservable: true,
  },
  {
    id: 'pool-25m',
    name: 'Piscina 25 m',
    description: 'Piscina de 25 metres',
    space_id: POOL_25M_SPACE_ID,
    reservable: true,
  },
  {
    id: 'padel',
    name: 'Pàdel',
    description: 'Pistes de pàdel',
    space_id: PADEL_SPACE_ID,
    reservable: true,
  },
];


// ---------------------------------------------------------
// Disponibilitat simulada
//
// Les claus són SEMPRE space_id reals.
// ---------------------------------------------------------

const SLOTS: Record<string, Slot[]> = {
  [FITNESS_SPACE_ID]: [
    {
      start: '09:00',
      end: '10:15',
      available: true,
      remaining_capacity: 90,
      occupancy_level: 'low',
      occupancy_score: 28,
    },
    {
      start: '10:15',
      end: '11:30',
      available: true,
      remaining_capacity: null,
      occupancy_level: 'unknown',
      occupancy_score: null,
    },
    {
      start: '12:30',
      end: '13:45',
      available: true,
      remaining_capacity: 6,
      occupancy_level: 'very_high',
      occupancy_score: 91,
    },
    {
      start: '13:45',
      end: '15:00',
      available: false,
      remaining_capacity: 0,
      occupancy_level: 'very_high',
      occupancy_score: 100,
    },
    {
      start: '17:00',
      end: '18:15',
      available: true,
      remaining_capacity: 30,
      occupancy_level: 'high',
      occupancy_score: 82,
    },
    {
      start: '19:00',
      end: '20:15',
      available: true,
      remaining_capacity: 64,
      occupancy_level: 'medium',
      occupancy_score: 51,
    },
  ],

  [POOL_25M_SPACE_ID]: [
    {
      start: '08:00',
      end: '09:00',
      available: true,
      remaining_capacity: 20,
      occupancy_level: 'low',
      occupancy_score: 22,
    },
    {
      start: '13:00',
      end: '14:00',
      available: true,
      remaining_capacity: 9,
      occupancy_level: 'high',
      occupancy_score: 78,
    },
    {
      start: '19:00',
      end: '20:00',
      available: true,
      remaining_capacity: null,
      occupancy_level: 'unknown',
      occupancy_score: null,
    },
  ],

  [PADEL_SPACE_ID]: [
    {
      start: '17:00',
      end: '18:15',
      available: true,
      remaining_capacity: 1,
      occupancy_level: 'medium',
      occupancy_score: 55,
    },
    {
      start: '18:30',
      end: '19:45',
      available: false,
      remaining_capacity: 0,
      occupancy_level: 'very_high',
      occupancy_score: 100,
    },
  ],
};


// ---------------------------------------------------------
// Reserves mock
//
// Aquesta reserva serveix per provar un conflicte.
// ---------------------------------------------------------

const reservations: ReservationCreated[] = [
  {
    reservation_id: 'res_mock_0',
    status: 'confirmed',
    user_id: 'demo-user',
    space_id: FITNESS_SPACE_ID,
    date: '2026-11-09',
    start: '17:00',
    end: '18:15',
  },
];

let nextId = 1;


// ---------------------------------------------------------
// Helpers
// ---------------------------------------------------------

function requireSpace(spaceId: string): void {
  if (!(spaceId in SPACE_NAMES)) {
    throw new ApiError(
      'INVALID_SPACE',
      `Espai desconegut: ${spaceId}`,
    );
  }
}


// ---------------------------------------------------------
// GET /services
// ---------------------------------------------------------

export async function getServices(): Promise<Service[]> {
  await delay();

  return SERVICES;
}


// ---------------------------------------------------------
// GET /availability
// ---------------------------------------------------------

export async function getAvailability(
  spaceId: string,
  date: string,
): Promise<Availability> {
  await delay();

  requireSpace(spaceId);

  return {
    space_id: spaceId,
    date,
    slots: SLOTS[spaceId] ?? [],
  };
}


// ---------------------------------------------------------
// POST /recommendations
// ---------------------------------------------------------

export async function postRecommendations(
  req: RecommendationRequest,
): Promise<Recommendation> {
  await delay();

  requireSpace(req.space_id);

  return {
    requested_slot: {
      start: '18:00',
      occupancy_score: 89,
      occupancy_level: 'very_high',
    },

    recommended_slot: {
      start: '19:00',
      occupancy_score: 52,
      occupancy_level: 'medium',
    },

    message:
      'Les 19:00 acostumen a tenir menys ocupació que les 18:00.',

    confidence: 'medium',

    basis: {
      space_id: req.space_id,
      weekday: 'Tuesday',
      historical_period: '2026-04-01 to 2026-10-31',
    },
  };
}


// ---------------------------------------------------------
// POST /reservations
// ---------------------------------------------------------

export async function createReservation(
  req: ReservationRequest,
): Promise<ReservationCreated> {
  await delay();

  requireSpace(req.space_id);

  if (
    !/^\d{2}:\d{2}$/.test(req.start) ||
    !/^\d{2}:\d{2}$/.test(req.end)
  ) {
    throw new ApiError(
      'INVALID_TIME',
      'Hora no valida.',
    );
  }

  const taken = reservations.some(
    (reservation) =>
      reservation.space_id === req.space_id &&
      reservation.date === req.date &&
      reservation.start === req.start &&
      reservation.status === 'confirmed',
  );

  if (taken) {
    throw new ApiError(
      'RESERVATION_CONFLICT',
      'Ja hi ha una reserva en aquesta franja.',
    );
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


// ---------------------------------------------------------
// GET /reservations
// ---------------------------------------------------------

export async function getReservations(
  userId: string,
): Promise<ReservationItem[]> {
  await delay();

  return reservations
    .filter(
      (reservation) =>
        reservation.user_id === userId,
    )
    .map((reservation) => ({
      reservation_id:
        reservation.reservation_id,

      space_id:
        reservation.space_id,

      space_name:
        SPACE_NAMES[reservation.space_id] ??
        reservation.space_id,

      date:
        reservation.date,

      start:
        reservation.start,

      end:
        reservation.end,

      status:
        reservation.status,
    }));
}