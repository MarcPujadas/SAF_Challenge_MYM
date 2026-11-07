# SAF Hack - Tasques de l'equip

## Objectiu immediat

Tenir un flux complet i demostrable:

```text
App -> consultar disponibilitat -> escollir franja -> SAFi recomana -> confirmar reserva -> SQLite -> panell administrador
```

Primer s'ha de completar aquest flux. Els extres només es fan quan el flux principal funciona.

---

# 1. Branques i manera de treballar

## Branca principal

La branca principal serà:

```text
main
```

`main` sempre ha d'estar estable. No s'hi programa directament.

## Branques de treball

Cada persona tindrà una branca principal pròpia:

```text
marc/backend-core
yassin/backend-safi-admin
marcos/frontend-app
hajar/frontend-ui
```

Per tasques grans o independents, es pot crear una subbranca a partir de la branca de la persona:

```text
marc/reservations-api
marc/sqlite-models

yassin/safi-api
yassin/admin-stats

marcos/reservation-flow
marcos/api-integration

hajar/home-screen
hajar/heatmap-ui
```

No crear branques diferents per canvis molt petits.

## Flux recomanat de Git

Abans de començar una sessió:

```bash
git checkout main
git pull origin main
git checkout <la-teva-branca>
git merge main
```

Treballar sempre dins la branca pròpia.

Quan una tasca estigui acabada:

```bash
git add .
git commit -m "feat: descripcio curta del canvi"
git push origin <la-teva-branca>
```

Després obrir una Pull Request cap a `main`.

## Regles de merge

- No fer `push` directe a `main`.
- No modificar fitxers d'una altra àrea sense avisar.
- Si es modifica un endpoint o un JSON, actualitzar `contracts.md` abans o al mateix PR.
- Si es modifica l'estructura del sistema, revisar `architecture.md`.
- Els agents d'IA han de respectar `agents.md`.
- Abans de fer merge, comprovar que l'aplicació arrenca i que no es trenca el flux principal.
- Si dues persones necessiten el mateix fitxer, acordar abans qui el modifica.

## Ordre recomanat d'integració

1. Backend core estable.
2. Recomanacions i SAFi.
3. Frontend connectat a l'API.
4. Dashboard administrador.
5. Millores visuals i extres.

---

# 2. Marc - Backend principal

**Branca principal**

```text
marc/backend-core
```

## Responsabilitat

Crear el nucli del backend FastAPI, SQLite i tot el sistema de reserves.

## Tasques prioritàries

- [ ] Crear l'estructura inicial de `backend/`.
- [ ] Configurar FastAPI i `main.py`.
- [ ] Afegir CORS perquè el frontend pugui connectar-se.
- [ ] Crear la connexió amb SQLite.
- [ ] Crear models mínims de base de dades:
  - [ ] User
  - [ ] Space
  - [ ] Service
  - [ ] Reservation
- [ ] Crear dades inicials d'espais i serveis per poder fer la demo.
- [ ] Crear `GET /api/v1/spaces`.
- [ ] Crear `GET /api/v1/services`.
- [ ] Crear `GET /api/v1/availability`.
- [ ] Crear `POST /api/v1/reservations`.
- [ ] Crear `GET /api/v1/reservations`.
- [ ] Validar que no es pugui crear una reserva impossible o incorrecta.
- [ ] Fer que les reserves quedin guardades realment a SQLite.
- [ ] Permetre començar amb `user_id = 1` com a usuari simulat.
- [ ] Preparar errors amb el format definit a `contracts.md`.

## Primera fita de Marc

Ha de funcionar això sense frontend:

```text
GET /services
GET /availability
POST /reservations
GET /reservations
```

I s'ha de poder comprovar des de `/docs` de FastAPI.

## No ha de fer encara

- Login complex.
- Sistema complet de permisos.
- Machine Learning.
- Lògica del LLM de SAFi.
- Disseny del panell administrador.

---

# 3. Yassin - Backend API SAFi, App i Administrador

**Branca principal**

```text
yassin/backend-safi-admin
```

## Responsabilitat

Crear les APIs de recomanació, SAFi i estadístiques per al panell administrador.

## Tasques prioritàries

### Recomanacions

- [ ] Crear `recommendation_service.py`.
- [ ] Definir una funció que rebi espai, dia i hora.
- [ ] Retornar ocupació esperada.
- [ ] Buscar una franja alternativa millor.
- [ ] Retornar el motiu de la recomanació.
- [ ] Retornar un nivell de confiança.
- [ ] Crear `POST /api/v1/recommendations`.
- [ ] Començar amb dades simulades si les dades processades encara no estan preparades.
- [ ] Substituir els mocks per les dades reals processades quan estiguin disponibles.

