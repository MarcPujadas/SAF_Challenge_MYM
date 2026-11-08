# 05 — Portal web i dashboard d'administracio

Codi: `web/`. Tecnologies: React, TypeScript, Vite, Tailwind. Entrada `web/src/App.tsx`.

## Vistes

- **Reserva** (`src/pages/Reserva.tsx`): selector de servei i data, disponibilitat real setmanal, proposta SAFi opcional, confirmacio a SQLite.
- **Admin Dashboard** (`src/pages/AdminDashboard.tsx`): resum de reserves, ocupacio i estadistiques de recomanacions. Usa exclusivament endpoints del backend.

## Flux web

`src/services/api.ts` es l'unic client d'API: URL `VITE_API_URL` (per defecte `http://localhost:8000`), timeout i lectura de l'envolupant `{success,data,error}`. Les reserves es creen amb `service_id` i claus `start/end` del contracte actual, amb assignacio de subespai al backend.

A l'entorn Windows d'un sol ordinador:
```powershell
cd web
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```
URL habitual: `http://127.0.0.1:5173`. Per connectar a un backend diferent, crea `web/.env` amb `VITE_API_URL=http://IP:8000`.

## Com interpretar el panell

Les metriques de reserves son operatives, mentre que tendències i ocupacio historica provenen de dades processades. Les recomanacions acceptades/ignorades provenen dels registres de SAFi. Un indicador no ha de ser presentat com a assistencia observada quan no ho es.

## Límits

Panell de prova sense control d'accés; no desplegar en public sense autenticacio/autoritzacio. Les dades de demo poden ser sintetiques i s'han d'etiquetar com a tals. Si el backend no respon, revisar `/health`, errors del navegador i configuracio `VITE_API_URL`.
