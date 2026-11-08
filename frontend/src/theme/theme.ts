import { Platform } from 'react-native';
import type { TextStyle, ViewStyle } from 'react-native';

// Sistema de disseny de l'app (verd SAF UAB). Nomes tokens visuals: cap logica de negoci.
// Contrast de text revisat per a WCAG AA (>= 4.5:1) sobre els fons indicats.

export const colors = {
  primary: '#1B7F3B', // text blanc sobre primary: 5.0:1
  primaryDark: '#145C2B',
  primaryLight: '#2E9B50',
  primarySoft: '#E6F4EA', // fons suau per a seleccionats; text primaryDark: 7.5:1
  white: '#FFFFFF',
  background: '#F4F7F5',
  surface: '#FFFFFF',
  surfaceMuted: '#EEF2EF',
  border: '#DCE3DE',
  text: '#17211B', // sobre blanc: 16:1
  textMuted: '#55625A', // sobre blanc: 6.3:1
  textOnPrimary: '#FFFFFF',

  danger: '#B3261E', // sobre blanc: 6.5:1
  dangerSoft: '#FCE9E7',
  warning: '#8A5A00', // sobre warningSoft: 5.6:1
  warningSoft: '#FFF3D6',
  info: '#0F5CA8',
  infoSoft: '#E4F0FB',
  neutralSoft: '#E6EAE7',

  // SAFi: accent propi per diferenciar les recomanacions de la resta.
  safi: '#5B2A86', // sobre safiSoft: 8.5:1
  safiSoft: '#F1E8FA',
} as const;

// Colors de les cel·les del heatmap (sempre amb text; mai nomes color). Text fosc a sobre: >= 7:1.
export const heatTones = {
  good: '#B7E2BF', // verd: disponible / previsio baixa
  warn: '#FFF0A6', // groc: previsio mitjana
  high: '#FFD4A3', // taronja: previsio alta
  bad: '#F4B6B0', // vermell suau: plena / previsio molt alta
  unknown: '#E3E7E4', // gris: desconegut
} as const;

export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 } as const;

export const radius = { sm: 8, md: 12, lg: 16, xl: 24, pill: 999 } as const;

// Fonts del sistema, mides fixes.
export const typography = {
  title: { fontSize: 26, fontWeight: '800', color: colors.text } as TextStyle,
  heading: { fontSize: 18, fontWeight: '700', color: colors.text } as TextStyle,
  body: { fontSize: 16, fontWeight: '400', color: colors.text } as TextStyle,
  caption: { fontSize: 13, fontWeight: '400', color: colors.textMuted } as TextStyle,
  button: { fontSize: 16, fontWeight: '700' } as TextStyle,
};

// Ombres subtils: shadow a iOS, elevation a Android.
export const shadow: { card: ViewStyle; floating: ViewStyle } = {
  card: Platform.select<ViewStyle>({
    ios: {
      shadowColor: '#0B2A16',
      shadowOpacity: 0.08,
      shadowRadius: 8,
      shadowOffset: { width: 0, height: 2 },
    },
    default: { elevation: 2 },
  }) as ViewStyle,
  floating: Platform.select<ViewStyle>({
    ios: {
      shadowColor: '#0B2A16',
      shadowOpacity: 0.18,
      shadowRadius: 14,
      shadowOffset: { width: 0, height: -2 },
    },
    default: { elevation: 10 },
  }) as ViewStyle,
};

// Mida tactil minima recomanada.
export const MIN_TOUCH = 44;
