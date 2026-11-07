# SAF Hack — idees_v2.md

## 1. Objectiu d’aquesta versió

Aquest document redefineix les prioritats actuals de l’app SAF Hack després de revisar l’estat real del projecte, el backend ja implementat i les funcionalitats existents a la branca mòbil.

L’objectiu és deixar de pensar només en “afegir pantalles” i passar a millorar la coherència funcional del producte.

Les dues prioritats principals són:

1. **Diferenciar clarament la disponibilitat actual de la previsió d’ocupació.**
2. **Millorar completament el Heatmap perquè sigui útil, llegible i integrat dins del flux de reserva.**

A partir d’aquí s’han de completar els serveis disponibles, millorar SAFi, corregir el comportament de cancel·lacions i, gairebé al final, implementar el mapa del SAF i el disseny visual final.

---

# 2. Concepte clau: Disponibilitat actual vs previsió

Actualment l’app barreja visualment informació que prové de fonts diferents.

Això s’ha de corregir perquè l’usuari entengui perfectament què és informació real del sistema de reserves i què és una estimació basada en l’històric.

## 2.1 Disponibilitat actual

La disponibilitat actual ha de provenir de les reserves existents al sistema.

Ha de respondre preguntes com:

- Aquesta franja es pot reservar?
- Quantes places queden?
- Aquesta pista està ocupada?
- Aquesta franja està completa?
- Hi ha conflicte amb una altra reserva?

Exemple:

```text
18:30 - 19:45
Disponible
12 places lliures
```

Aquesta dada ha de venir del backend de reserves.

No és una predicció.

---

## 2.2 Previsió d’ocupació

La previsió ha de provenir de les dades històriques del SAF.

Ha de respondre preguntes com:

- Aquesta franja acostuma a estar molt plena?
- Quin dia acostuma a tenir menys ocupació?
- Aquesta hora acostuma a ser tranquil·la?
- Hi ha una alternativa millor?

Exemple:

```text
18:30 - 19:45
Previsió SAFi: ocupació alta
Score històric: 82/100
```

Aquesta informació és estadística.

No s’ha de presentar com a ocupació en temps real.

---

## 2.3 Com s’ha de mostrar a l’app

Cada franja hauria de mostrar dos blocs diferenciats.

Exemple:

```text
18:30 - 19:45

Disponibilitat actual
✓ Disponible
12 places

Previsió SAFi
🔴 Ocupació habitual alta
82 / 100
```

L’usuari ha de poder entendre en menys d’un segon que:

- la franja es pot reservar,
- però normalment és una hora molt plena.

Aquest contrast és una de les parts més importants del projecte.

---

# 3. PRIORITAT 0 — Redissenyar el Heatmap

Aquesta és la funcionalitat que s’ha de millorar abans que qualsevol altra feature gran.

Actualment el Heatmap té limitacions importants:

- en alguns casos només mostra un dia,
- mostra poques franges,
- no queda clar si representa disponibilitat actual o històric,
- els dies no estan en l’eix més natural,
- no està integrat dins del procés de reserva,
- no permet navegar fàcilment entre dates,
- no serveix encara com una eina clara de decisió.

---

## 3.1 Estructura visual nova

El Heatmap principal ha de tenir:

- **dies de la setmana a l’eix X**
- **hores a l’eix Y**

Exemple:

```text
            Dl   Dt   Dc   Dj   Dv   Ds   Dg

07:15       🟢   🟢   🟢   🟢   🟢   —    —
08:30       🟢   🟡   🟢   🟡   🟢   🟡   —
09:45       🟡   🟡   🟡   🟢   🟡   🟢   🟢
11:00       🟡   🟢   🟡   🟢   🟢   🟢   🟢
12:15       🟢   🟢   🟡   🟡   🟢   🟡   🟢
13:30       🟢   🟡   🟡   🟢   🟢   🟢   —
14:45       🟡   🟡   🟢   🟢   🟡   🟢   —
16:00       🟡   🟡   🟡   🟢   🟡   🟡   —
17:15       🟡   🔴   🟡   🟡   🔴   🟡   —
18:30       🔴   🔴   🔴   🟡   🔴   🟡   —
19:45       🔴   🟡   🔴   🟢   🟡   —    —
```

Això permet comparar dies ràpidament.

És molt més útil que posar els dies en files i les hores en columnes.

---

## 3.2 Dos modes de Heatmap

El Heatmap hauria de permetre alternar entre:

```text
[ DISPONIBILITAT ] [ PREVISIÓ SAFi ]
```

