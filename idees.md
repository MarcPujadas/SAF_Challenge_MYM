# SAF Hack - MVP, Idees i Repartiment

## 1. Objectiu del producte

Fer que reservar al SAF sigui fàcil i ajudar l'usuari a escollir el millor moment per anar-hi.

El projecte ha de demostrar dues coses:

1. **Utilitat per a l'usuari**: reserva fàcil i recomanacions útils.
2. **Utilitat per al SAF**: entendre millor l'ocupació dels seus espais.

La demo ha de prioritzar una experiència simple i visual.

---

# 2. Essencial per a la demo

## App mòbil

### 2.1 Pantalla inicial

Només obrir l'app:

```text
┌─────────────────────────────┐
│          SAF Hack           │
│                             │
│       [ RESERVAR ]          │
│                             │
│ Disponibilitat              │
│                             │
│         HEATMAP             │
│                             │
│ ─────────────────────────── │
│ Serveis   SAFi   Mapa       │
└─────────────────────────────┘
```

El botó **Reservar** és l'acció principal.

---

### 2.2 Reserva

Flux mínim:

```text
Servei / espai
      ↓
Dia
      ↓
Hora
      ↓
SAFi dona informació
      ↓
Confirmar
      ↓
Reserva creada
```

La reserva ha de quedar guardada a SQLite.

---

### 2.3 Heatmap

Mostrar de forma visual quan hi ha més o menys ocupació.

Exemple:

```text
🟢 baixa
🟡 mitjana
🔴 alta
```

Ha de permetre veure ràpidament quines franges poden ser millors.

---

### 2.4 Recomanador

Quan l'usuari selecciona una hora, comparar-la amb alternatives.

Exemple:

> Les 18:00 acostumen a tenir una ocupació alta.
>
> Si pots, les 19:00 solen estar més tranquil·les.

Primera versió basada en dades històriques, no en ML complex.

---

### 2.5 SAFi durant la reserva

SAFi apareix com una notificació o petit assistent.

No ha d'interrompre el flux.

Exemples:

> Aquesta franja acostuma a estar molt plena.

> Una hora més tard sol haver-hi menys ocupació.

> Els divendres aquesta activitat acostuma a tenir més disponibilitat.

---

### 2.6 SAFi Chat

Apartat específic de conversa.

Preguntes de demo:

- Quan hi ha menys gent al fitness?
- Quina hora em recomanes demà?
- Quan és millor anar a piscina?
- Hi ha alguna alternativa a les 18:00?

SAFi només respon amb informació que pugui justificar amb les dades.

---

# 3. Essencial per al SAF

## Web d'administració

Crear una web simple amb un dashboard.

### Mostrar com a mínim

- total de reserves,
- reserves d'avui,
- reserves per espai,
- reserves per hora,
- heatmap d'ocupació,
- hores amb més ocupació,
- hores amb menys ocupació.

L'objectiu és que el SAF pugui veure ràpidament:

> On tenim saturació?

> On tenim espais infrautilitzats?

---

# 4. Serveis disponibles

Afegir una pantalla amb els serveis i espais disponibles.

Cada element pot mostrar:

- nom,
- descripció curta,
- disponibilitat,
- horari,
- botó de reserva.

Aquesta pantalla és important, però està per sota de la reserva i del recomanador en prioritat.

---

# 5. Mapa

Mostrar els espais del SAF sobre un mapa o plànol simple.

Quan l'usuari toca un espai:

```text
Sala Fitness

Disponibilitat: mitjana
Horari: ...

[ RESERVAR ]
```

Si no hi ha temps per fer un mapa interactiu, utilitzar una imatge/plànol amb punts clicables o una llista visual.

---

# 6. Problemes de dades que hem de resoldre

Abans de fer recomanacions:

- normalitzar noms d'espais,
- normalitzar noms d'activitats,
- separar reserves de pista i reserves de persones,
- tractar els torns especials del fitness,
- evitar interpretar 10:00 i 15:00 com franges buides normals,
- detectar recursos que representen el mateix espai,
- separar reserves de més de 4 hores,
- gestionar sobrerreserves,
- comparar períodes similars,
- no fer personalització basada en persones perquè no tenim identificadors.

Aquesta part és essencial per al rigor del projecte.

---

# 7. Extres si sobra temps

## Usuari real

- registre,
- login,
- perfil,
- historial de reserves,
- cancel·lació.

Per l'MVP podem utilitzar un usuari de demo.

---

## Recomanar altres dies

Exemple:

```text
Dilluns       🔴
Dimarts       🟡
Dimecres      🔴
Dijous        🟢
Divendres     🟢
```

SAFi:

> Divendres acostuma a ser el millor dia per aquesta activitat.

---

## Recomanar activitats alternatives

Exemple:

> Fitness està molt ple ara mateix.
>
> La piscina té menys ocupació.

Només fer-ho si les dades permeten una comparació útil.

---

## Notificacions

Exemples:

> La teva reserva és en 30 minuts.

> La franja que havies consultat ara té més disponibilitat.

---

## Preferències personals

Si implementem usuaris reals:

- activitats preferides,
- dies preferits,
- franges habituals.

No confondre aquestes dades pròpies de SAF Hack amb les dades històriques del SAF, que no tenen identificadors d'usuari.

---

## Predicció avançada

Només si tot l'MVP ja funciona.

Possibles variables:

- dia de la setmana,
- hora,
- mes,
- tendència recent,
- tipus d'espai.

No és necessari per presentar una bona solució.

---

# 8. Prioritats

## P0 - Ha de funcionar

