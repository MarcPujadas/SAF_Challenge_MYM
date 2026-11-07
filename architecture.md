# SAF Hack - Architecture

## 1. Objectiu

SAF Hack és una aplicació mòbil per consultar la disponibilitat dels espais del SAF, fer reserves i rebre recomanacions basades en dades històriques d'ocupació.

El sistema també inclou:

- **SAFi**, un assistent que ajuda l'usuari durant la reserva i respon preguntes sobre ocupació, horaris i alternatives.
- **Panell web d'administració**, perquè el SAF pugui consultar ocupació, reserves i estadístiques.
- **Motor de recomanació**, que analitza les dades històriques i proposa hores o dies amb menys ocupació.

La prioritat de la Hackathon és tenir un sistema simple, demostrable i basat en dades reals.

---

## 2. Arquitectura general

```text
                    ┌───────────────────────┐
                    │      APP MÒBIL        │
                    │ React Native + Expo   │
                    │                       │
                    │ - Reserva             │
                    │ - Heatmap             │
                    │ - SAFi                │
                    │ - Serveis             │
                    │ - Mapa                │
                    └───────────┬───────────┘
                                │ HTTPS / JSON
                                ▼
                    ┌───────────────────────┐
                    │       BACKEND         │
                    │ Python + FastAPI      │
                    │                       │
                    │ - API                 │
                    │ - Reserves            │
                    │ - Usuaris             │
                    │ - SAFi                │
                    │ - Recomanacions       │
                    │ - Estadístiques       │
                    └───────┬───────┬───────┘
                            │       │
                 ┌──────────┘       └───────────┐
                 ▼                              ▼
        ┌─────────────────┐          ┌────────────────────┐
        │     SQLite      │          │ MOTOR DE DADES     │
        │                 │          │ Python / Pandas    │
        │ - Usuaris       │          │                    │
        │ - Reserves      │          │ - Ocupació         │
        │ - Espais        │          │ - Heatmaps         │
        │ - Serveis       │          │ - Recomanacions    │
        └─────────────────┘          └─────────┬──────────┘
                                              │
                                              ▼
                                    ┌────────────────────┐
                                    │ DADES SAF          │
                                    │                    │
                                    │ NO PUBLICAR        │
                                    │ AL REPOSITORI      │
                                    └────────────────────┘

                    ┌───────────────────────┐
                    │    WEB ADMIN SAF      │
                    │ React / Next.js       │
                    │                       │
                    │ - Estadístiques       │
                    │ - Heatmaps            │
                    │ - Reserves            │
                    │ - Espais              │
                    └───────────┬───────────┘
                                │ HTTPS / JSON
                                └──────► BACKEND
```

---

## 3. Tecnologies

### Aplicació mòbil

**React Native + Expo**

Motius:

- ràpid de desenvolupar,
- interfície moderna,
- una sola base de codi,
- fàcil de provar al mòbil,
- suficient per a la demo de la Hackathon.

### Backend

**Python + FastAPI**

Responsable de coordinar tot el sistema.

El frontend no accedeix directament ni a SQLite ni als fitxers de dades.

### Base de dades

**SQLite**

S'utilitza per guardar les dades creades per l'aplicació:

- usuaris,
- reserves,
- espais,
- serveis,
- procedència i ús històric SAF,
- configuració mínima.

Les reserves de la demo són reserves reals dins del nostre sistema i queden persistides a SQLite.

La relació actual `services.space_id` es manté com a espai representatiu per
compatibilitat. La taula `service_spaces` permet preparar la relació d'un
servei amb diversos recursos físics sense canviar encara els endpoints ni les
respostes existents. El mapping és centralitzat a
`backend/app/config/service_spaces.py`; la capacitat de persones no es confon
amb la capacitat d'unitats reservables. Pàdel Pista 2 es pot marcar com a
virtual quan falta a la taula `spaces`, sense modificar el dataset original.

Les dades històriques importades es mantenen separades de les reserves
operatives: `historical_usage` referencia `data_sources` i conserva el recurs
raw, el mapping i el checksum de la font. Les files no classificades es
conserven per a revisió; no es calculen counts de persones ni ocupació si la
semàntica de les dades no ho permet.

