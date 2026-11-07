# SAF Hack — tasques_v3.md

> Document de treball per a la fase actual.
>
> Aquest document substitueix `tasks_v2.md` com a guia pràctica d’execució.
>
> Objectiu: repartir clarament la feina entre:
>
> - **Copilot → Backend**
> - **Claude Code / Yassin → dades, heatmap, previsió i lògica històrica**
> - **Claude Code / Marcos → app mòbil**
>
> La prioritat màxima és:
>
> 1. separar **disponibilitat actual** de **previsió SAFi**,
> 2. reconstruir el **Heatmap**,
> 3. integrar-lo dins de Reserva,
> 4. corregir cancel·lacions,
> 5. completar serveis i SAFi,
> 6. deixar mapa i disseny visual final per gairebé al final.

---

# 1. Arquitectura de responsabilitats

## Copilot — Backend

Treballa principalment a:

```text
backend/
contracts.md
```

Responsabilitats:

- FastAPI,
- SQLite,
- endpoints,
- validacions,
- contractes JSON,
- disponibilitat real,
- reserves,
- cancel·lacions,
- endpoints setmanals,
- tests backend,
- compatibilitat amb app i web.

Copilot **NO ha de calcular UI**.

Copilot **NO ha de decidir el disseny visual del Heatmap**.

---

## Claude Code — Yassin

Treballa principalment a:

```text
backend/app/services/
backend/scripts/
backend/tests/
```

Responsabilitats:

- dades històriques,
- occupancy score,
- occupancy level,
- previsió,
- heatmap històric,
- completar dies/franges,
- comparació entre dies,
- SAFi multi-servei des del punt de vista de dades,
- normalització de serveis/espais,
- funcions reutilitzables de dades.

Yassin **NO ha de modificar pantalles React Native**.

Yassin **NO ha de duplicar endpoints que ja pot exposar Copilot des del router**.

---

## Claude Code — Marcos

Treballa principalment a:

```text
frontend/
```

Responsabilitats:

- React Native,
- Expo,
- navegació,
- pantalles,
- consum d’API,
- Heatmap,
- Reserva,
- Serveis,
- Meves reserves,
- SAFi,
- UX funcional,
- estats loading/error/empty.

Marcos **NO calcula ocupació**.

Marcos **NO calcula prediccions**.

Marcos **NO accedeix directament a SQLite**.

---

# 2. Regles generals

Abans de tocar codi, cada IA ha de llegir:

```text
agents.md
architecture.md
contracts.md
idees_v2.md
tasques_v3.md
```

Regles:

1. No treballar directament a `main`.
2. Crear branca des de l’últim `main`.
3. Backend és la font de veritat.
4. App només consumeix APIs.
5. No calcular `occupancy_score` al frontend.
6. No calcular recomanacions al frontend.
7. No inventar camps nous sense actualitzar `contracts.md`.
8. No canviar noms de camps existents sense coordinar-ho.
9. Mantenir tests existents passant.
10. Cada endpoint nou ha de tenir tests.
11. No eliminar funcionalitat existent si no és necessari.
12. No fer refactors massius sense relació amb la tasca.
13. Fer diffs petits i fàcils de revisar.
14. No pujar datasets del SAF al repositori.
15. No integrar encara mapa ni disseny visual final fins que Heatmap + Reserva estiguin tancats.

---

# 3. Prioritats globals

## P0 — Fer ara

```text
Disponibilitat actual vs previsió
Heatmap nou
dies a l’eix X
hores a l’eix Y
tots els dies
totes les franges
tots els serveis
Heatmap dins Reserva
Heatmap clicable
```

## P1 — Just després

```text
recomanació descartable
cancel·lació correcta
SAFi multi-servei
recomanar altres dies
pantalla Serveis
```

## P2 — Quan el flux principal sigui estable

```text
navegació millorada
serveis amb imatges
mapa SAF
```

## P3 — Final

```text
logo
verd corporatiu
tipografia
cards
icones
espaiat
poliment UX
```

---

# 4. COPILOT — TASQUES BACKEND

# 4.1 Revisar `GET /services`

## Objectiu

Assegurar que l’API retorna tots els serveis correctes i que l’app pot distingir:

```text
reservable = true
reservable = false
```

## Revisar

