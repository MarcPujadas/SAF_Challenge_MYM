# SAF Hack - Tasques v2 i repartiment actualitzat

> Aquest document substitueix el repartiment antic de `tasks.md` per a la fase actual del projecte.
>
> Objectiu: que cada persona i la seva IA sàpiguen **què ha d'implementar, quins fitxers pot tocar, quines APIs ha de consumir o crear i què no ha de duplicar**.

---

# 1. Objectiu de la fase actual

Ja no estem en la fase de crear l'esquelet del projecte.

Ara la prioritat és tenir una demo completa de principi a fi:

```text
APP MÒBIL
   │
   ├── consultar serveis
   ├── consultar disponibilitat
   ├── rebre recomanació SAFi
   └── crear reserva
   │
   ▼
BACKEND FASTAPI
   │
   ├── SQLite
   ├── dades històriques SAF
   ├── recomanador
   ├── SAFi
   └── estadístiques
   │
   ├───────────────────────────────┐
   ▼                               ▼
WEB USUARIS                    WEB ADMIN
reserva web                    dashboard directors
disponibilitat                 ocupació
SAFi                           reserves
                               heatmaps
                               insights
```

La mateixa API i la mateixa base de dades han de servir:

- l'app mòbil,
- la web de reserves,
- el dashboard dels responsables del SAF.

El backend és sempre la font de veritat.

---

# 2. Arquitectura acordada

## Backend

```text
backend/
```

Tecnologies:

- Python
- FastAPI
- SQLite
- Pandas

Responsabilitats:

- dades,
- lògica de negoci,
- reserves,
- disponibilitat,
- recomanacions,
- SAFi,
- estadístiques,
- heatmaps,
- validacions.

Els frontends **no calculen ocupació ni recomanacions**.

---

## App mòbil - Marcos

```text
frontend/
```

Tecnologies:

- React Native
- Expo
- TypeScript

Orientada als usuaris habituals del SAF.

Funcions principals:

- consultar serveis,
- consultar disponibilitat,
- reservar,
- veure recomanacions SAFi,
- consultar reserves,
- SAFi Chat.

---

## Web - Hajar

Crear una nova carpeta:

```text
web/
```

Tecnologia recomanada per la hackathon:

- React
- Vite
- TypeScript

La web tindrà dues zones.

### Zona pública / usuaris

```text
/
 /reservar
 /disponibilitat
 /safi
```

Permet:

- consultar serveis,
- consultar disponibilitat,
- reservar,
- veure heatmap,
- rebre recomanacions SAFi.

### Zona d'administració

```text
/admin
```

Permet als responsables del SAF:

- veure KPI,
- consultar ocupació,
- veure reserves,
- veure heatmaps,
- detectar hores punta,
- detectar hores amb menys demanda,
- detectar espais molt o poc utilitzats,
- consultar insights accionables.

---

# 3. Estat actual de `main`

## Backend implementat

```text
✓ FastAPI
✓ CORS
✓ SQLite
✓ Usuari demo
✓ Espais
✓ Serveis
✓ Importació de dades SAF
✓ Reserves
✓ Persistència de reserves
✓ Validació d'espais
✓ Validació d'usuaris
✓ Validació de franges
✓ Detecció de conflictes
✓ Control de capacitat
✓ Disponibilitat
✓ Franges de 75 minuts per Fitness / Pàdel / Tennis / Esquaix
✓ Processament històric
✓ Occupancy score
✓ Occupancy level
✓ Recommendation service
✓ POST /recommendations
✓ POST /safi/advice
✓ POST /safi/chat
✓ GET /admin/summary
✓ GET /admin/stats
✓ GET /admin/reservations
✓ GET /admin/occupancy
✓ Tests automatitzats
```

Actualment els tests integrats del backend passen.

---

## Backend parcial o pendent

```text
○ GET /availability/heatmap
○ /admin/occupancy connectat a dades històriques reals
○ /admin/stats amb hores punta i hores tranquil·les reals
○ estadístiques històriques més completes
○ SAFi més enllà dels casos principals de Fitness
○ registre de recomanacions acceptades / ignorades
```

Important:

