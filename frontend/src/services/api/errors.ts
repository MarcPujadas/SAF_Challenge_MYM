import { ApiError } from './client';

// Missatge curt per a l'usuari a partir d'un error de l'API.
export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    switch (err.code) {
      case 'SLOT_NOT_AVAILABLE':
        return 'Aquesta franja ja no està disponible. Tria\'n una altra.';
      case 'INVALID_SPACE':
        return 'Aquest espai no existeix.';
      case 'INVALID_TIME':
        return 'L\'hora escollida no és vàlida.';
      case 'RESERVATION_CONFLICT':
        return 'Ja hi ha una reserva en aquesta franja.';
      case 'NETWORK_ERROR':
        return 'No hi ha connexió amb el servidor. Torna-ho a provar.';
    }
  }
  return 'Alguna cosa ha anat malament. Torna-ho a provar.';
}
