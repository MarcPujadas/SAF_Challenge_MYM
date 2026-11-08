// Tipos copiats de contracts.md. No afegir camps que no hi surtin.
// Dates: YYYY-MM-DD. Hores: HH:MM (24 h). Els identificadors son strings.

export type ApiErrorCode =
  | 'SLOT_NOT_AVAILABLE'
  | 'INVALID_SPACE'
  | 'INVALID_TIME'
  | 'RESERVATION_CONFLICT'
  | 'INVALID_DATE'
  | 'INVALID_DATE_RANGE'
  | 'OCCUPANCY_DATA_UNAVAILABLE'
  | 'INVALID_SERVICE'
  | 'INVALID_SERVICE_CONFIGURATION'
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
// Model multiespai: l'entitat principal es service.id. space_id es nomes un subespai
// representatiu per compatibilitat: NO s'ha d'utilitzar per agregar ni reservar un servei.
export type CapacityMode = 'unit' | 'people';

export type Service = {
  id: string;
  name: string;
  description: string;
  space_id?: string; // compat. no usar
  reservable: boolean;
  resource_count?: number;
  capacity_mode?: CapacityMode;
};

// GET /services/{service_id}/spaces
export type ServiceSpace = {
  service_id: string;
  space_id: string;
  resource_label: string;
  person_capacity: number | null;
  reservation_capacity: number | null;
  capacity_mode: string; // p. ex. 'resource_units'
  is_active: boolean;
  is_virtual: boolean;
  reservable: boolean;
};

// GET /services/{service_id}/availability/week?from=&to=   (contracts.md, seccio 5)
// Disponibilitat actual agregada del servei (SQLite + reserves confirmades). Sense previsio.
// unit:   available_units / total_units (remaining_people_capacity = null)
// people: remaining_people_capacity (available_units / total_units = null)
export type ServiceSlotSpace = {
  space_id: string;
  available: boolean;
};

export type ServiceWeekSlot = {
  start: string;
  end: string;
  available: boolean;
  capacity_mode: CapacityMode;
  available_units: number | null;
  total_units: number | null;
  remaining_people_capacity: number | null;
  spaces: ServiceSlotSpace[]; // informatiu: el backend assigna el recurs en reservar
};

export type ServiceWeekDay = {
  date: string;
  slots: ServiceWeekSlot[];
};

export type ServiceAvailabilityWeek = {
  service_id: string;
  from: string;
  to: string;
  capacity_mode: CapacityMode;
  days: ServiceWeekDay[];
};

// POST /recommendations
export type RecommendationRequest = {
  service_id: string;
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
  recommendation_id: string | null;
  requested_slot: RecommendationSlot;
  recommended_slot: RecommendationSlot | null; // null si no hi ha alternativa (regla 7)
  message: string;
  confidence: Confidence;
  basis: {
    service_id?: string;
    space_id?: string;
    weekday: string;
    historical_period: string | null;
  };
  recommendation_available?: boolean;
  unavailable_reason?: string | null;
};

// POST /recommendations/{recommendation_id}/action
export type RecommendationActionType = 'accepted' | 'ignored';

export type RecommendationAction = {
  recommendation_id: string;
  action: RecommendationActionType;
};

// GET /availability/heatmap?service_id=&from=&to=  (previsio historica; days pot ser [])
// Els serveis sense forecast agregat validat retornen occupancy_score null,
// occupancy_level 'unknown' i unavailable_reason 'aggregated_forecast_not_validated'.
export type HeatmapSlot = {
  hour: string;
  occupancy_score: number | null; // 0..100
  occupancy_level: OccupancyLevel;
  occupancy_ratio?: number | null;
  samples?: number;
  unavailable_reason?: string | null;
};

export type HeatmapDay = {
  date: string;
  slots: HeatmapSlot[];
};

export type Heatmap = {
  service_id?: string;
  space_id?: string;
  aggregate?: boolean;
  source?: string;
  occupancy_ratio_available?: boolean;
  days: HeatmapDay[];
};

// POST /reservations
// Reserva per servei: space_id s'ometeix (o null) i el backend autoassigna el subespai.
export type ReservationRequest = {
  user_id: string;
  service_id: string;
  space_id?: string | null;
  participants_count?: number | null;
  date: string;
  start: string;
  end: string;
};

export type ReservationCreated = {
  reservation_id: string;
  status: ReservationStatus;
  user_id: string;
  service_id: string | null;
  space_id: string; // subespai assignat pel backend
  space_name: string;
  participants_count: number | null;
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
  service_id?: string;
  space_id?: string;
  space_ids?: string[];
  date_reference?: string;
};

export type SafiChatResponse = {
  message: string;
  sources: SafiSource[];
  can_answer: boolean;
  provider?: string;
};