### Mode A — Disponibilitat actual

Representa les reserves creades i la capacitat real del sistema.

Possible escala:

```text
🟢 disponible
🟡 disponibilitat limitada
🔴 complet / no disponible
⚪ no reservable
```

### Mode B — Previsió SAFi

Representa la previsió històrica.

Escala:

```text
🟢 ocupació baixa
🟡 ocupació mitjana
🟠 ocupació alta
🔴 ocupació molt alta
⚪ sense dades
```

---

## 3.3 Heatmap combinat opcional

També es pot plantejar una visualització compacta combinada.

Exemple:

```text
🟢 + 82
```

on:

- el color exterior representa disponibilitat actual,
- el score representa previsió històrica.

Però per l’MVP és preferible tenir dos modes separats perquè és més fàcil d’entendre.

---

## 3.4 Navegació per setmanes

El Heatmap ha de permetre:

```text
< Setmana anterior     9 - 15 nov     Setmana següent >
```

Per defecte:

- setmana actual,
- o pròxims 7 dies.

Per la demo pot ser suficient amb:

```text
Setmana actual
Setmana següent
```

---

## 3.5 Selecció de servei

El selector de serveis ha de mostrar tots els serveis vàlids.

No només tres.

Possible format:

```text
Fitness
Piscina 25 m
Piscina 16 m
Pàdel
Tennis
Esquaix
Futbol 7
Activitats dirigides
...
```

Si un servei no té dades històriques suficients:

```text
Previsió SAFi no disponible
```

però no s’ha d’amagar necessàriament.

---

## 3.6 Cel·les clicables

Cada cel·la ha de ser interactiva.

Exemple:

```text
Usuari toca:

Dijous
19:45
🟢
```

L’app ha de poder:

```text
seleccionar servei
seleccionar dijous
seleccionar 19:45
→ obrir Reserva
```

Aquest pas farà que el Heatmap deixi de ser una pantalla informativa i passi a formar part real del flux de reserva.

---

# 4. PRIORITAT 0 — Integrar Heatmap dins de Reserva

El Heatmap no ha de viure només en una pantalla independent.

Quan l’usuari entri a reservar:

```text
1. Servei
2. Disponibilitat de la setmana
3. Dia i hora
4. SAFi
5. Confirmació
```

---

## 4.1 Flux nou recomanat

```text
Seleccionar servei
       ↓
Mostrar mini Heatmap
       ↓
Usuari veu dies/hores
       ↓
Selecciona una cel·la
       ↓
Veu detall de la franja
       ↓
SAFi pot donar recomanació
       ↓
Confirmar reserva
```

---

## 4.2 Mini Heatmap dins Reserva

No cal que sigui tan gran com la pantalla completa.

Exemple:

```text
Disponibilitat / previsió

        Dl  Dt  Dc  Dj  Dv
17:15   🟡  🔴  🟡  🟢  🟡
18:30   🔴  🔴  🔴  🟡  🔴
19:45   🔴  🟡  🟡  🟢  🟡
```

En tocar:

```text
Dj 19:45
```

es selecciona automàticament:

```text
date
start
end
```

---

# 5. PRIORITAT 0 — Backend necessari pel nou Heatmap

El backend actual té:

```text
GET /availability
GET /availability/heatmap
```

però cal separar millor els dos conceptes.

---

## 5.1 Disponibilitat actual

`GET /availability`

ha de continuar sent la font de veritat per la disponibilitat actual.

Ha de retornar per cada slot:

```json
{
  "start": "18:30",
  "end": "19:45",
  "available": true,
  "remaining_capacity": 12
}
```

A més pot retornar la previsió per comoditat, però s’ha de distingir clarament.

Idealment:

```json
{
  "start": "18:30",
  "end": "19:45",
  "availability": {
    "available": true,
    "remaining_capacity": 12
  },
  "forecast": {
    "occupancy_score": 82,
    "occupancy_level": "high"
  }
}
```

Si no es vol trencar el contracte existent, es pot mantenir l’estructura actual però la UI ha de separar conceptualment els camps.

---

## 5.2 Heatmap de disponibilitat real

Cal una manera de consultar una setmana sencera de disponibilitat actual.

Opció recomanada:

```text
GET /api/v1/availability/week
```

Paràmetres:

```text
space_id
from
to
```

Resposta:

```json
{
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
}
```

Aquesta API ha de consultar la base de dades actual de reserves.

No ha d’utilitzar l’històric per decidir si una franja està lliure.

