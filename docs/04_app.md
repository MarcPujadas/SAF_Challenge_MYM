# 04 — App SAFi (Expo / React Native)

Codi: `frontend/`. Entrada: `App.tsx`, `index.ts`. Navegacio: `src/navigation/RootNavigator.tsx`.

## Pantalles

- `HomeScreen`: accessos principals.
- `ServeisScreen`: cataleg.
- `ReservaScreen`: serveis, franges i reserva.
- `HeatmapScreen`: visio setmanal i diferenciacio entre disponibilitat actual i previsio.
- `MevesReservesScreen`: reserves de l'usuari i cancel-lacio.
- `SafiChatScreen`: consultes naturals.
- `ConfirmacionScreen`: confirmacio.

Components reutilitzables a `src/components/ui/`; tema i verd principal a `src/theme/theme.ts`. `src/components/safi/SafiFloatingCard.tsx` implementa la targeta flotant de recomanacions, separada del contingut amb scroll.

## Comunicacio

`src/services/api/client.ts` apunta a `EXPO_PUBLIC_API_URL`; `index.ts` exposa el contracte de negoci. L'app distingeix `service_id` del `space_id` representatiu. No ha d'utilitzar mocks quan `EXPO_PUBLIC_USE_MOCKS=false`.

`frontend/.env` (no versionat):
```env
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_USE_MOCKS=false
```

Per a Expo Web a **Windows**, `localhost` es correcte. Per a telefon fisic, `localhost` designa el telefon; posa-hi la IP LAN del PC i inicia Uvicorn amb `--host 0.0.0.0`. El PC i telefon han de compartir una xarxa que permeti connexions entrants.

## Chat

`chatSafi` prova `POST /safi/chat-llm` i, si falla, `POST /safi/chat`. La clau Ornith es configura **nomes al backend**, mai a Expo (`EXPO_PUBLIC_*` es visible a l'app).

## Nota demo

El launcher de Windows usa Expo Web per evitar la dependencia d'un telefon. El comportament exacte de gestos/targeta flotant pot ser diferent a navegador i a dispositiu fisic. No s'ha validat una build nativa instal-lable independent.
