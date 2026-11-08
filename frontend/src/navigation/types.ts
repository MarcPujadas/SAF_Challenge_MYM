import type { ReservationCreated } from '../services/api';

export type RootStackParamList = {
  Home: undefined;
  // spaceId nomes informatiu (recurs ja assignat); mai es una seleccio obligatoria.
  Reserva: { serviceId?: string; date?: string; start?: string; spaceId?: string } | undefined;
  Confirmacion: { reservation: ReservationCreated; serviceName: string };
  MevesReserves: undefined;
  SafiChat: undefined;
  Serveis: undefined;
  Heatmap: { serviceId?: string } | undefined;
};
