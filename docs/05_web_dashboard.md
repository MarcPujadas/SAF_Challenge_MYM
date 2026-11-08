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


## Versió de la Hajar integrada

La branca `hajar/web-dashboard` (commit `c4ecaf3`) publica un dashboard bàsic com a punt d'entrada. La vista **Dashboard SAF** utilitza aquesta implementació, adaptant-la als noms de camp i a l'envolupant de l'API actual i mostrant els errors de connexió de manera real. Les funcionalitats avançades que ja existien a `main` es conserven a **SAFi Insights**; la reserva web continua separada. Aquesta integració evita incorporar fitxers d'entorns virtuals o un backend antic.

## Integració definitiva (08/11/2026)

La versió `c52c03b` de `hajar/web-dashboard` s'ha incorporat a `main`. Per mantenir les funcionalitats i la compatibilitat, el dashboard mostra **només dades retornades per la API**, no els valors ficticis del prototip. La nova pantalla de reserva manté el disseny i el pas a pas de la Hajar, però reserva per `service_id`, usa disponibilitat multiespai i respecta les franges `start/end` retornades pel backend. Les recomanacions no confonen previsió amb disponibilitat. La pestanya `SAFi Insights` conserva el treball preexistent. No s'han importat els fitxers `safhack.db` ni `web/.env` de la branca.