### SAFi

- [ ] Crear `safi_service.py`.
- [ ] Crear `POST /api/v1/safi/chat`.
- [ ] Fer que SAFi consulti primer les dades o serveis interns.
- [ ] Passar al LLM només dades ja preparades i fiables.
- [ ] Evitar que el LLM inventi ocupacions, horaris o aforaments.
- [ ] Si no hi ha dades suficients, SAFi ha de respondre que no ho sap.
- [ ] Preparar missatges curts de SAFi durant la reserva.

Exemple:

```text
Aquesta franja acostuma a tenir molta ocupació.
Si pots, les 19:00 solen estar més tranquil·les.
```

### Administrador

- [ ] Crear `GET /api/v1/admin/stats`.
- [ ] Crear `GET /api/v1/admin/reservations`.
- [ ] Crear `GET /api/v1/admin/occupancy`.
- [ ] Retornar dades útils per heatmaps i gràfics.
- [ ] Incloure estadístiques bàsiques:
  - [ ] reserves totals
  - [ ] espais més utilitzats
  - [ ] hores amb més ocupació
  - [ ] hores amb menys ocupació
  - [ ] reserves creades per l'app

## Primera fita de Yassin

Amb un request com:

```json
{
  "space_id": "fitness",
  "date": "2026-11-10",
  "preferred_start": "18:00",
  "preferred_end": "20:00"
}
```

l'API ha de ser capaç de respondre:

```text
18:00 -> ocupació alta
19:00 -> millor alternativa
```

Encara que al principi utilitzi mocks.

## Dependències

Yassin ha de coordinar-se amb Marc per no duplicar endpoints ni models.

Si necessita dades de reserves, les ha de consumir a través dels serveis/backend ja creats, no recrear una segona base de dades.

---

# 4. Marcos - Frontend principal

**Branca principal**

```text
marcos/frontend-app
```

## Responsabilitat

Construir el flux funcional de l'aplicació mòbil amb React Native + Expo i connectar-lo amb el backend.

## Tasques prioritàries

- [ ] Crear el projecte React Native + Expo.
- [ ] Crear navegació principal.
- [ ] Crear pantalla inicial.
- [ ] Afegir botó gran `RESERVAR`.
- [ ] Crear el flux de reserva:
  - [ ] seleccionar servei
  - [ ] seleccionar dia
  - [ ] seleccionar hora
  - [ ] veure recomanació SAFi
  - [ ] confirmar reserva
  - [ ] veure confirmació
- [ ] Crear client API centralitzat.
- [ ] Consumir `GET /services`.
- [ ] Consumir `GET /availability`.
- [ ] Consumir `POST /recommendations`.
- [ ] Consumir `POST /reservations`.
- [ ] Mostrar errors de backend de manera entenedora.
- [ ] Començar amb mocks que segueixin exactament `contracts.md` si el backend encara no està llest.
- [ ] Substituir els mocks per endpoints reals sense canviar la UI.

## Primera fita de Marcos

Ha de poder fer visualment aquest recorregut:

```text
Home
 -> Reservar
 -> Fitness
 -> Dimarts
 -> 18:00
 -> avís SAFi
 -> Confirmar
 -> Reserva creada
```

Encara que la primera versió utilitzi dades simulades.

## Fitxers que hauria de controlar

Principalment:

```text
frontend/src/screens/
frontend/src/navigation/
frontend/src/services/api/
frontend/src/state/
```

---

# 5. Hajar - Frontend UI, Heatmap i pantalles complementàries

**Branca principal**

```text
hajar/frontend-ui
```

## Responsabilitat

Construir els components visuals, el heatmap, SAFi i les pantalles que complementen el flux principal.

## Tasques prioritàries

### Home

- [ ] Dissenyar la pantalla principal.
- [ ] Botó gran `RESERVAR`.
- [ ] Zona de disponibilitat just a sota.
- [ ] Accessos a:
  - [ ] Serveis
  - [ ] SAFi
  - [ ] Mapa

### Heatmap

- [ ] Crear component de heatmap.
- [ ] Mostrar ocupació per dia i hora.
- [ ] Utilitzar nivells visuals simples:
  - [ ] baixa
  - [ ] mitjana
  - [ ] alta
  - [ ] molt alta