---

## 5.3 Heatmap de previsió

L’endpoint:

```text
GET /availability/heatmap
```

pot continuar existint com a previsió basada en històric.

Però cal considerar canviar el nom en una futura versió a:

```text
GET /forecast/heatmap
```

o:

```text
GET /occupancy/forecast
```

per evitar confusions.

Per no trencar l’app actual, es pot mantenir el nom de moment i documentar clarament que és una previsió històrica.

---

## 5.4 Garantir tots els dies

El backend ha de retornar tots els dies demanats dins del rang.

Si un dia no té dades:

```json
{
  "date": "2026-11-12",
  "slots": []
}
```

o slots amb:

```text
occupancy_level = unknown
occupancy_score = null
```

Això evita que el frontend mostri només un dia perquè els altres no apareixen a la resposta.

---

## 5.5 Garantir totes les franges

El backend ha de definir les franges vàlides per cada servei.

Exemple Fitness:

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

El Heatmap no hauria de dependre només de les hores que apareixen als registres històrics.

Si una franja és vàlida però no té dades:

```text
unknown
```

en comptes de desaparèixer.

---

# 6. PRIORITAT 0 — Mostrar tots els serveis

Actualment l’app pot acabar mostrant només una part dels serveis.

Això s’ha de revisar tant a backend com a frontend.

---

## 6.1 Backend

Comprovar:

```text
GET /services
```

i verificar:

- quants serveis retorna,
- quants tenen `reservable = true`,
- quins `space_id` tenen,
- si hi ha serveis que desapareixen perquè no tenen mapatge,
- si hi ha serveis duplicats,
- si alguna normalització els està excloent.

---

## 6.2 Frontend

A `ReservaScreen` actualment es fa:

```typescript
setServices(list.filter((s) => s.reservable));
```

Això significa que qualsevol servei amb:

```text
reservable = false
```

desapareix.

Cal decidir:

### Pantalla Reserva

Mostrar només serveis reservables.

### Pantalla Serveis

Mostrar tots els serveis:

```text
reservable
no reservable
consulta
```

D’aquesta manera no es perd informació del SAF.

---

# 7. PRIORITAT 1 — Recomanacions SAFi descartables

Les recomanacions no han d’interrompre l’usuari.

Cada targeta SAFi ha de tenir:

```text
✕
```

a la cantonada superior.

Exemple:

```text
┌─────────────────────────────┐
│ SAFi                     ✕ │
│ Aquesta hora acostuma...   │
│                             │
│ [Canviar a 19:45]          │
└─────────────────────────────┘
```

---

## 7.1 Comportament

Quan l’usuari toca la `✕`:

```text
la recomanació desapareix
```

i la reserva continua normalment.

No ha de bloquejar:

```text
Confirmar
```

---

## 7.2 Estat frontend

Afegir:

```typescript
const [adviceDismissed, setAdviceDismissed] = useState(false);
```

Quan es selecciona una nova franja:

```text
adviceDismissed = false
```

Quan es prem `✕`:

```text
adviceDismissed = true
```

Només mostrar la recomanació si:

```text
advice && !adviceDismissed
```

---

## 7.3 Registre accepted / ignored

Per ara aquesta analítica no és prioritària.

No s’ha de complicar l’experiència per registrar-ho.

Es pot mantenir internament, però no ha de condicionar cap funcionalitat de l’app.

---

# 8. PRIORITAT 1 — Cancel·lació de reserves

Actualment existeix la cancel·lació.

S’ha de millorar el comportament visual.

---

## 8.1 Comportament requerit

Quan l’usuari cancel·la una reserva:

```text
reserva confirmada
↓
Cancel·lar
↓
Confirmació
↓
DELETE /reservations/{id}
↓
backend marca la reserva cancel·lada
```

A la pantalla actual es pot mostrar temporalment com:

```text
Cancel·lada
```

si es vol donar feedback immediat.

Però quan l’usuari surt de:

```text
Les meves reserves
```

i torna a entrar:

```text
la reserva cancel·lada NO ha d’aparèixer
```

---

## 8.2 Backend

`GET /reservations`

ha de retornar per defecte només:

```text
status = confirmed
```

o bé s’ha d’afegir un paràmetre:

```text
include_cancelled=false
```

Per l’app d’usuari, el comportament per defecte recomanat és:

```text
no mostrar cancel·lades
```

L’històric administratiu sí que pot conservar-les.

---

## 8.3 Frontend

Quan es cancel·la:

1. cridar API,
2. treure la reserva de la llista local o marcar-la temporalment,
3. quan es torna a entrar a la pantalla, tornar a carregar:

```text
GET /reservations
```

4. la reserva cancel·lada no ha de tornar.

És important refrescar també quan la pantalla recupera focus, no només en el primer `useEffect`.

Es recomana utilitzar:

```text
useFocusEffect
```

de React Navigation.

---

# 9. PRIORITAT 1 — SAFi multi-servei

Actualment SAFi funciona principalment amb Fitness.

S’ha d’ampliar perquè entengui:

```text
Fitness
Piscina 25 m
Piscina 16 m
Pàdel
Tennis
Esquaix
Futbol
Activitats dirigides
```

Exemples:

```text
Quan està més buida la piscina?

Quina hora és millor per anar a pàdel?

Quan hi ha menys gent al fitness?

Quin dia és millor per tennis?
```

---

## 9.1 Backend

Ampliar:

```text
SPACE_ALIASES
```

i la detecció d’intenció.

SAFi ha de:

1. detectar servei,
2. detectar data o dia,
3. detectar hora opcional,
4. consultar històric,
5. respondre només si té dades.

Si no té informació suficient:

```text
No tinc prou dades per respondre això.
```

No inventar.

---

# 10. PRIORITAT 1 — Recomanar altres dies

Ara SAFi recomana principalment una altra hora del mateix dia.

S’ha d’afegir comparació entre dies.

Exemple:

```text
Dimarts 18:30 → 89
Dijous 18:30 → 52
```

Resposta:

```text
Dimarts a les 18:30 acostuma a estar molt ple.
Si tens flexibilitat, dijous a aquesta hora sol estar més tranquil.
```

---

## 10.1 Backend

Crear una funció aproximada:

```python
get_best_day_alternative(
    space_id,
    preferred_date,
    preferred_start
)
```

Ha de comparar:

```text
mateixa hora
altres dies propers
```

i retornar:

```json
{
  "date": "2026-11-12",
  "start": "18:30",
  "occupancy_score": 52,
  "occupancy_level": "medium"
}
```

---

## 10.2 Frontend

SAFi pot mostrar:

```text
Millor dia alternatiu
Dijous · 18:30

[Canviar al dijous]
```

En tocar-lo:

```text
date = dijous
slot = 18:30
```

---

# 11. PRIORITAT 1 — Pantalla de Serveis

Crear una pantalla pròpia:

```text
Serveis
```

No limitar els serveis a la pantalla Reserva.

---

## 11.1 Cada targeta

Exemple:

```text
[imatge]

Fitness

Sala fitness i cardio

Previsió habitual
🟡 Mitjana

Horari
07:15 - 21:00

[Veure disponibilitat]
[Reservar]
```

---

## 11.2 Dades

Backend existent:

```text
GET /services
```

Pot ser necessari ampliar-lo amb:

```text
image
category
opening_hours
location
```

Només si aquestes dades existeixen o es poden definir de manera controlada.

No inventar horaris a partir de la previsió.

---

# 12. PRIORITAT 2 — Millorar navegació

La navegació actual és funcional però massa orientada a prototip.

Es recomana una navegació inferior:

```text
Inici
Serveis
SAFi
Mapa
Perfil / Reserves
```

Per l’MVP:

```text
Inici
Serveis
SAFi
Reserves
```

I quan el mapa estigui llest:

```text
Mapa
```

---

# 13. PRIORITAT 2 — Mapa del SAF

Aquesta funcionalitat s’ha de fer gairebé al final.

No abans de tenir:

- Heatmap correcte,
- Reserva integrada,
- tots els serveis,
- SAFi estable,
- cancel·lació correcta.

---

## 13.1 Versió recomanada

No cal un sistema GIS.

Pot ser:

- imatge/plànol del SAF,
- punts clicables,
- zones amb overlay.

En tocar un espai:

```text
Sala Fitness

Disponibilitat actual:
✓ Disponible

Previsió:
🟡 Mitjana

[VEURE DISPONIBILITAT]
[RESERVAR]
```

---

## 13.2 Backend

Només caldria ampliar els espais amb informació visual si és necessari:

```json
{
  "id": "...",
  "name": "...",
  "map_x": 0.43,
  "map_y": 0.61
}
```

o mantenir aquest mapatge al frontend si és només una imatge fixa de demo.

Per evitar complicar el backend, una primera versió pot mantenir les coordenades al frontend.

---

# 14. PRIORITAT 3 — Disseny visual final

