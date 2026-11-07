const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function fetchAdminSummary() {
  const res = await fetch(`${API_URL}/admin/summary`);
  return res.json();
}

export async function fetchAdminReservations() {
  const res = await fetch(`${API_URL}/admin/reservations`);
  return res.json();
}