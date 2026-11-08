const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
type Envelope<T> = { success: boolean; data: T | null; error: { code: string; message: string } | null };
export type Service = { id: string; name: string; description?: string; space_id?: string; reservable: boolean };
export type Slot = { start: string; end: string; available: boolean; available_units: number | null; remaining_people_capacity: number | null };
export type ServiceDay = { date: string; slots: Slot[] };
export type ServiceWeek = { service_id: string; days: ServiceDay[] };
export type Recommendation = { recommendation_id: string | null; message: string; recommended_slot: { start: string; occupancy_score: number | null } | null; recommendation_available?: boolean };
export type Reservation = { reservation_id: string; service_id: string | null; space_id: string; date: string; start: string; end: string; status: string };
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(API_BASE_URL + '/api/v1' + path, { ...init, signal: controller.signal, headers: { 'Content-Type': 'application/json', ...init?.headers } });
    const body = await response.json() as Envelope<T>;
    if (!response.ok || !body.success || body.data === null) throw new Error(body.error?.message || 'Error de comunicació amb SAFi');
    return body.data;
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') throw new Error('El backend no respon (12 s). Comprova iniciar_web.bat.');
    throw err;
  } finally { clearTimeout(timeout); }
}
export const getServices = () => api<Service[]>('/services');
export const fetchServices = getServices;
export const getServiceAvailabilityWeek = (id: string, date: string) => api<ServiceWeek>('/services/' + encodeURIComponent(id) + '/availability/week?from=' + date + '&to=' + date);
export const getRecommendation = (body: {service_id: string; date: string; preferred_start: string; preferred_end: string}) => api<Recommendation>('/recommendations', {method:'POST',body:JSON.stringify(body)});
export const sendRecommendationAction = (id:string, action:'accepted'|'ignored') => api<unknown>('/recommendations/'+encodeURIComponent(id)+'/action',{method:'POST',body:JSON.stringify({action})});
export const createReservation = (body:{user_id:string;service_id:string;date:string;start:string;end:string}) => api<Reservation>('/reservations',{method:'POST',body:JSON.stringify(body)});
export const fetchAdminSummary = () => api<any>('/admin/summary');
export const fetchAdminStats = () => api<any>('/admin/stats');
export const fetchAdminReservations = () => api<any>('/admin/reservations');
export const fetchAdminRecommendationsStats = (spaceId?:string) => api<any>('/admin/recommendations/stats' + (spaceId?'?space_id='+encodeURIComponent(spaceId):''));