`/admin/occupancy` existeix però encara retorna una estructura buida.

`/admin/stats` existeix però `busiest_hour` i `quietest_hour` encara poden ser `null`.

---

## App mòbil actual

Ja existeixen:

```text
frontend/App.tsx
frontend/src/navigation/
frontend/src/screens/
frontend/src/services/api/
```

També existeix un client API centralitzat amb:

```text
getServices()
getAvailability()
postRecommendations()
createReservation()
getReservations()
```

Però:

```text
USE_MOCKS = true
```

i el flux visual de reserva encara no consumeix realment aquestes funcions.

---

## Web actual

No existeix encara una web separada real.

La branca antiga:

```text
hajar/frontend-ui
```

conté components React Native.

**No s'ha de mergejar directament a `main`.**

Pot servir com a referència visual, però la nova feina de Hajar ha de començar des de `main` en una carpeta nova:

```text
web/
```

---

# 4. Regles per totes les persones i totes les IA

Abans de modificar codi, llegir:

```text
agents.md
architecture.md
contracts.md
tasks_v2.md
```

Regles:

1. No programar directament a `main`.
2. Crear una branca nova des de l'últim `main`.
3. El backend és la font de veritat.
4. App i web només consumeixen APIs.
5. No calcular occupancy scores al frontend.
6. No duplicar el recomanador al frontend.
7. No accedir directament a SQLite des del frontend.
8. No canviar un contracte JSON sense modificar `contracts.md`.
9. No inventar camps que no existeixin al contracte.
10. No pujar datasets SAF al repositori.
11. No tocar `marc/guided-activities-wip` durant aquesta fase.
12. Mantenir els tests existents passant.
13. Cada nova funcionalitat backend ha d'afegir tests.
14. No substituir codi funcional d'una altra persona si no és necessari.
15. Prioritzar la demo completa abans que els extres.

---

# 5. Flux de demo que tots hem de protegir

La fita comuna és:

```text
1. Obrir app o web
2. GET /services
3. Seleccionar servei
4. Seleccionar data
5. GET /availability
6. Seleccionar franja
7. POST /recommendations o POST /safi/advice
8. Mostrar recomanació
9. Usuari decideix
10. POST /reservations
11. Reserva guardada a SQLite
12. GET /admin/reservations
13. La reserva apareix al dashboard
```

Quan aquest recorregut funcioni des de l'app i des de la web, el MVP principal està complet.

---

# 6. MARC - Integració, Backend Core i dades

## Branca recomanada

```text
marc/backend-integration-v2
```

Crear-la des de l'últim `main`.

---

## Responsabilitat

Marc és responsable de:

- estabilitat global del backend,
- coherència de dades,
- contractes,
- integració entre backend, app i web,
- persistència de noves dades generades pel sistema,
- evitar inconsistències entre APIs.

Marc **no ha de construir la UI de Marcos ni la web de Hajar**.

---

## P0 - Tasques immediates

### 1. Revisar i alinear contractes reals

Existeix una incompatibilitat actual.

El frontend espera:

```text
basis.space
```

però el backend retorna:

```text
basis.space_id
```

Escollir un únic format.

Recomanació:

```json
"basis": {
  "space_id": "sala-fitnes-sala-cardio",
  "weekday": "Tuesday",
  "historical_period": "2026-04-01 to 2026-10-31"
}
```

Actualitzar conjuntament:

```text
contracts.md
backend
frontend/src/services/api/types.ts
```

No deixar frontend i backend amb formats diferents.

---

### 2. Revisar IDs de serveis i espais

Evitar hardcodes com:

```text
fitness
```

quan l'espai real és:

```text
sala-fitnes-sala-cardio
```

La UI ha d'utilitzar:

```text
GET /services
→ service.space_id
```

com a font real de l'identificador de l'espai.

---

### 3. Crear tests d'integració del flux complet

Afegir tests que comprovin:

```text
GET /services
→ GET /availability
→ POST /recommendations
→ POST /reservations
→ GET /reservations
→ GET /admin/reservations
```

Objectiu:

una reserva creada des del flux públic ha d'aparèixer també a l'API d'administració.

---

### 4. Donar suport a la integració real de frontends

