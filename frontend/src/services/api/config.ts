// Configuracio del client API.
//
// EXPO_PUBLIC_USE_MOCKS=true
//   -> utilitza dades simulades de mocks.ts
//
// EXPO_PUBLIC_USE_MOCKS=false
//   -> utilitza el backend FastAPI real
//
// Per defecte utilitzem el backend real perquè
// aquest és el comportament esperat per la demo.

export const USE_MOCKS =
  process.env.EXPO_PUBLIC_USE_MOCKS === 'true';