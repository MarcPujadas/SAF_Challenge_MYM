// src/services/api.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Service {
  id: string;
  name: string;
  space_id: string;
  description?: string;
}

export interface Reservation {
  id?: string;
  space_id: string;
  user_id: string;
  date: string;
  start_time: string;
  end_time: string;
  status?: string;
}

export interface RecommendationRequest {
  user_id: string;
  basis: {
    space_id: string;
    weekday: string;
    historical_period?: string;
  };
  requested_start: string;
}

export interface RecommendationResponse {
  recommendation_id: string;
  recommended_start: string;
  reason: string;
  occupancy_score: number;
  occupancy_level: string;
}

// Funció auxiliar robusta per gestionar respostes del backend
async function handleResponse(res: Response) {
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.error || 'Error en la petició a l’API');
  }
  return await res.json();
}

// 1. Serveis
export async function getServices(): Promise<Service[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/services`);
  return handleResponse(res);
}

// 2. Disponibilitat
export async function getAvailability(spaceId: string, date: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/availability?space_id=${spaceId}&date=${date}`);
  return handleResponse(res);
}

// 3. Recomanacions SAFi
export async function getRecommendation(data: RecommendationRequest): Promise<RecommendationResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/recommendations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

// 4. Registrar acció de recomanació
export async function sendRecommendationAction(recommendationId: string, action: 'accepted' | 'ignored') {
  const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/${recommendationId}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  });
  return handleResponse(res);
}

// 5. Crear Reserva
export async function createReservation(reservation: Reservation) {
  const res = await fetch(`${API_BASE_URL}/api/v1/reservations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reservation),
  });
  return handleResponse(res);
}

// 6. Heatmap d'ocupació
export async function getHeatmap(spaceId: string, from: string, to: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/availability/heatmap?space_id=${spaceId}&from=${from}&to=${to}`);
  return handleResponse(res);
}

// --- ADMIN APIs ---

export async function getAdminSummary() {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/summary`);
  return handleResponse(res);
}

export async function getAdminStats() {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/stats`);
  return handleResponse(res);
}

export async function getAdminReservations() {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/reservations`);
  return handleResponse(res);
}

export async function getAdminOccupancy(spaceId?: string, from?: string, to?: string) {
  let url = `${API_BASE_URL}/api/v1/admin/occupancy`;
  const params = new URLSearchParams();
  if (spaceId) params.append('space_id', spaceId);
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  if (params.toString()) url += `?${params.toString()}`;

  const res = await fetch(url);
  return handleResponse(res);
}

export async function fetchAdminRecommendationsStats(spaceId?: string, from?: string, to?: string) {
  let url = `${API_BASE_URL}/api/v1/admin/recommendations/stats`;
  const params = new URLSearchParams();
  if (spaceId) params.append('space_id', spaceId);
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  if (params.toString()) url += `?${params.toString()}`;

  const res = await fetch(url);
  return handleResponse(res);
}

// --- ÀLIES DE COMPATIBILITAT ---
export const fetchAdminReservations = getAdminReservations;
export const fetchAdminSummary = getAdminSummary;
export const fetchAdminStats = getAdminStats;
export const fetchServices = getServices;