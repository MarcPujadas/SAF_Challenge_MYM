import { request } from './client';
import { USE_MOCKS } from './config';
import * as mocks from './mocks';
import type {
  Availability,
  Recommendation,
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

export function postRecommendations(req: RecommendationRequest): Promise<Recommendation> {
  return USE_MOCKS
    ? mocks.postRecommendations(req)
    : request<Recommendation>('POST', '/recommendations', { body: req });
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

export function chatSafi(
  message: string,
  userId: string = DEFAULT_USER_ID,
): Promise<SafiChatResponse> {
  const body: SafiChatRequest = { user_id: userId, message };
  return USE_MOCKS
    ? mocks.chatSafi(body)
    : request<SafiChatResponse>('POST', '/safi/chat', { body });
}

export { ApiError } from './client';
export { errorMessage } from './errors';
export type * from './types';