```text
backend/app/main.py
backend/app/database/database.py
backend/scripts/import_services.py
backend/scripts/import_spaces.py
```

## Comprovacions

- tots els serveis esperats existeixen,
- cada servei té `space_id`,
- cap `space_id` apunta a un espai inexistent,
- no hi ha duplicats,
- `reservable` és correcte,
- no s’estan amagant serveis per error.

## Tests

Afegir tests que comprovin:

```text
GET /services
→ retorna tots els serveis
→ cap id duplicat
→ tots els space_id són vàlids
```

---

# 4.2 Separar disponibilitat actual i previsió

## Problema actual

`GET /availability` retorna informació de disponibilitat i també informació històrica.

A nivell de producte s’han de considerar conceptes diferents.

## Disponibilitat actual

Ha de venir de:

```text
SQLite
reservations
capacity
conflicts
```

## Previsió

Ha de venir de:

```text
historical_occupancy.csv
historical_service.py
```

## Decisió de compatibilitat

No trencar l’app actual si no és necessari.

Es pot mantenir:

```json
{
  "start": "18:30",
  "end": "19:45",
  "available": true,
  "remaining_capacity": 12,
  "occupancy_level": "high",
  "occupancy_score": 82
}
```

però documentant clarament:

```text
available + remaining_capacity
= disponibilitat actual

occupancy_level + occupancy_score
= previsió històrica
```

---

# 4.3 Crear endpoint setmanal de disponibilitat actual

## Nou endpoint

```text
GET /api/v1/availability/week
```

## Query params

```text
space_id
from
to
```

## Objectiu

Permetre construir un Heatmap de disponibilitat real per setmana.

## Font

Només:

```text
SQLite
reservations
capacity
```

No històric.

## Resposta orientativa

```json
{
  "success": true,
  "data": {
    "space_id": "sala-fitnes-sala-cardio",
    "days": [
      {
        "date": "2026-11-09",
        "slots": [
          {
            "start": "07:15",
            "end": "08:30",
            "available": true,
            "remaining_capacity": 21
          }
        ]
      }
    ]
  },
  "error": null
}
```

## Regles

- retornar tots els dies del rang,
- retornar totes les franges vàlides,
- si no hi ha reserves, la franja continua existint,
- si no hi ha capacitat configurada, usar `null` quan correspongui,
- no inventar disponibilitat si l’espai no és reservable.

## Errors

```text
INVALID_DATE
INVALID_DATE_RANGE
INVALID_SPACE
```

## Tests

Cobrir:

- setmana completa,
- espai amb reserves,
- espai sense reserves,
- franja plena,
- rang de dates,
- dates invàlides,
- espai invàlid.

---

# 4.4 Cancel·lacions

## Comportament requerit

```text
DELETE /reservations/{id}
→ status = cancelled
```

Però:

```text
GET /reservations?user_id=demo-user
```

ha de retornar per defecte només reserves:

```text
confirmed
```

## Opció futura

Es pot afegir:

```text
include_cancelled=true
```

però no és necessari per l’MVP.

## Important

Les reserves cancel·lades s’han de conservar a SQLite.

No esborrem el registre.

Això permet:

- estadístiques,
- auditoria,
- dashboard admin.

## Tests

```text
crear reserva
→ consultar
→ cancel·lar
→ consultar de nou
→ ja no apareix a GET /reservations
```

---

# 4.5 Contractes

Actualitzar `contracts.md` amb:

```text
GET /availability/week
```

i aclarir explícitament:

```text
availability = estat actual de reserves

occupancy_score / occupancy_level = previsió històrica
```

No utilitzar la paraula “real-time occupancy” si no disposem d’un sensor o font real.

---

# 4.6 No tocar ara

Copilot no ha de dedicar temps ara a:

```text
login
auth
notifications
profile
ML avançat
map coordinates
visual design
```

---

# 5. CLAUDE CODE / YASSIN — DADES I PREVISIÓ

# 5.1 Revisar `historical_service.py`

## Objectiu

Assegurar que el Heatmap de previsió pot representar una setmana sencera de manera coherent.

Actualment el frontend depèn de les dades que realment existeixen al CSV.

Això pot provocar:

```text
només 1 dia
només 3 hores
franges absents
```

---

# 5.2 Retornar tots els dies del rang

Quan es demana:

```text
from=2026-11-09
to=2026-11-15
```