- [ ] Preparar el component perquè consumeixi `GET /availability/heatmap`.
- [ ] Permetre filtrar per espai o servei si hi ha temps.

### SAFi

- [ ] Crear interfície del xat SAFi.
- [ ] Crear component de notificació SAFi dins del procés de reserva.
- [ ] Diferenciar clarament recomanació de bloqueig: SAFi suggereix, però l'usuari decideix.
- [ ] Connectar la UI amb `POST /safi/chat` quan estigui disponible.

### Serveis

- [ ] Crear pantalla de serveis disponibles.
- [ ] Mostrar nom, informació bàsica i disponibilitat.
- [ ] Afegir botó per iniciar una reserva des d'un servei.

### Mapa

- [ ] Crear pantalla de mapa simple.
- [ ] Mostrar les principals instal·lacions/espais.
- [ ] Si no hi ha temps per un mapa interactiu real, utilitzar un esquema o imatge amb punts interactius.

## Primera fita de Hajar

Tenir la Home visualment completa amb:

```text
[ RESERVAR ]

Heatmap

Serveis | SAFi | Mapa
```

I tenir un component reutilitzable de notificació SAFi.

## Coordinació amb Marcos

Marcos controla principalment el flux i la integració funcional.

Hajar controla principalment els components visuals i les pantalles complementàries.

Per evitar conflictes:

- no editar tots dos la mateixa pantalla alhora,
- crear components separats,
- integrar-los després mitjançant una PR.

---

# 6. Tasques compartides

Aquestes tasques necessiten coordinació de tot l'equip.

## Contractes API

- [ ] Revisar `contracts.md` abans de programar cada integració.
- [ ] No inventar noms nous de camps al frontend.
- [ ] No canviar respostes del backend sense actualitzar el contracte.

## Dades

- [ ] No pujar els datasets reals del SAF al repositori públic.
- [ ] Afegir fitxers de dades a `.gitignore`.
- [ ] Treballar amb dades processades o agregades quan sigui possible.
- [ ] Guardar sempre la base de la recomanació: espai, dia, franja i període analitzat.

## Qualitat

- [ ] Provar el flux complet abans de fer cada merge important.
- [ ] Revisar que la demo no depengui d'una funcionalitat inacabada.
- [ ] Evitar refactors grans durant la Hackathon.
- [ ] Prioritzar coses que es puguin ensenyar en la presentació.

---

# 7. Ordre de feina recomanat

## Fase 1 - Treball en paral·lel

**Marc**

```text
FastAPI + SQLite + reservations
```

**Yassin**

```text
Recommendations mock + SAFi mock + admin endpoints
```

**Marcos**

```text
Navegació + flux complet de reserva amb mocks
```

**Hajar**

```text
Home + heatmap + components SAFi + serveis
```

## Fase 2 - Primera integració

Connectar:

```text
Frontend
   |
   v
FastAPI
   |
   +--> SQLite
   |
   +--> Recommendation Service
```

Objectiu:

```text
Reserva real creada des del mòbil
```

## Fase 3 - SAFi i dades

- Connectar recomanacions reals.
- Connectar SAFi.
- Connectar heatmap real.
- Comprovar que les explicacions corresponen a les dades.

## Fase 4 - Administrador

- Dashboard web.
- Estadístiques.
- Heatmap global.
- Reserves creades.

## Fase 5 - Extres

Només si tot l'anterior funciona:

- mapa interactiu,
- usuaris reals,
- login,
- notificacions,
- preferències personals,
- recomanacions d'activitats alternatives,
- millores visuals.

---

# 8. Definition of Done

Una tasca es considera acabada quan:

- [ ] Funciona.
- [ ] No trenca una funcionalitat existent.
- [ ] Respecta `architecture.md`.
- [ ] Respecta `contracts.md`.
- [ ] Respecta `agents.md`.
- [ ] No inclou datasets privats al repositori.
- [ ] Té un commit amb un missatge clar.
- [ ] Es pot revisar en una Pull Request.

---

# 9. MVP que tots hem de protegir

No sacrificar aquest flux per implementar extres:

```text
1. Obrir l'app
2. Veure disponibilitat
3. Prémer RESERVAR
4. Escollir servei, dia i hora
5. Rebre una recomanació de SAFi
6. Confirmar
7. Crear la reserva a SQLite
8. Veure-la al backend / administrador
```

Quan això funcioni de principi a fi, el projecte ja té una demo completa.
