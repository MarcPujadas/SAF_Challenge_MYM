// Tipos copiats de contracts.md. No afegir camps que no hi surtin.
// Dates: YYYY-MM-DD. Hores: HH:MM (24 h). Els identificadors son strings.

export type ApiErrorCode =
  | 'SLOT_NOT_AVAILABLE'
  | 'INVALID_SPACE'
  | 'INVALID_TIME'
  | 'RESERVATION_CONFLICT'
  | (string & {});

export type ApiEnvelope<T> = {
  success: boolean;
  data: T | null;
  error: { code: ApiErrorCode; message: string } | null;
};

export type OccupancyLevel = 'low' | 'medium' | 'high' | 'very_high' | 'unknown';
export type Confidence = 'low' | 'medium' | 'high';
export type ReservationStatus = 'confirmed' | 'cancelled';

// GET /services
export type Service = {
  id: string;
  name: string;
  description: string;
  space_id: string;
  reservable: boolean;
};

// GET /availability?space_id=&date=
// Regla 7 del contracte: si una dada no existeix, null o 'unknown'.
export type Slot = {
  start: string;
  end: string;
  available: boolean;
  remaining_capacity: number | null;
  occupancy_level: OccupancyLevel;
  occupancy_score: number | null; // 0..100
};

export type Availability = {
  space_id: string;
  date: string;
  slots: Slot[];
};

// POST /recommendations
export type RecommendationRequest = {
  space_id: string;
  date: string;
  preferred_start: string;
  preferred_end: string;
};

export type RecommendationSlot = {
  start: string;
  occupancy_score: number | null; // 0..100
  occupancy_level: OccupancyLevel;
};

export type Recommendation = {
  requested_slot: RecommendationSlot;
  recommended_slot: RecommendationSlot | null; // null si no hi ha alternativa (regla 7)
  message: string;
  confidence: Confidence;
  basis: {
    space_id: string;
    weekday: string;
    historical_period: string;
  };
};

// POST /reservations
export type ReservationRequest = {
  user_id: string;
  space_id: string;
  date: string;
  start: string;
  end: string;
};

export type ReservationCreated = {
  reservation_id: string;
  status: ReservationStatus;
  user_id: string;
  space_id: string;
  date: string;
  start: string;
  end: string;
};

// GET /reservations?user_id=
export type ReservationItem = {
  reservation_id: string;
  space_id: string;
  space_name: string;
  date: string;
  start: string;
  end: string;
  status: ReservationStatus;
};

// DELETE /reservations/{reservation_id}
export type ReservationCancelled = {
  reservation_id: string;
  status: ReservationStatus;
};

// POST /safi/chat
export type SafiChatRequest = {
  user_id: string;
  message: string;
};

export type SafiSource = {
  type: string;
  space_id: string;
  date_reference: string;
};

export type SafiChatResponse = {
  message: string;
  sources: SafiSource[];
  can_answer: boolean;
};