### Dades i recomanador

**Python + Pandas**

Les dades històriques del SAF s'han de processar abans d'utilitzar-les.

El recomanador no necessita Machine Learning complex per a la primera versió.

### Panell d'administració

**React / Next.js**

Aplicació web separada que consumeix la mateixa API del backend.

---

## 4. Components del backend

Proposta d'estructura:

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── reservations.py
│   │   ├── spaces.py
│   │   ├── availability.py
│   │   ├── recommendations.py
│   │   ├── safi.py
│   │   ├── users.py
│   │   └── admin.py
│   │
│   ├── services/
│   │   ├── reservation_service.py
│   │   ├── recommendation_service.py
│   │   ├── availability_service.py
│   │   └── safi_service.py
│   │
│   ├── models/
│   │   ├── reservation.py
│   │   ├── user.py
│   │   ├── space.py
│   │   └── service.py
│   │
│   ├── schemas/
│   │   └── ...
│   │
│   └── database/
│       ├── database.py
│       └── safhack.db
│
└── tests/
```

---

## 5. Flux d'una reserva

```text
Usuari
  │
  ▼
Selecciona servei
  │
  ▼
Selecciona dia
  │
  ▼
Backend consulta disponibilitat
  │
  ├──► SQLite: reserves actuals
  │
  └──► Recomanador: ocupació històrica
  │
  ▼
SAFi genera avís si és necessari
  │
  ▼
Usuari selecciona hora
  │
  ▼
Backend valida disponibilitat
  │
  ▼
Crea reserva a SQLite
  │
  ▼
Confirmació
```

SAFi no bloqueja una reserva només perquè una hora sigui molt popular.

Exemple:

> Aquesta franja acostuma a tenir una ocupació alta. Si pots, les 19:00 solen estar més tranquil·les.

L'usuari pot continuar igualment amb la seva selecció.

---

## 6. Motor de recomanació

### Primera versió

El recomanador utilitza dades històriques agrupades per:

- espai,
- activitat,
- dia de la setmana,
- hora,
- període o mes quan sigui útil.

Retorna una puntuació simple d'ocupació.

Exemple:

```text
Fitness - dimarts
17:00 -> alta
18:00 -> molt alta
19:00 -> mitjana
20:00 -> baixa
```

A partir d'això el sistema pot recomanar:

- una altra hora,
- un altre dia,
- una alternativa similar si existeix.

### No fer a la primera versió

- models predictius complexos,
- entrenament de xarxes neuronals,
- personalització avançada per usuari,
- prediccions que no es puguin justificar amb les dades disponibles.

---

## 7. Tractament obligatori de les dades

Les dades del SAF tenen limitacions conegudes. El sistema les ha de tractar abans de generar recomanacions.

### 7.1 Fitness

La sala fitness funciona amb torns de 75 minuts.

Les 10:00 i les 15:00 poden aparèixer amb molt poques reserves perquè corresponen a canvis de torn.

**No s'han de recomanar automàticament com a hores amb poca ocupació.**

### 7.2 Sales i piscines vs pistes

En sales i piscines una reserva pot representar una persona.

En pistes una reserva pot representar la pista sencera.

**No es poden comparar els números directament.**

Cada tipus d'espai ha de tenir la seva mètrica d'ocupació.

### 7.3 Recursos duplicats o dividits

Un mateix espai pot aparèixer amb recursos diferents segons:

- dia,
- hora,
- pista sencera,
- mitja pista,
- canvis com el pàdel a partir de les 18:30.

S'ha de crear una capa de normalització.

### 7.4 Noms diferents entre fitxers

Els noms dels espais no coincideixen sempre.

S'ha de mantenir una taula d'equivalències.

### 7.5 Reserves molt llargues

Les reserves de més de 4 hores poden correspondre a clubs o escoles.

No s'han de barrejar automàticament amb l'ús habitual de particulars.

### 7.6 Activitats duplicades

Exemples:

- `BODY PUMP (LES MILLS)`
- `BODY PUMP LES MILLS`

S'han de normalitzar abans de calcular estadístiques.

### 7.7 Sobrerreserves

Hi ha casos amb més inscrits que aforament.

Per visualització, l'ocupació es pot limitar al 100%, mantenint el valor original separat si cal analitzar-lo.

### 7.8 Efecte estacional

Agost té molt menys ús que octubre.

No s'ha de fer una mitjana global sense tenir en compte el període.

### 7.9 Sense identificadors d'usuari

Les dades històriques no permeten saber qui repeteix ni quantes persones diferents hi van.

SAFi no pot afirmar comportaments personals basant-se en aquest dataset.

---

## 8. SAFi

SAFi és l'assistent de l'aplicació.

Té dues funcions.

### Durant la reserva

Mostra avisos curts basats en dades.

Exemples:

> Aquesta hora acostuma a estar molt plena.

> Una hora més tard l'ocupació històrica és menor.

> Aquesta activitat acostuma a tenir més disponibilitat els divendres.

### Xat

L'usuari pot preguntar:

- Quan hi ha menys gent al fitness?
- Quina hora em recomanes demà?
- Quan és millor anar a piscina?
- Quines alternatives tinc a les 18:00?

### Arquitectura de SAFi

```text
Pregunta usuari
      │
      ▼
