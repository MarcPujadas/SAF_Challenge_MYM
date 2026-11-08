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
        return 'Ja tens una reserva que coincideix amb aquesta franja.';
      case 'INVALID_DATE':
        return 'La data escollida no és vàlida.';
      case 'INVALID_DATE_RANGE':
        return 'El rang de dates no és vàlid.';
      case 'OCCUPANCY_DATA_UNAVAILABLE':
        return 'No tenim prou dades històriques d’aquesta franja per fer una previsió fiable.';
      case 'INVALID_SERVICE':
        return 'Aquest servei no existeix o no es pot reservar.';
      case 'INVALID_SERVICE_CONFIGURATION':
        return 'Aquest servei no està ben configurat. Torna-ho a provar més tard.';
      case 'INVALID_USER':
        return 'Aquest usuari no és vàlid.';
      case 'RESERVATION_NOT_FOUND':
        return 'Aquesta reserva no existeix.';
      case 'RESERVATION_ALREADY_CANCELLED':
        return 'Aquesta reserva ja estava cancel·lada.';
      case 'NETWORK_ERROR':
        return 'No hi ha connexió amb el servidor. Torna-ho a provar.';
    }
  }
  return 'Alguna cosa ha anat malament. Torna-ho a provar.';
}
