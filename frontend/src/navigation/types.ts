import type { ReservationCreated } from '../services/api';

export type RootStackParamList = {
  Home: undefined;
  Reserva: undefined;
  Confirmacion: { reservation: ReservationCreated; spaceName: string };
};