Quan Marcos i Hajar deixin els mocks:

- validar CORS,
- validar Base URL,
- corregir errors de contracte,
- assegurar respostes consistents,
- evitar regressions.

No adaptar el backend a errors del frontend si això trenca `contracts.md`.

---

## P1 - Històric generat pel propi sistema

Quan el flux complet ja funcioni, començar a guardar informació per millorar SAFi.

Primera versió recomanada:

```text
recommendations
recommendation_actions
```

### `recommendations`

Guardar:

- id,
- user_id,
- space_id,
- date,
- requested_start,
- recommended_start,
- requested_score,
- recommended_score,
- created_at.

### `recommendation_actions`

Guardar:

- recommendation_id,
- action,
- created_at.

`action` podria ser:

```text
accepted
ignored
```

Això permetrà mesurar:

```text
percentatge de recomanacions acceptades
canvi de franja provocat per SAFi
redistribució potencial de demanda
```

---

## P2 - Després de l'MVP

Només quan app + web + dashboard funcionin:

- reprendre `marc/guided-activities-wip`,
- corregir i validar processament d'activitats dirigides,
- incorporar-les a estadístiques,
- donar suport a insights sobre activitats.

No mergejar aquesta branca abans.

---

## Fitxers que Marc controla principalment

```text
backend/app/database/
backend/app/main.py
backend/tests/
backend/scripts/
contracts.md
architecture.md
```

Pot modificar serveis compartits del backend si és necessari, coordinant-ho amb Yassin.

---

## Definition of Done de Marc

P0 acabat quan:

```text
✓ contractes backend/frontend coincideixen
✓ tests actuals continuen passant
✓ existeix test end-to-end de reserva
✓ app i web poden consumir el backend sense workarounds
✓ una reserva creada apareix a admin
```

---

# 7. YASSIN - Heatmap, Analytics, Admin i SAFi Backend

## Branca recomanada

```text
yassin/admin-analytics-v2
```

Crear-la des de l'últim `main`.

---

## Responsabilitat

Yassin transforma les dades del backend en informació útil per:

- usuaris,
- web,
- dashboard,
- SAFi.

Yassin és responsable de les APIs analítiques.

No ha de construir el dashboard visual.

---

## P0 - Tasques immediates

### 1. Implementar GET /api/v1/availability/heatmap

Contracte ja definit a:

```text
contracts.md
```

Ha de permetre:

```text
space_id
from
to
```

i retornar dades reals basades en l'històric processat.

Exemple conceptual:

```json
{
  "space_id": "sala-fitnes-sala-cardio",
  "days": [
    {
      "date": "2026-11-09",
      "slots": [
        {
          "hour": "18:30",
          "occupancy_score": 87,
          "occupancy_level": "very_high"
        }
      ]
    }
  ]
}
```

El frontend no calcula aquests valors.

---

### 2. Implementar realment GET /admin/occupancy

Ara mateix:

```text
spaces: []
```

Ha de consultar les dades històriques processades.

Ha de suportar:

```text
from
to
space_id
```

i retornar per espai:

```text
average_occupancy_score
peak_hour
lowest_hour
```

Si no hi ha dades:

```text
null
unknown
```

No inventar valors.

---

### 3. Millorar GET /admin/stats

Actualment:

```text
busiest_hour = null
quietest_hour = null
```

Connectar aquests camps a les dades reals d'ocupació.

No utilitzar simplement el nombre de reserves creades per l'app com si fos ocupació real.

Afegir només camps que estiguin documentats a `contracts.md`.

---

### 4. Afegir tests

Tests mínims:

```text
heatmap amb dades
heatmap sense dades
filtre per space_id
filtre per dates
admin occupancy
admin stats
dates incorrectes
rang de dates incorrecte
```

---

## P1 - SAFi Insights

Quan les APIs admin bàsiques funcionin, preparar una funció backend que pugui generar insights basats en dades.

Exemples:

```text
Fitness té una demanda alta els dimarts de 18:30 a 19:45.
```

```text
Dijous al vespre presenta més capacitat disponible que dimarts.
```

```text
Aquest espai té una ocupació històrica baixa en aquesta franja.
```

