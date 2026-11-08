# Portal web SAFi

Portal de reserves i estadistiques per al SAF, integrat amb FastAPI (mateix backend que Expo). Amb **Windows** fes doble clic a `../iniciar_web.bat`; instal-la les dependències automaticament i obre `http://127.0.0.1:5173`.

Manual: `npm ci`, `npm run dev`; per compilar: `npm run build`. El backend ha d'estar actiu a `http://127.0.0.1:8000`. Per canviar-lo, crea `web/.env` amb `VITE_API_URL=http://IP:8000`.

El client `src/services/api.ts` desempaqueta el format `{success,data,error}` del backend; reserva amb `service_id` i camps `start/end`.

Documentacio: `../docs/05_web_dashboard.md`. Recorda que el panell no te autenticacio/autoritzacio real; no exposar-lo publicament.


## Integració de la web de Hajar (8/11/2026)

La vista inicial **Dashboard SAF** es basa en `hajar/web-dashboard` (`c4ecaf3`) i manté el seu disseny. S'ha adaptat al contracte real de FastAPI: els endpoints retornen `{success,data,error}`, amb `reservations_today`, `busiest_space.name`, `reservation_id` i `start`.

Per no perdre feina integrada anteriorment, la pestanya **SAFi Insights** conserva l'analítica avançada i **Fes una reserva** conserva el flux de reserves web. El backend i l'app Expo no s'han substituït.

## Integració final de la branca de Hajar (08/11/2026)

Versió de referència: `hajar/web-dashboard` commit `c52c03b`. La web de Hajar s'ha incorporat a `main` amb el seu estil i el dashboard, els selectors de serveis i la pantalla de reserva, adaptats a l'API multiespai real. `web/src/pages/AdminInsights.tsx` preserva l'analítica avançada ja integrada. Les dades de prova en números fixos s'han eliminat per no presentar-les com a observacions reals.

La configuració del backend és `VITE_API_URL` (base URL sense `/api/v1`). `web/.env.example` és una plantilla pública; **no** copiar `web/.env` del desenvolupador ni incloure claus al ZIP.
