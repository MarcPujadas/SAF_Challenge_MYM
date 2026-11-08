import { request } from './client';
import { USE_MOCKS } from './config';
import * as mocks from './mocks';
import type {
  Heatmap,
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
} from './types';

// contracts.md: usuari de demo (no el "1" de tasks.md).
export const DEFAULT_USER_ID = 'demo-user';

export function getServices(): Promise<Service[]> {
  return USE_MOCKS ? mocks.getServices() : request<Service[]>('GET', '/services');
}

// Subespais (recursos) d'un servei. Informatiu: l'usuari tria servei, no recurs.
export function getServiceSpaces(serviceId: string): Promise<ServiceSpace[]> {
  return USE_MOCKS
    ? mocks.getServiceSpaces(serviceId)
    : request<ServiceSpace[]>('GET', `/services/${encodeURIComponent(serviceId)}/spaces`);
}

// Disponibilitat actual agregada per servei (flux de Heatmap i Reserva).
export function getServiceAvailabilityWeek(
  serviceId: string,
  from: string,
  to: string,
): Promise<ServiceAvailabilityWeek> {
  return USE_MOCKS
    ? mocks.getServiceAvailabilityWeek(serviceId, from, to)
    : request<ServiceAvailabilityWeek>(
        'GET',
        `/services/${encodeURIComponent(serviceId)}/availability/week`,
        { query: { from, to } },
      );
}

export function postRecommendations(req: RecommendationRequest): Promise<Recommendation> {
  return USE_MOCKS
    ? mocks.postRecommendations(req)
    : request<Recommendation>('POST', '/recommendations', { body: req });
}

export function postRecommendationAction(
  recommendationId: string,
  action: RecommendationActionType,
): Promise<RecommendationAction> {
  return USE_MOCKS
    ? mocks.postRecommendationAction(recommendationId, action)
    : request<RecommendationAction>(
        'POST',
        `/recommendations/${encodeURIComponent(recommendationId)}/action`,
        { body: { action } },
      );
}

// Previsio historica per servei (GET /availability/heatmap?service_id=...).
export function getHeatmap(serviceId: string, from: string, to: string): Promise<Heatmap> {
  return USE_MOCKS
    ? mocks.getHeatmap(serviceId, from, to)
    : request<Heatmap>('GET', '/availability/heatmap', {
        query: { service_id: serviceId, from, to },
      });
}

export function createReservation(
  req: Omit<ReservationRequest, 'user_id'> & { user_id?: string },
): Promise<ReservationCreated> {
  const body: ReservationRequest = { ...req, user_id: req.user_id ?? DEFAULT_USER_ID };
  return USE_MOCKS
    ? mocks.createReservation(body)
    : request<ReservationCreated>('POST', '/reservations', { body });
}

export function getReservations(
  userId: string = DEFAULT_USER_ID,
  includeCancelled = false,
): Promise<ReservationItem[]> {
  return USE_MOCKS
    ? mocks.getReservations(userId, includeCancelled)
    : request<ReservationItem[]>('GET', '/reservations', {
        query: {
          user_id: userId,
          include_cancelled: includeCancelled ? 'true' : 'false',
        },
      });
}

export function cancelReservation(reservationId: string): Promise<ReservationCancelled> {
  return USE_MOCKS
    ? mocks.cancelReservation(reservationId)
    : request<ReservationCancelled>('DELETE', `/reservations/${encodeURIComponent(reservationId)}`);
}

export async function chatSafi(
  message: string,
  userId: string = DEFAULT_USER_ID,
): Promise<SafiChatResponse> {
  const body: SafiChatRequest = { user_id: userId, message };
  if (USE_MOCKS) return mocks.chatSafi(body);

  try {
    return await request<SafiChatResponse>('POST', '/safi/chat-llm', { body });
  } catch {
    // Demo-safe fallback: if Ornith is unavailable or returns an invalid response,
    // keep SAFi usable through the deterministic backend.
    return request<SafiChatResponse>('POST', '/safi/chat', { body });
  }
}

export { ApiError } from './client';
export { errorMessage } from './errors';
export type * from './types';