Sempre han de ser justificables.

No afegir endpoint nou sense actualitzar primer `contracts.md`.

Possible endpoint futur:

```text
GET /api/v1/admin/insights
```

però és P1, no P0.

---

## P1 - Ampliar SAFi

Ara SAFi està molt centrat en Fitness.

Després del dashboard MVP:

- permetre consultes sobre altres espais quan les dades ho suportin,
- reutilitzar el mateix recommendation service,
- no crear lògica paral·lela,
- respondre "No ho sé" quan no existeixin dades.

No integrar un LLM fins que el flux estructurat sigui estable.

---

## Fitxers que Yassin controla principalment

```text
backend/app/routers/safi_admin.py
backend/app/services/safi_service.py
backend/app/services/recommendation_service.py
backend/app/services/historical_service.py
backend/tests/test_safi_admin.py
```

Coordinar amb Marc abans de modificar:

```text
database.py
main.py
contracts.md
```

---

## Definition of Done de Yassin

P0 acabat quan:

```text
✓ /availability/heatmap retorna dades reals
✓ /admin/occupancy retorna dades reals
✓ /admin/stats mostra hores punta/tranquil·les reals quan hi ha dades
✓ filtres funcionen
✓ els nous endpoints tenen tests
✓ no es calcula ocupació al frontend
```

---

# 8. MARCOS - App mòbil i integració amb APIs reals

## Branca recomanada

```text
marcos/mobile-api-integration
```

Crear-la des de l'últim `main`.

---

## Responsabilitat

Convertir l'esquelet Expo actual en una app funcional per als usuaris.

Marcos **no implementa lògica de negoci**.

Només:

```text
UI
→ API
→ mostrar resultat
```

---

## P0 - Tasques immediates

### 1. Deixar de dependre dels mocks

Actualment:

```text
USE_MOCKS = true
```

Preparar configuració perquè es pugui utilitzar backend real.

Idealment:

```text
EXPO_PUBLIC_API_URL
```

i un mode clar per canviar entre mocks i backend si encara es necessita durant desenvolupament.

Per la demo final:

```text
backend real
```

---

### 2. Implementar el flux real de reserva

`ReservaScreen.tsx` ha de deixar de ser placeholder.

Flux:

```text
GET /services
      ↓
seleccionar servei
      ↓
seleccionar data
      ↓
GET /availability
      ↓
seleccionar franja
      ↓
POST /recommendations
      ↓
mostrar recomanació SAFi
      ↓
usuari manté o canvia la franja
      ↓
POST /reservations
      ↓
ConfirmacionScreen
```

---

### 3. Utilitzar `service.space_id`

No hardcodejar:

```text
fitness
```

com a espai.

Utilitzar sempre:

```typescript
service.space_id
```

retornat per:

```text
GET /services
```

---

### 4. Gestionar loading i errors

Mostrar correctament:

```text
carregant serveis
carregant disponibilitat
sense disponibilitat
error de xarxa
SLOT_NOT_AVAILABLE
RESERVATION_CONFLICT
INVALID_TIME
```

No mostrar errors tècnics crus a l'usuari.

---

### 5. Confirmació real

`ConfirmacionScreen` ha de mostrar:

```text
servei
data
hora
reservation_id
estat
```

utilitzant la resposta real del backend.

---

## P1 - Les meves reserves

Consumir:

```text
GET /reservations?user_id=demo-user
```

Mostrar:

- servei / espai,
- data,
- hora,
- estat.

Si hi ha temps:

```text
DELETE /reservations/{reservation_id}
```

---

## P1 - SAFi Chat

Crear pantalla que consumeixi:

```text
POST /safi/chat
```

No simular respostes amb `setTimeout`.

Mostrar:

- resposta,
- estat de càrrega,
- "No ho sé amb les dades disponibles" quan correspongui.

---

## P1 - Heatmap mòbil

Quan Yassin acabi:

```text
GET /availability/heatmap
```

consumir-lo.

No calcular heatmap localment.

---

## Fitxers que Marcos controla principalment

```text
frontend/App.tsx
frontend/src/navigation/
frontend/src/screens/
frontend/src/services/api/
frontend/src/state/
frontend/package.json
```

