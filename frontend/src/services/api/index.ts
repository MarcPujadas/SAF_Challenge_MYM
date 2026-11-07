import { request } from './client';
import { USE_MOCKS } from './config';
import * as mocks from './mocks';
import type {
  Availability,
  AvailabilityWeek,
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
} from './types';

// contracts.md: usuari de demo (no el "1" de tasks.md).
export const DEFAULT_USER_ID = 'demo-user';

export function getServices(): Promise<Service[]> {
  return USE_MOCKS ? mocks.getServices() : request<Service[]>('GET', '/services');
}

export function getAvailability(spaceId: string, date: string): Promise<Availability> {
  return USE_MOCKS
    ? mocks.getAvailability(spaceId, date)
    : request<Availability>('GET', '/availability', { query: { space_id: spaceId, date } });
}

// PROVISIONAL, pendent de contracts.md: GET /availability/week (tasques_v3.md 4.3).
export function getAvailabilityWeek(
  spaceId: string,
  from: string,
  to: string,
): Promise<AvailabilityWeek> {
  return USE_MOCKS
    ? mocks.getAvailabilityWeek(spaceId, from, to)
    : request<AvailabilityWeek>('GET', '/availability/week', {
        query: { space_id: spaceId, from, to },
      });
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

export function getHeatmap(spaceId: string, from: string, to: string): Promise<Heatmap> {
  return USE_MOCKS
    ? mocks.getHeatmap(spaceId, from, to)
    : request<Heatmap>('GET', '/availability/heatmap', {
        query: { space_id: spaceId, from, to },
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

export function getReservations(userId: string = DEFAULT_USER_ID): Promise<ReservationItem[]> {
  return USE_MOCKS
    ? mocks.getReservations(userId)
    : request<ReservationItem[]>('GET', '/reservations', { query: { user_id: userId } });
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