Aquesta fase s’ha de fer després de tancar les funcionalitats principals, però no deixar-la per l’última hora.

---

## 14.1 Identitat visual

Canviar l’aspecte actual de prototip.

Direcció:

- verd com a color principal,
- logo SAF,
- fotografies reals de serveis,
- targetes,
- icones,
- botons menys genèrics,
- millor jerarquia tipogràfica,
- espais i marges coherents,
- cantonades i ombres subtils.

---

## 14.2 Home

La Home hauria de tenir:

```text
Logo SAF Hack

Hola 👋

[ RESERVAR ]

Disponibilitat aquesta setmana
mini heatmap

Serveis destacats
[Fitness] [Piscina] [Pàdel]

SAFi
"Quan vols venir?"

Navegació inferior
```

---

## 14.3 Reserva

Substituir llistes llargues de botons per:

- cards,
- chips,
- selectors horitzontals,
- mini calendaris,
- Heatmap,
- bottom sheet per confirmar.

---

## 14.4 Tipografia

Definir:

```text
Title
Heading
Body
Caption
Button
```

amb mides fixes.

Evitar tenir cada pantalla amb mides independents.

---

## 14.5 Localització

Mostrar de manera clara el nom de l’espai i, si aporta valor:

```text
SAF UAB
Edifici ...
Planta ...
```

Només si tenim dades reals.

---

# 15. PRIORITAT 3 — Funcionalitats que NO cal prioritzar ara

No bloquejar l’MVP per:

```text
login real
registre
perfil complet
preferències personals
notificacions push
ML avançat
predicció meteorològica
recomanacions personalitzades
```

Poden quedar com a futur.

---

# 16. Canvis recomanats al backend

## 16.1 Revisar `/services`

Objectiu:

```text
tots els serveis disponibles
space_id correcte
reservable correcte
sense duplicats
```

Tests:

- tots els serveis esperats apareixen,
- cap servei apunta a un `space_id` inexistent,
- no hi ha IDs duplicats.

---

## 16.2 Crear disponibilitat setmanal

Nou endpoint recomanat:

```text
GET /api/v1/availability/week
```

Query:

```text
space_id
from
to
```

Font:

```text
SQLite / reservations
```

No històric.

---

## 16.3 Mantenir previsió separada

Endpoint actual:

```text
GET /availability/heatmap
```

Font:

```text
historical_occupancy
```

Documentar explícitament:

```text
FORECAST / historical
```

---

## 16.4 Completar dies i franges absents

No eliminar del Heatmap:

- dies sense mostres,
- hores sense mostres.

Retornar:

```text
unknown
```

---

## 16.5 Cancel·lacions

`DELETE /reservations/{id}`

ha de:

```text
status = cancelled
```

`GET /reservations`

per l’app:

```text
només confirmed
```

El backend conserva les cancel·lades per administració i estadístiques.

---

## 16.6 SAFi multi-servei

Generalitzar:

```text
chat()
advice()
recommend()
```

perquè no depenguin principalment de Fitness.

---

## 16.7 Comparació entre dies

Afegir servei específic per comparar:

```text
space_id
hora
weekday
```

i trobar alternatives.

---

# 17. Canvis recomanats al frontend

## 17.1 `HeatmapScreen.tsx`

Canviar completament:

- dies → eix X,
- hores → eix Y,
- selector Disponibilitat / Previsió,
- canvi de setmana,
- tots els serveis,
- cel·les clicables,
- llegenda,
- empty state,
- scroll vertical i horitzontal controlat.

---

## 17.2 `ReservaScreen.tsx`

Afegir:

- mini Heatmap,
- selecció directa des de cel·la,
- distinció Disponibilitat / Previsió,
- recomanació descartable amb `✕`,
- recomanació d’un altre dia,
- menys botons verticals.

---

## 17.3 `MevesReservesScreen.tsx`

Canviar:

- refrescar en focus,
- cancel·lar,
- feedback immediat,
- reserva cancel·lada desapareix en tornar a entrar,
- no mostrar `cancelled` per defecte.

---

## 17.4 `HomeScreen.tsx`

Més endavant:

- mini heatmap,
- serveis destacats,
- CTA principal,
- SAFi,
- navegació inferior.

---

## 17.5 Nova `ServeisScreen.tsx`

Mostrar:

- tots els serveis,
- imatge,
- descripció,
- disponibilitat,
- previsió,
- reservar.

---

## 17.6 Nova `MapScreen.tsx`

Quasi al final.

---