---

## Definition of Done de Marcos

P0 acabat quan des d'un mòbil es pugui:

```text
✓ obrir l'app
✓ carregar serveis reals
✓ escollir un servei
✓ carregar disponibilitat real
✓ escollir una franja
✓ veure una recomanació real
✓ crear una reserva real
✓ veure la confirmació
✓ reserva guardada a SQLite
```

---

# 9. HAJAR - Web pública + Dashboard SAF

## Branca recomanada

```text
hajar/web-dashboard
```

Crear-la **des de l'últim `main`**.

No continuar directament des de:

```text
hajar/frontend-ui
```

La branca antiga es pot consultar com a referència visual.

---

## Responsabilitat

Crear la nova aplicació web.

No modificar:

```text
frontend/
```

de Marcos.

Crear:

```text
web/
```

---

## Estructura recomanada

```text
web/
├── src/
│   ├── pages/
│   │   ├── Home
│   │   ├── Reserva
│   │   ├── Disponibilitat
│   │   └── AdminDashboard
│   │
│   ├── components/
│   │   ├── Heatmap
│   │   ├── SefiAdvice
│   │   ├── KpiCard
│   │   └── OccupancyChart
│   │
│   └── services/
│       └── api/
│
├── package.json
└── ...
```

Preferència:

```text
React + Vite + TypeScript
```

---

## P0 - Web de reserva

La web també ha de permetre reservar.

Flux:

```text
GET /services
      ↓
servei
      ↓
data
      ↓
GET /availability
      ↓
franja
      ↓
POST /recommendations
      ↓
recomanació SAFi
      ↓
POST /reservations
```

Ha de consumir exactament els mateixos contractes que l'app.

---

## P0 - API client web

Crear un únic client API.

Configurar Base URL amb variable d'entorn.

Per exemple:

```text
VITE_API_URL
```

No posar URLs repetides dins dels components.

---

## P0 - Dashboard administradors

Crear ruta:

```text
/admin
```

Primera versió:

### KPI

Consumir:

```text
GET /admin/summary
GET /admin/stats
```

Mostrar almenys:

```text
Total reserves
Reserves d'avui
Espai més utilitzat
Hora punta
```

Quan un valor sigui `null`, no inventar-lo.

---

### Reserves

Consumir:

```text
GET /admin/reservations
```

Mostrar taula:

```text
espai
data
hora
estat
```

---

### Ocupació

Quan Yassin implementi l'API real:

```text
GET /admin/occupancy
```

Mostrar:

```text
ocupació mitjana
hora punta
hora menys ocupada
```

---

### Heatmap

Quan Yassin implementi:

```text
GET /availability/heatmap
```

crear visualització real.

No utilitzar dades hardcoded.

---

## P1 - Filtres dashboard

Afegir:

```text
date from
date to
space_id
```

Sempre enviant filtres al backend.

No filtrar datasets grans manualment al navegador si el backend ja pot fer-ho.

---

## P1 - SAFi Insights

Quan existeixi endpoint backend:

```text
/admin/insights
```

mostrar un bloc de recomanacions accionables.

Exemple:

```text
Fitness està molt saturat els dimarts al vespre.
```

---

## P1 - SAFi públic

La web pot tenir:

```text
/safi
```

consumint:

```text
POST /safi/chat
```

---

## Fitxers que Hajar controla principalment

```text
web/
```

No modificar sense coordinació:

```text
frontend/
backend/
```

---

## Definition of Done de Hajar

P0 acabat quan:

```text
✓ existeix web separada
✓ web consumeix backend real
✓ es pot crear una reserva des de la web
✓ /admin mostra KPI reals
✓ /admin mostra reserves reals
✓ dashboard no utilitza dades hardcoded
✓ una reserva feta des de l'app apareix al dashboard
✓ una reserva feta des de la web apareix al mateix dashboard
```

---

# 10. Coordinació Marc + Yassin

Marc i Yassin treballen tots dos al backend, però amb responsabilitats diferents.

## Marc

```text
integració
persistència
contractes
models
reserves
consistència
tests end-to-end
dades generades pel sistema
```

