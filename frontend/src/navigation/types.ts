import type { ReservationCreated } from '../services/api';

export type RootStackParamList = {
  Home: undefined;
  Reserva: { serviceId?: string; date?: string; start?: string } | undefined;
  Confirmacion: { reservation: ReservationCreated; spaceName: string };
  MevesReserves: undefined;
  SafiChat: undefined;
  Serveis: undefined;
  Heatmap: { serviceId?: string } | undefined;
};