# 18. Ordre de desenvolupament recomanat

## Fase A — Dades i Heatmap

```text
1. Revisar /services
2. Separar availability actual vs forecast
3. Crear availability/week
4. Completar dies/franges del forecast
5. Redissenyar HeatmapScreen
6. Eix X = dies
7. Eix Y = hores
8. Selector Disponibilitat / Previsió
```

Aquesta és la fase més important.

---

## Fase B — Reserva integrada

```text
9. Integrar mini Heatmap dins Reserva
10. Cel·la Heatmap → seleccionar dia/hora
11. SAFi descartable amb ✕
12. Diferenciar disponibilitat i previsió a cada slot
```

---

## Fase C — Reserves i SAFi

```text
13. Corregir cancel·lació visual
14. Refrescar Meves reserves en focus
15. No tornar a mostrar cancel·lades
16. SAFi multi-servei
17. Recomanar altres dies
```

---

## Fase D — Serveis

```text
18. Crear pantalla Serveis
19. Mostrar tots els serveis
20. Veure disponibilitat
21. Reservar directament
```

---

## Fase E — Quasi final

```text
22. Mapa SAF
23. Navegació inferior
24. Imatges
25. Logo
26. Identitat verda
27. Tipografia
28. Revisió UX
```

---

# 19. Criteris d’acceptació

## Heatmap

Ha de complir:

- tots els dies de la setmana visibles,
- dies a l’eix X,
- hores a l’eix Y,
- totes les franges vàlides,
- no confondre actual amb previsió,
- poder canviar de servei,
- poder tocar una cel·la,
- poder anar a reservar,
- mostrar unknown si falten dades.

---

## Reserva

Ha de complir:

- seleccionar servei,
- veure disponibilitat,
- veure previsió,
- seleccionar dia/hora,
- veure SAFi,
- poder tancar SAFi,
- poder acceptar alternativa,
- confirmar,
- persistir reserva.

---

## Cancel·lació

Ha de complir:

```text
cancel·lar
→ backend actualitzat
→ feedback
→ sortir de Meves reserves
→ tornar
→ la reserva no apareix
```

---

## Serveis

Ha de complir:

- tots els serveis reals visibles,
- reservables identificats,
- no reservables diferenciats,
- accés a disponibilitat,
- accés a reserva.

---

## SAFi

Ha de complir:

- Fitness,
- Piscina,
- Pàdel,
- Tennis,
- altres serveis amb dades,
- preguntes per dia,
- preguntes per hora,
- no inventar si no hi ha dades.

---

# 20. Prioritats finals

## P0 — Fer ara

```text
Disponibilitat actual vs previsió
Heatmap nou
dies eix X
hores eix Y
tots els dies
totes les franges
tots els serveis
Heatmap dins Reserva
Heatmap clicable
```

---

## P1 — Immediatament després

```text
recomanació descartable
cancel·lació correcta
SAFi multi-servei
recomanació d’altres dies
pantalla Serveis
```

---

## P2 — Quan el flux principal sigui estable

```text
navegació millor
serveis amb imatges
mapa SAF
```

---

## P3 — Acabat final

```text
logo
verd corporatiu
tipografia
cards
icones
espaiat
animacions subtils
poliment UX
```

---

# 21. Flux ideal final de l’app

```text
HOME
↓
RESERVAR
↓
SERVEI
↓
HEATMAP

[Disponibilitat] [Previsió SAFi]

      Dl  Dt  Dc  Dj  Dv
17:15 🟢  🟡  🟢  🟢  🟡
18:30 🔴  🔴  🟡  🟢  🔴
19:45 🟡  🟢  🟢  🟢  🟡

↓ tocar Dijous 18:30

DISPONIBILITAT
✓ Disponible
14 places

PREVISIÓ SAFi
🟢 baixa ocupació

↓
SAFi

"És una bona franja.
Dimarts a aquesta hora acostuma a estar més ple."

[✕]
[Confirmar reserva]

↓

RESERVA CREADA
```

Aquest és el flux que hauria de guiar totes les decisions de desenvolupament a partir d’ara.

---

# 22. Idea principal de producte

La diferenciació que ha de quedar clara tant a l’usuari com al jurat és:

```text
Disponibilitat actual
= què puc reservar ara

Previsió SAFi
= quan acostuma a ser millor anar
```

El Heatmap és la peça visual que uneix aquestes dues idees.

Per això la millora del Heatmap i la seva integració dins de Reserva són la prioritat funcional més important de la següent fase.