## Yassin

```text
analytics
heatmaps
occupancy
stats
SAFi
insights
recomanacions
```

Regla:

```text
Marc = sistema i integració
Yassin = interpretació de dades i APIs analítiques
```

Abans de modificar el mateix fitxer:

```text
main.py
database.py
contracts.md
historical_service.py
```

coordinar el canvi.

---

# 11. APIs que ha de consumir cada frontend

## App Marcos

P0:

```text
GET  /api/v1/services
GET  /api/v1/availability
POST /api/v1/recommendations
POST /api/v1/reservations
```

P1:

```text
GET    /api/v1/reservations
DELETE /api/v1/reservations/{id}
POST   /api/v1/safi/advice
POST   /api/v1/safi/chat
GET    /api/v1/availability/heatmap
```

---

## Web Hajar - zona usuari

P0:

```text
GET  /api/v1/services
GET  /api/v1/availability
POST /api/v1/recommendations
POST /api/v1/reservations
```

P1:

```text
POST /api/v1/safi/advice
POST /api/v1/safi/chat
GET  /api/v1/availability/heatmap
```

---

## Web Hajar - admin

P0:

```text
GET /api/v1/admin/summary
GET /api/v1/admin/stats
GET /api/v1/admin/reservations
GET /api/v1/admin/occupancy
```

Quan estigui implementat:

```text
GET /api/v1/availability/heatmap
```

P1 futur, només després de contractar-lo:

```text
GET /api/v1/admin/insights
```

---

# 12. Ordre recomanat de desenvolupament

Treball paral·lel:

```text
MARC
contractes + tests end-to-end + integració

YASSIN
heatmap + admin occupancy + stats

MARCOS
app → APIs reals

HAJAR
web/ → reserva + dashboard
```

---

# 13. Ordre recomanat d'integració

## Fase A

Marc:

```text
contractes coherents
```

Yassin:

```text
heatmap + admin analytics
```

Marcos:

```text
flux reserva mòbil real
```

Hajar:

```text
estructura web + reserva real
```

---

## Fase B

Integrar a `main`:

```text
1. Marc - contractes / integració
2. Yassin - analytics
3. Marcos - app real
4. Hajar - web real
```

Si les branques són independents es poden obrir PR en paral·lel, però abans de merge:

```text
merge main → branca
tests
prova manual
PR
```

---

# 14. Test final obligatori de la demo

## Test 1 - App

```text
obrir app
→ Fitness
→ data
→ disponibilitat
→ recomanació
→ reservar
→ reserva confirmada
```

---

## Test 2 - Dashboard

Sense crear res manualment:

```text
obrir /admin
→ la reserva de l'app apareix
```

---

## Test 3 - Web

```text
obrir web
→ reservar Tennis
→ reserva confirmada
```

---

## Test 4 - Dashboard

```text
refrescar /admin
→ apareix també la reserva web
```

---

## Test 5 - SAFi

```text
seleccionar hora molt ocupada
→ SAFi recomana alternativa
→ mostrar justificació
```

---

## Test 6 - Heatmap

```text
seleccionar Fitness
→ veure dades reals
→ canviar dia / filtre
→ heatmap respon amb dades del backend
```

---

# 15. Què NO prioritzar ara

Fins que el flux anterior funcioni:

```text
✗ login real
✗ notificacions
✗ mapa avançat
✗ ML complex
✗ LLM complet
✗ predicció avançada
✗ activitats dirigides
✗ refactors grans
✗ animacions complexes
```

---

# 16. Fita comuna

Considerem la primera versió completa quan podem demostrar:

```text
APP ────────┐
            │
            ▼
          BACKEND
            │
            ▼
          SQLite
            │
            ▼
       DASHBOARD WEB
            ▲
            │
WEB RESERVA ┘
```

I concretament:

> Una reserva feta des de l'app o des de la web queda guardada al mateix backend i apareix al dashboard dels responsables del SAF.

A partir d'aquí es poden afegir:

- SAFi Insights,
- aprenentatge de recomanacions,
- activitats dirigides,
- comparacions històriques,
- predicció de saturació,
- millores visuals.