- Backend FastAPI arrancant.
- SQLite.
- Crear reserva.
- Consultar disponibilitat.
- Processament bàsic de dades.
- Recomanació d'una hora alternativa.
- App amb botó Reservar.
- Heatmap.
- SAFi mostrant un avís durant la reserva.
- Dashboard admin mínim.

## P1 - Molt recomanable

- SAFi Chat.
- Serveis disponibles.
- Llista de reserves de l'usuari.
- Filtres del dashboard.
- Millorar disseny visual.

## P2 - Si sobra temps

- Mapa interactiu.
- Login real.
- Cancel·lació de reserves.
- Activitats alternatives.
- Notificacions.
- Predicció avançada.

---

# 9. Repartiment entre quatre persones

## Persona 1 - Backend Core

Responsable de la base del servidor.

### Tasques inicials

- crear projecte FastAPI,
- configurar SQLite,
- models de base de dades,
- model `User`,
- model `Reservation`,
- model `Space`,
- endpoints `/spaces`,
- endpoints `/services`,
- endpoint `POST /reservations`,
- endpoint `GET /reservations`,
- validació de conflictes de reserva.

### Després

- autenticació si sobra temps,
- cancel·lació de reserva,
- tests del backend.

---

## Persona 2 - Backend Integració + Admin + SAFi

Responsable de connectar els diferents serveis del backend.

### Tasques inicials

- endpoint `/availability`,
- endpoint `/availability/heatmap`,
- integrar el servei de recomanacions de Persona 4,
- endpoint `/recommendations`,
- endpoint `/safi/advice`,
- preparar estructura `/safi/chat`,
- endpoints `/admin/summary`,
- `/admin/occupancy`,
- `/admin/reservations`.

### Després

- integrar LLM amb SAFi,
- preparar context perquè el LLM respongui només amb dades disponibles,
- millorar estadístiques d'administració.

---

## Persona 3 - Frontend

Responsable de l'app mòbil i, quan el flux principal funcioni, de la web admin.

### Tasques inicials app

- projecte React Native + Expo,
- navegació,
- pantalla principal,
- botó gran `Reservar`,
- flux de reserva,
- consum de `/spaces`,
- consum de `/availability`,
- consum de `/reservations`,
- component d'avís SAFi,
- heatmap visual.

### Quan la reserva funcioni

- pantalla SAFi Chat,
- pantalla serveis,
- millorar UX.

### Web admin

Fer una web senzilla amb:

- KPI cards,
- heatmap,
- gràfic de reserves per hora,
- espais més utilitzats.

No dedicar temps al dashboard abans que la reserva mòbil funcioni.

---

## Persona 4 - Dades + Recomanador

Responsable de convertir les dades del SAF en informació útil.

### Tasques inicials

- inspeccionar datasets,
- crear scripts de neteja,
- normalitzar espais,
- normalitzar activitats,
- detectar tipus d'espai,
- separar pistes de sales,
- tractar torns de fitness,
- separar reserves llargues,
- calcular ocupació històrica,
- generar estructura de dades processades.

### Recomanador

Crear una funció aproximada:

```python
recommend(space_id, date, preferred_time)
```

que retorni:

```text
ocupació hora seleccionada
millor alternativa
score
nivell d'ocupació
explicació curta
```

### Després

- heatmaps,
- comparació de dies,
- insights per al pitch,
- tres dades clau per a la pàgina final del SAF.

---

# 10. Ordre de treball recomanat

## Fase 1

Treball paral·lel:

```text
Persona 1 -> FastAPI + SQLite + reserves
Persona 2 -> endpoints availability/admin amb mocks
Persona 3 -> app mòbil amb dades mock
Persona 4 -> neteja i recomanador
```

Els mocks han de seguir `contracts.md`.

Això permet que ningú esperi els altres.

---

## Fase 2

Integració:

```text
Persona 4
   ↓
Recommendation Service
   ↓
Persona 2 Backend
   ↓
API
   ↓
Persona 3 Frontend
```

Persona 1 assegura que reserves i SQLite funcionen durant tota la integració.

---

## Fase 3

Quan el flux següent funcioni:

```text
obrir app
→ reservar
→ veure recomanació SAFi
→ confirmar
→ guardar a SQLite
→ veure reserva al dashboard admin
```

**NO afegir funcionalitats grans fins que aquest flux funcioni completament.**

---

# 11. Demo ideal

La demo de 3 minuts pot seguir aquest recorregut:

### 1. Problema

> Hi ha hores del SAF que se saturen i altres que queden buides.

### 2. Obrir SAF Hack

Mostrar botó gran de reserva i heatmap.

### 3. Fer una reserva

Seleccionar una hora amb ocupació alta.

### 4. SAFi intervé

> Aquesta hora acostuma a estar molt plena. Et recomano les 19:00.

### 5. Canviar l'hora

Reservar l'alternativa.

### 6. Dashboard

Mostrar que el SAF també pot veure els patrons d'ocupació.

### Missatge final

> SAF Hack ajuda l'usuari a trobar el millor moment per fer esport i ajuda el SAF a repartir millor l'ús de les seves instal·lacions.

---

# 12. Criteris de la Hackathon que hem de tenir presents

El projecte ha de prioritzar:

- utilitat per al SAF,
- rigor,
- originalitat,
- execució.

Cada dada o afirmació important de la presentació ha de poder explicar:

- de quin espai surt,
- de quin període,
- de quina franja,
- quina limitació té.

Per al lliurament necessitarem també:

- prototip o tauler,
- codi,
- presentació de 3 minuts,
- una pàgina per al SAF amb tres missatges, cadascun amb la seva xifra i el seu límit.

Aquesta última pàgina s'ha de preparar quan Persona 4 hagi extret els insights finals de les dades.
