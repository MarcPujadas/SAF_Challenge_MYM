import type { ServiceWeekSlot } from '../services/api';

// Nomes text de presentacio: els nombres venen del backend, aqui no es calcula res.
const UNIT_LABEL: Record<string, string> = {
  padel: 'pistes',
  tennis: 'pistes',
  squash: 'pistes',
  football: 'camps',
  'pool-25m': 'carrils',
  'pool-16m': 'carrils',
};

// unit: "3 de 5 pistes disponibles" · people: "47 places disponibles"
export function capacityText(serviceId: string, slot: ServiceWeekSlot): string {
  if (slot.capacity_mode === 'people') {
    return slot.remaining_people_capacity != null
      ? `${slot.remaining_people_capacity} places disponibles`
      : 'Places disponibles: desconegudes';
  }
  if (slot.available_units == null || slot.total_units == null) {
    return 'Disponibilitat desconeguda';
  }
  const label = UNIT_LABEL[serviceId] ?? 'recursos';
  return `${slot.available_units} de ${slot.total_units} ${label} disponibles`;
}