el backend ha de poder construir els 7 dies encara que algun dia no tingui mostres.

Exemple:

```json
{
  "date": "2026-11-12",
  "slots": []
}
```

o preferiblement slots amb:

```json
{
  "occupancy_score": null,
  "occupancy_level": "unknown"
}
```

---

# 5.3 Retornar totes les franges vàlides

No utilitzar només:

```text
hores presents al dataset
```

com a definició del Heatmap.

Per cada tipus d’espai, definir franges vàlides.

Fitness ja té:

```text
07:15
08:30
09:45
11:00
12:15
13:30
14:45
16:00
17:15
18:30
19:45
```

Per altres serveis:

- detectar franges reals,
- reutilitzar dades processades,
- no inventar hores.

Si una franja és vàlida però no té mostres:

```text
score = null
level = unknown
```

---

# 5.4 Revisar múltiples serveis

La previsió no ha de funcionar només bé per Fitness.

Revisar:

```text
Piscina 25 m
Piscina 16 m
Pàdel
Tennis
Esquaix
Futbol 7
Activitats dirigides
```

Per cada servei:

- confirmar `space_id`,
- confirmar dades històriques,
- confirmar franges,
- confirmar occupancy score.

---

# 5.5 Comparació entre dies

Crear una funció reutilitzable semblant a:

```python
get_best_day_alternative(
    space_id,
    preferred_date,
    preferred_start
)
```

## Objectiu

Trobar un dia proper amb menor ocupació per la mateixa hora.

Exemple:

```text
Dimarts 18:30 → 89
Dijous 18:30 → 52
```

Retorn:

```json
{
  "date": "2026-11-12",
  "start": "18:30",
  "occupancy_score": 52,
  "occupancy_level": "medium"
}
```

## Regles

- comparar dies propers,
- mantenir la mateixa hora quan sigui possible,
- no recomanar dies sense dades,
- no recomanar una alternativa si no és millor.

---

# 5.6 SAFi multi-servei

Generalitzar la lògica perquè SAFi pugui respondre preguntes sobre:

```text
fitness
piscina
pàdel
tennis
esquaix
futbol
activitats dirigides
```

## Detectar

- servei,
- data,
- dia,
- hora,
- intenció.

Exemples que han de funcionar:

```text
Quan hi ha menys gent al fitness?

Quan és millor anar a piscina?

Quina hora és millor per pàdel?

Quin dia està més tranquil el tennis?

Hi ha alternativa a les 18:30?
```

## Regla essencial

Si no hi ha dades:

```text
can_answer = false
```

No inventar.

---

# 5.7 Tests Yassin

Afegir tests per:

- setmana completa,
- dies sense dades,
- hores sense dades,
- múltiples serveis,
- comparació entre dies,
- millor dia alternatiu,
- cap alternativa millor,
- SAFi multi-servei.

---

# 5.8 Entrega a Copilot

Yassin ha de deixar funcions reutilitzables.

Copilot serà qui les exposi a través dels endpoints si cal.

Evitar duplicar routers.

---

# 6. CLAUDE CODE / MARCOS — APP MÒBIL

# 6.1 Actualitzar branca

Abans de continuar:

```text
marcos/mobile-api-integration
```

ha d’actualitzar-se amb l’últim `main`.

Resoldre conflictes amb cura.

Especialment:

```text
frontend/.env.example
frontend/src/services/api/config.ts
frontend/src/services/api/types.ts
frontend/src/services/api/index.ts
frontend/src/services/api/mocks.ts
```

---

# 6.2 Redissenyar funcionalment `HeatmapScreen.tsx`

Aquesta és la primera gran tasca de Marcos.

## Eixos

Canviar a:

```text
X = dies de la setmana
Y = hores
```

Exemple:

```text
        Dl  Dt  Dc  Dj  Dv  Ds  Dg

07:15   🟢  🟢  🟢  🟢  🟢  —   —
08:30   🟢  🟡  🟢  🟡  🟢  🟡  —
...
18:30   🔴  🔴  🔴  🟡  🔴  🟡  —
19:45   🔴  🟡  🔴  🟢  🟡  —   —
```

---

# 6.3 Dos modes

Afegir selector:

```text
[ Disponibilitat ] [ Previsió SAFi ]
```

## Disponibilitat

Consumeix:

```text
GET /availability/week
```

