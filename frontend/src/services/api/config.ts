// Unic interruptor: EXPO_PUBLIC_USE_MOCKS=true -> dades simulades (mocks.ts).
// Per defecte (sense la variable o qualsevol altre valor) -> backend real.
export const USE_MOCKS = process.env.EXPO_PUBLIC_USE_MOCKS === 'true';