Backend
      │
      ▼
Consulta dades / recomanador
      │
      ▼
Context estructurat
      │
      ▼
LLM
      │
      ▼
Resposta SAFi
```

El LLM **no consulta directament els fitxers originals**.

El backend prepara primer les dades que necessita i després les passa al model.

SAFi ha de respondre "No ho sé" quan les dades no permetin respondre.

---

## 9. Aplicació mòbil

### Pantalla principal

Prioritat visual:

```text
┌─────────────────────────────┐
│          SAF Hack           │
│                             │
│      [ RESERVAR ]           │
│                             │
│ Disponibilitat              │
│                             │
│      HEATMAP                │
│                             │
│ ─────────────────────────── │
│ Serveis   SAFi   Mapa       │
└─────────────────────────────┘
```

### Pantalles mínimes

1. Inici.
2. Reserva.
3. Confirmació de reserva.
4. Heatmap / disponibilitat.
5. SAFi.
6. Serveis.

El mapa pot quedar com a extra si falta temps.

---

## 10. Panell web d'administració

El panell web serveix perquè el SAF pugui entendre què està passant.

### MVP

Mostrar:

- reserves totals,
- reserves per dia,
- reserves per hora,
- reserves per espai,
- heatmap general,
- franges amb alta ocupació,
- franges amb baixa ocupació.

### Extra

- filtrar per dates,
- comparar espais,
- comparar mesos,
- veure recomanacions que genera el sistema,
- detectar espais infrautilitzats,
- exportar dades.

---

## 11. Usuaris

### MVP

Es pot utilitzar un usuari de demo autenticat automàticament.

### Si hi ha temps

Afegir:

- registre,
- login,
- historial de reserves,
- cancel·lació de reserves.

La resta de l'arquitectura no ha de dependre de tenir autenticació real.

---

## 12. Privacitat i dades de la Hackathon

Les dades originals del SAF:

- són dades reals,
- no contenen dades personals,
- només es poden utilitzar per al repte,
- **no es poden pujar a cap repositori públic**,
- no es poden compartir fora de l'equip,
- no es pot intentar identificar ningú.

Per tant:

```text
data/raw/
data/processed/
*.xlsx
*.csv
```

han d'estar al `.gitignore` si contenen dades derivades que no es puguin publicar.

Al repositori només s'han de pujar:

- codi,
- estructures,
- exemples sintètics,
- documentació,
- scripts de processament sense les dades originals.

---

## 13. Principi general

Tot el sistema ha de seguir aquesta regla:

> El backend és l'única font de veritat.

El frontend mòbil i el panell web:

- no calculen ocupacions,
- no decideixen recomanacions,
- no accedeixen directament a la base de dades,
- només consumeixen l'API definida a `contracts.md`.

Això permet que quatre persones treballin en paral·lel sense trencar la integració.
