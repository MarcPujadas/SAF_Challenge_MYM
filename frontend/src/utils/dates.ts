// Helpers de dates LOCALS (YYYY-MM-DD). Mai toISOString (dona UTC). Sense logica de negoci.

const pad = (n: number) => String(n).padStart(2, '0');

export function formatDate(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function parseDate(s: string): Date {
  const [y, m, d] = s.split('-').map(Number);
  return new Date(y, m - 1, d);
}

export function todayDate(): string {
  return formatDate(new Date());
}

export function addDays(date: string, n: number): string {
  const d = parseDate(date);
  d.setDate(d.getDate() + n);
  return formatDate(d);
}

// Dilluns de la setmana que conte `date`.
export function mondayOf(date: string): string {
  const d = parseDate(date);
  return addDays(date, -((d.getDay() + 6) % 7));
}

// `count` dates consecutives des de `from`.
export function daysFrom(from: string, count = 7): string[] {
  return Array.from({ length: count }, (_, i) => addDays(from, i));
}

const WEEKDAY_SHORT = ['Dg', 'Dl', 'Dt', 'Dc', 'Dj', 'Dv', 'Ds'];
const WEEKDAY_LONG = ['diumenge', 'dilluns', 'dimarts', 'dimecres', 'dijous', 'divendres', 'dissabte'];
const MONTH_SHORT = ['gen', 'feb', 'març', 'abr', 'maig', 'juny', 'jul', 'ag', 'set', 'oct', 'nov', 'des'];

export const weekdayShort = (date: string) => WEEKDAY_SHORT[parseDate(date).getDay()];
export const weekdayLong = (date: string) => WEEKDAY_LONG[parseDate(date).getDay()];

// "9 - 15 nov" o "27 oct - 2 nov"
export function formatRange(from: string, to: string): string {
  const a = parseDate(from);
  const b = parseDate(to);
  if (a.getMonth() === b.getMonth()) {
    return `${a.getDate()} - ${b.getDate()} ${MONTH_SHORT[b.getMonth()]}`;
  }
  return `${a.getDate()} ${MONTH_SHORT[a.getMonth()]} - ${b.getDate()} ${MONTH_SHORT[b.getMonth()]}`;
}