Mostra:

```text
disponible
limitada
completa
```

## Previsió SAFi

Consumeix:

```text
GET /availability/heatmap
```

Mostra:

```text
low
medium
high
very_high
unknown
```

---

# 6.4 Tots els serveis

El selector del Heatmap ha de mostrar tots els serveis que retorni:

```text
GET /services
```

No filtrar serveis de manera incorrecta.

Si un servei no té previsió:

```text
Sense dades de previsió
```

però l’usuari el pot continuar veient.

---

# 6.5 Cel·les clicables

Cada cel·la ha de poder:

```text
seleccionar servei
seleccionar data
seleccionar hora
```

i anar a:

```text
Reserva
```

Afegir paràmetres a navegació:

```typescript
Reserva: {
  serviceId?: string;
  spaceId?: string;
  date?: string;
  start?: string;
}
```

o estructura equivalent.

---

# 6.6 Integrar Heatmap dins `ReservaScreen.tsx`

Quan l’usuari selecciona un servei:

```text
mostrar mini heatmap
```

Ordre:

```text
1. Servei
2. Heatmap
3. Dia/hora
4. SAFi
5. Confirmar
```

No cal duplicar tota `HeatmapScreen`.

Crear un component reutilitzable:

```text
HeatmapGrid
```

Possible ubicació:

```text
frontend/src/components/HeatmapGrid.tsx
```

---

# 6.7 Mostrar disponibilitat i previsió separades

Quan l’usuari selecciona una franja:

```text
18:30 - 19:45

Disponibilitat actual
✓ Disponible
12 places

Previsió SAFi
🔴 Alta
82 / 100
```

No presentar:

```text
occupancy_score
```

com si fos ocupació actual.

---

# 6.8 Recomanacions descartables

A `ReservaScreen.tsx` afegir:

```text
✕
```

a la targeta de SAFi.

Estat:

```typescript
const [adviceDismissed, setAdviceDismissed] = useState(false);
```

Quan canvia la franja:

```text
adviceDismissed = false
```

Quan prem `✕`:

```text
adviceDismissed = true
```

SAFi no ha de bloquejar mai:

```text
Confirmar
```

---

# 6.9 Cancel·lació correcta

A `MevesReservesScreen.tsx`:

## Després de cancel·lar

- eliminar visualment la reserva o marcar-la breument,
- refrescar la llista.

## Quan l’usuari surt i torna

Utilitzar:

```text
useFocusEffect
```

per tornar a executar:

```text
getReservations()
```

La reserva cancel·lada no ha de tornar a aparèixer.

---

# 6.10 Pantalla Serveis

Crear:

```text
frontend/src/screens/ServeisScreen.tsx
```

Cada servei ha de mostrar:

```text
nom
descripció
reservable / no reservable
botó disponibilitat
botó reservar si és reservable
```

En una fase posterior:

```text
imatge
horari
localització
```

---

# 6.11 SAFi multi-servei

Quan backend/Yassin ho tinguin estable:

Marcos només ha d’assegurar que `SafiChatScreen`:

- no assumeix Fitness,
- mostra errors,
- mostra `can_answer=false`,
- mostra resposta del backend tal qual.

No afegir intel·ligència al frontend.

---

# 6.12 Recomanació d’altres dies

Quan el backend retorni una alternativa de dia:

Mostrar:

```text
Millor alternativa
Dijous · 18:30

[Canviar a dijous]
```

En tocar:

```text
date = dijous
start = 18:30
```

---

# 7. Componentització recomanada frontend

Per evitar duplicació:

```text
frontend/src/components/
```

Crear si és útil:

```text
HeatmapGrid.tsx
HeatmapLegend.tsx
ServiceCard.tsx
SafiAdviceCard.tsx
AvailabilityBadge.tsx
ForecastBadge.tsx
```

No cal fer-ho tot si complica l’MVP.

Prioritzar claredat.

---

# 8. Mapa del SAF — NO ARA

El mapa queda per gairebé al final.

No començar fins que estiguin completats:

```text
Heatmap
Reserva
Cancel·lació
Serveis
SAFi
```

Versió inicial:

```text
imatge/plànol
punts clicables
```

No cal GIS.

---

# 9. Disseny visual — DESPRÉS DE FUNCIONALITAT

Quan tot l’anterior funcioni:

## Direcció visual

```text
verd principal
logo SAF
imatges reals
cards
icones
tipografia coherent
millor spacing
botons menys genèrics
navegació inferior
```

No començar refactor visual gran abans de tancar funcionalitat.

---

# 10. Ordre exacte de treball

## PAS 1 — Copilot

```text
/services
availability actual vs forecast
GET /availability/week
cancel·lacions
contracts
tests
```

## PAS 2 — Yassin

En paral·lel:

```text
completar Heatmap històric
tots els dies
totes les franges
multi-servei
comparació entre dies
SAFi multi-servei
tests
```

## PAS 3 — Integració backend

Copilot integra les funcions de Yassin si cal.

Executar:

```text
pytest
```

Tots els tests han de passar.

## PAS 4 — Marcos

```text
Update from main
HeatmapScreen
Disponibilitat / Previsió
eixos correctes
tots els serveis
cel·les clicables
Heatmap dins Reserva
recomanació descartable
cancel·lació correcta
```

## PAS 5 — Marcos + backend

Provar flux complet:

```text
obrir app
→ servei
→ heatmap
→ disponibilitat
→ previsió
→ seleccionar franja
→ SAFi
→ confirmar
→ reserva
→ Meves reserves
→ cancel·lar
→ sortir
→ tornar
→ reserva cancel·lada no apareix
```

## PAS 6

```text
SAFi multi-servei
altres dies
ServeisScreen
```

## PAS 7 — Quasi final

```text
Mapa
navegació
UI visual
```

---

# 11. Criteris d’acceptació globals

## Heatmap

Ha de complir:

```text
✓ dies a X
✓ hores a Y
✓ setmana completa
✓ totes les franges
✓ selector Disponibilitat / Previsió
✓ tots els serveis
✓ cel·les clicables
✓ unknown quan falten dades
✓ no confondre forecast amb disponibilitat actual
```

---

## Reserva

```text
✓ servei
✓ mini heatmap
✓ disponibilitat actual
✓ previsió
✓ seleccionar franja
✓ SAFi
✓ tancar SAFi
✓ alternativa
✓ confirmar
✓ persistir
```

---

## Cancel·lació

```text
✓ cancel·lar
✓ status backend = cancelled
✓ desapareix de llista activa
✓ sortir
✓ tornar
✓ no reapareix
```

---

## SAFi

```text
✓ Fitness
✓ Piscina
✓ Pàdel
✓ Tennis
✓ altres serveis amb dades
✓ hora
✓ dia
✓ alternativa
✓ no inventar
```

---

## Serveis

```text
✓ tots visibles a ServeisScreen
✓ reservables identificats
✓ no reservables visibles
✓ disponibilitat
✓ reservar
```

---

# 12. Què NO s’ha de fer encara

No dedicar temps ara a:

```text
login real
registre
perfil complet
push notifications
preferències personals
ML avançat
recomanacions personalitzades
predicció meteorològica
GIS
```

---

# 13. Branques recomanades

## Copilot

```text
marc/backend-availability-v3
```

## Yassin

```text
yassin/forecast-heatmap-v3
```

## Marcos

```text
marcos/mobile-heatmap-v3
```

Cada branca ha de sortir de:

```text
main
```

actualitzat.

---

# 14. Regla de merge

Ordre recomanat:

```text
1. Yassin → main o branca backend comuna
2. Copilot integra backend final
3. pytest
4. merge backend a main
5. Marcos actualitza des de main
6. implementa frontend
7. proves físiques
8. merge frontend
```

Si Copilot i Yassin treballen en paral·lel:

- Yassin toca serveis de dades,
- Copilot toca routers, contracts i tests d’API,
- evitar editar massivament els mateixos fitxers.

---

# 15. Objectiu final d’aquesta fase

Quan aquesta fase acabi, l’app ha de poder demostrar:

```text
L’usuari veu què està disponible ara.

L’usuari veu quan acostuma a haver-hi menys gent.

Pot comparar tota la setmana.

Pot tocar directament una franja.

SAFi pot suggerir una alternativa.

Pot reservar.

Pot veure la reserva.

Pot cancel·lar-la.

Quan torna a entrar, la cancel·lada ja no apareix.
```

Aquest és el nucli funcional que s’ha de completar abans de passar al mapa i al disseny visual final.
