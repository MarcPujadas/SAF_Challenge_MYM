# SAF Hack — Backend

Backend de **SAF Hack**, desenvolupat amb **Python, FastAPI i SQLite**.

El backend s'encarrega de:

- gestionar espais i serveis del SAF,
- consultar disponibilitat,
- crear i consultar reserves,
- validar conflictes i franges,
- guardar les reserves de l'aplicació a SQLite,
- processar les dades històriques proporcionades pel SAF,
- estimar l'ocupació habitual,
- buscar alternatives amb menys ocupació,
- proporcionar la base de dades i serveis necessaris per a SAFi i el panell d'administració.

---

# 1. Arquitectura

```text
APP MÒBIL
React Native + Expo
        |
        | HTTP / JSON
        v
FASTAPI BACKEND
        |
        +--------------------+
        |                    |
        v                    v
     SQLite            Dades històriques
                       SAF processades
        |                    |
        |                    v
        |             Historical Service
        |                    |
        +-----------> Recommendation Service
```

El frontend **mai accedeix directament** ni a SQLite ni als fitxers de dades.

FastAPI és la font de veritat del sistema.

---

# 2. Tecnologies

- Python 3.12
- FastAPI
- SQLite
- Pandas
- OpenPyXL
- Pytest
- Uvicorn

---

# 3. Estructura principal

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── database.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── historical_service.py
│       └── recommendation_service.py
│
├── scripts/
│   ├── import_spaces.py
│   ├── import_services.py
│   ├── process_historical_data.py
│   ├── build_resource_mapping.py
│   └── scripts d'anàlisi
│
├── tests/
│   └── test_core.py
│
├── data/
│   ├── local/
│   └── processed/
│
├── pytest.ini
├── requirements.txt
└── README.md
```

Les carpetes `data/local/` i `data/processed/` són locals i no s'han de publicar al repositori.

---

# 4. Dataset del SAF

Els importadors utilitzen aquests fitxers locals proporcionats per al repte:

```text
backend/data/local/saf-espais-2026-equips.xlsx
backend/data/local/historical_occupancy.csv
backend/data/local/guided_activity_sessions.csv
```

## Important

Les dades originals del SAF **no s'han de publicar al repositori públic**.

Tampoc es publiquen les dades processades derivades del dataset.

Aquestes rutes estan ignorades per Git.

---

# 5. Instal·lació

Des de la carpeta `backend/`:

```bash
python -m venv .venv
```

## Windows PowerShell

Activar l'entorn virtual:

```powershell
.venv\Scripts\Activate.ps1
```

Instal·lar dependències:

```powershell
pip install -r requirements.txt
```

---

# 6. Dependències

`requirements.txt`:

```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
pytest>=8,<9
httpx>=0.27,<1.0
pandas>=2.2,<3.0
openpyxl>=3.1,<4.0
```

---

# 7. Preparació inicial de les dades

Abans d'executar el backend per primera vegada, cal preparar els espais, serveis i dades històriques.

Totes les comandes següents s'executen des de:

```text
backend/
```

## 7.1 Importar espais

```powershell
python -m scripts.import_spaces
```

L'script llegeix:

```text
data/local/saf-espais-2026-equips.xlsx
```

concretament el full:

```text
Espais
```

El dataset conté 42 files, incloent 2 duplicats exactes.

Després d'eliminar-los s'importen:

```text
40 espais únics
```

Exemples:

```text
sala-fitnes-sala-cardio
pistes-de-padel-pista-1
tennis-tennis-1
piscina-25-metres-carrer-1
esquaix-esquaix-2
futbol-7-camp-1
```

---

# 8. Importar serveis

Executar:

```powershell
python -m scripts.import_services
```

Actualment es preparen els serveis principals de la demo:

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

Els serveis apunten als espais corresponents de SQLite.

Per exemple:

```text
Fitness
    ↓
sala-fitnes-sala-cardio
```

---

# 9. Processament de les dades històriques

Executar:

```powershell
python scripts/process_historical_data.py
```

El procés importa les reserves individuals del full:

```text
Reserves
```

del XLSX local. No importa també `Reserves per franja`, perquè és un resum
agregat de les mateixes reserves. Les activitats dirigides s'importen per
separat des de `data/local/guided_activity_sessions.csv`; el CSV històric
existent es manté com a font de compatibilitat per a les funcions antigues i
no se suma com una segona font de reserves.

Els recursos del SAF es normalitzen i es relacionen amb els `space_id` utilitzats pel nostre backend.

El mapping reusable separa normalització de text, registry d'alias,
jerarquia de recursos i estats `mapped`, `manual_review` i `ignored`.
Els registres amb recursos ambigus es conserven a `historical_usage` com a
`manual_review`; no es converteixen en scores fins que la relació es revisi.
El registry documenta la correcció de Pàdel Pista 2 i els vuit carrils de la
piscina de 25 m. No s'infereixen subdivisions de camps de futbol.

La projecció compatible generada es guarda a:

```text
backend/data/processed/historical_occupancy.csv
```

Aquest CSV manté les columnes antigues necessàries per les consultes per
`space_id` i afegeix procedència i camps de traçabilitat per als recursos
mapejats. Les files originals (incloses les pendents de revisió) s'importen
separadament a SQLite; no s'elimina ni es modifica el XLSX font. Els CSV/XLSX
locals no es publiquen al repositori.

---

# 10. Base de dades SQLite

La base de dades es crea automàticament a:

```text
backend/app/database/safhack.db
```

La base conté:

```text
users
spaces
services
service_spaces
data_sources
historical_usage
reservations
```

La base de dades local està ignorada per Git.

`services.space_id` es conserva com a recurs representatiu per compatibilitat
amb l'API actual. `service_spaces` manté el mapping complet servei → recursos:
capacitat de persones i unitats físiques es guarden per separat. El seed és
idempotent i s'executa en inicialitzar la base de dades i després d'importar
espais o serveis.

El mapping central és a `app/config/service_spaces.py`. Inclou vuit carrils
per a piscina de 25 m i quatre pistes de pàdel, tennis, esquaix i futbol quan
correspon. Pàdel Pista 2 es conserva com a recurs virtual si manca a SQLite,
perquè apareix al mapping de l'històric normalitzat; no es modifica el fitxer
font ni s'inventa capacitat de persones.

`data_sources` registra els imports SAF (`saf_reserves_2026` i
`saf_guided_activities_2026`) i les reserves operatives de l'aplicació
(`app_live`). `historical_usage` conserva cada fila d'origen amb el seu
checksum i número de fila, el nom raw, el volum de reserves, el mapping i el
`capacity_mode`. La clau de deduplicació és
`(source_id, source_checksum, source_record_key)`: reexecutar el mateix import
actualitza les mateixes files, mentre que una nova versió del fitxer es manté
com a versió històrica separada. `people_count`, `occupied_units` i
`occupancy_ratio` queden nuls quan no es poden justificar amb la semàntica de
la font. Les reserves de l'app continuen només a `reservations`.

Per executar l'informe de qualitat del mapping des de `backend/`:

```powershell
python -m scripts.validate_service_spaces
```

L'informe identifica mappings incomplets/invàlids, recursos duplicats,
recursos de base de dades o històric sense mapping i el cas especial de Pàdel
Pista 2. El script `python -m scripts.validate_data_integrity` també mostra
la cobertura per files i volum, els recursos `manual_review` i els gates
mínims de recursos. Aquests informes són per a revisió humana i no formen
part de l'arrencada de l'API.

## Usuari de demostració

S'inicialitza automàticament:

```text
id: demo-user
name: Usuari Demo
```

---

# 11. Executar el backend

Des de `backend/`:

```powershell
uvicorn app.main:app --reload
```

L'API estarà disponible a:

```text
http://127.0.0.1:8000
```

Documentació Swagger:

```text
http://127.0.0.1:8000/docs
```

---

# 12. Format de les respostes

Les respostes segueixen el contracte definit a `contracts.md`.

## Resposta correcta

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

## Error

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Readable error message"
  }
}
```

---

# 13. Endpoints del Backend Core

## Health

```text
GET /health
```

Permet comprovar que el backend està funcionant.

---

## Usuari actual

```text
GET /api/v1/users/me
```

Retorna l'usuari simulat de la demo.

---

## Espais

```text
GET /api/v1/spaces
```

Retorna els espais disponibles.

Exemple:

```json
{
  "id": "sala-fitnes-sala-cardio",
  "name": "Sala fitnes + sala cardio",
  "type": "fitness",
  "capacity": 120,
  "reservable": true
}
```

---

## Serveis

```text
GET /api/v1/services
```

Retorna els serveis que es poden mostrar a l'aplicació.

---

## Disponibilitat

```text
GET /api/v1/availability
```

Paràmetres:

```text
space_id
date
```

Exemple:

```text
/api/v1/availability?space_id=sala-fitnes-sala-cardio&date=2026-11-10
```

Cada franja retorna:

```json
{
  "start": "18:30",
  "end": "19:45",
  "available": true,
  "remaining_capacity": 119,
  "occupancy_level": "very_high",
  "occupancy_score": 100
}
```

Aquest endpoint combina dues fonts:

```text
SQLite
→ reserves creades des de l'aplicació

Dades històriques SAF
→ estimació de l'ocupació habitual
```

Per tant:

```text
available = true
```

no significa necessàriament que la franja acostumi a estar tranquil·la.

Una franja pot estar disponible però tenir:

```text
occupancy_level = very_high
```

---

# 14. Reserves

## Crear reserva

```text
POST /api/v1/reservations
```

Exemple:

```json
{
  "user_id": "demo-user",
  "space_id": "sala-fitnes-sala-cardio",
  "date": "2026-11-10",
  "start": "18:30",
  "end": "19:45"
}
```

El backend valida:

- que l'espai existeixi,
- que sigui reservable,
- que l'usuari existeixi,
- que la franja sigui vàlida,
- que l'usuari no tingui una altra reserva al mateix moment,
- que quedi capacitat disponible.

Les reserves confirmades es guarden realment a SQLite.

---

## Consultar reserves

```text
GET /api/v1/reservations?user_id=demo-user
```

Retorna les reserves de l'usuari.

---

# 15. Errors de reserva

Alguns errors possibles:

```text
INVALID_USER
INVALID_SPACE
INVALID_DATE
INVALID_TIME
RESERVATION_CONFLICT
SLOT_NOT_AVAILABLE
INVALID_REQUEST
```

Exemple:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_TIME",
    "message": "The requested time does not match a valid reservation slot."
  }
}
```

---

# 16. Fitness

Fitness té un tractament específic perquè les dades del SAF mostren torns reals.

## Dilluns a divendres

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

Cada torn dura:

```text
75 minuts
```

Exemple:

```text
18:30 → 19:45
```

## Dissabte

```text
08:00
09:30
11:00
12:30
14:00
15:30
17:00
18:30
```

## Diumenge

```text
09:30
11:00
12:30
```

Les hores anòmales trobades al dataset, com algunes reserves puntuals a `09:15`, `11:45`, `15:00` o `20:00`, no es consideren torns habituals.

---

# 17. Altres espais

Actualment Fitness és l'espai que disposa d'una normalització específica de torns.

Altres tipus d'espai com:

```text
Pàdel
Tennis
Piscina
Futbol
Esquaix
```

utilitzen temporalment una generació més genèrica de franges.

Aquesta simplificació és suficient per al MVP de la Hackathon.

Una futura versió podria incorporar regles específiques per cada activitat.

---

# 18. Ocupació històrica

El servei:

```text
app/services/historical_service.py
```

analitza l'històric agrupant principalment per:

```text
space_id
dia de la setmana
hora
```

Calcula:

```text
average_reservations
samples
occupancy_score
occupancy_level
```

---

# 19. Occupancy Score

`occupancy_score` és un índex de:

```text
0 → 100
```

utilitzat per comparar l'ocupació habitual entre franges del mateix espai.

## Important

No és necessàriament:

```text
percentatge d'aforament real
```

És un **índex relatiu basat en l'històric**.

La referència es calcula a partir de les dades observades de cada espai/dia.

---

# 20. Nivells d'ocupació

Els nivells són:

```text
low
medium
high
very_high
unknown
```

Actualment:

```text
0–34   → low
35–64  → medium
65–84  → high
85–100 → very_high
```

`unknown` s'utilitza quan no hi ha prou informació històrica.

---

# 21. Motor de recomanació

El servei:

```text
app/services/recommendation_service.py
```

utilitza l'ocupació històrica per comparar la franja demanada amb altres franges properes.

Exemple:

```text
18:30
occupancy_score: 100
very_high

↓

19:45
occupancy_score: 70
high
```

El sistema pot retornar:

```text
Les 19:45 acostumen a tenir menys ocupació que les 18:30.
```

---

# 22. Alternatives

Quan busca una alternativa:

- prioritza hores amb menys ocupació,
- intenta mantenir-se a prop de l'hora demanada,
- limita normalment la cerca a unes 3 hores de diferència.

Això evita recomanacions absurdes com:

```text
Usuari demana 18:00
→ recomanar 07:15
```

---

# 23. Confiança de la recomanació

La confiança depèn de la quantitat de mostres històriques disponibles.

```text
20 o més mostres → high
10–19            → medium
menys de 10      → low
```

La resposta també conserva la base de la recomanació:

```text
space_id
weekday
historical_period
```

El període històric utilitzat actualment és:

```text
2026-04-01 → 2026-10-31
```

---

# 24. SAFi

El Backend Core proporciona ja les dades i el servei de recomanació necessaris perquè SAFi pugui consultar informació fiable.

SAFi ha de seguir aquest principi:

```text
Backend / dades
       ↓
informació estructurada
       ↓
SAFi / LLM
       ↓
resposta a l'usuari
```

El LLM no ha d'inventar:

- ocupacions,
- aforaments,
- horaris,
- disponibilitat,
- reserves.

Si el backend no té prou dades, SAFi ha d'indicar que no ho sap.

Endpoints disponibles:

- `POST /api/v1/safi/advice`
- `POST /api/v1/safi/chat`
- `POST /api/v1/safi/chat-llm`
- `POST /api/v1/recommendations`

`/api/v1/safi/chat` continua sent el flux determinista i funciona sense cap
proveïdor LLM. `/api/v1/safi/chat-llm` utilitza Ornith només per redactar una
resposta a partir de dades consultades pels serveis interns compartits.
Disponibilitat actual, previsió històrica i reserves continuen sent fonts
separades; el model no pot crear ni cancel·lar reserves.

Per habilitar la integració, configura `UTH_KEY` a l'entorn del procés del
backend. La clau no s'ha d'incloure al codi, al repositori ni als logs. Si no
està configurada o Ornith no respon, `/safi/chat-llm` retorna
`LLM_UNAVAILABLE`; una resposta incompatible retorna `LLM_ERROR`.

---

# 25. Panell administrador

El panell administrador consumirà la mateixa API FastAPI.

Les funcionalitats administratives previstes inclouen:

- reserves totals,
- reserves creades per l'app,
- espais més utilitzats,
- hores amb més ocupació,
- hores amb menys ocupació,
- heatmaps,
- consulta de reserves.

Endpoints disponibles:

- `GET /api/v1/admin/summary`
- `GET /api/v1/admin/stats`
- `GET /api/v1/admin/reservations`
- `GET /api/v1/admin/occupancy`

`GET /api/v1/admin/stats` calcula `busiest_hour` i `quietest_hour` a partir
dels scores de l'històric processat. Si no hi ha dades històriques, aquests
camps retornen `null`.

`GET /api/v1/admin/occupancy` accepta els filtres opcionals `from`, `to` i
`space_id`. Per a cada espai retorna l'score mitjà, l'hora punta i l'hora amb
menys ocupació. Si se sol·licita un espai sense dades al període, les mètriques
retornen `null`.

## Heatmap històric

```text
GET /api/v1/availability/heatmap
```

Accepta els filtres opcionals `space_id`, `from` i `to`, i retorna dies amb
franges, `occupancy_score` i `occupancy_level` calculats des de les dades
històriques processades. Sense dades per als filtres indicats, `days` és una
llista buida.

Exemple:

```text
/api/v1/availability/heatmap?space_id=sala-fitnes-sala-cardio&from=2026-04-01&to=2026-04-30
```

---

# 26. Tests

Els tests del Backend Core estan a:

```text
backend/tests/test_core.py
```

Executar des de `backend/`:

```powershell
pytest -q
```

Resultat esperat actual:

```text
5 passed
```

Els tests comproven:

- serveis i disponibilitat,
- creació de reserves,
- consulta de reserves,
- rebuig de franges invàlides,
- conflictes entre reserves,
- capacitat màxima d'una franja.

Els tests utilitzen una SQLite temporal i no depenen del dataset privat del SAF.

---

# 27. Configuració de Pytest

`pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

Això evita que els scripts d'anàlisi siguin interpretats accidentalment com a tests.

---

# 28. Flux complet esperat

```text
Usuari obre l'app
        ↓
GET /services
        ↓
Selecciona Fitness
        ↓
GET /availability
        ↓
Backend consulta:
SQLite + històric SAF
        ↓
Usuari selecciona hora
        ↓
Recommendation Service
        ↓
SAFi mostra recomanació
        ↓
Usuari confirma
        ↓
POST /reservations
        ↓
Backend valida
        ↓
SQLite
        ↓
Reserva confirmada
```

---

# 29. Flux de desenvolupament

No treballar directament sobre:

```text
main
```

Branques principals:

```text
marc/backend-core
yassin/backend-safi-admin
marcos/frontend-app
hajar/frontend-ui
```

Abans de començar una sessió:

```bash
git checkout main
git pull origin main
git checkout <branca>
git merge main
```

Quan una funcionalitat estigui estable:

```bash
git add .
git commit -m "feat: descripcio del canvi"
git push origin <branca>
```

i crear una Pull Request cap a `main`.

---

# 30. Estat actual del Backend Core

Implementat:

```text
✓ FastAPI
✓ CORS
✓ SQLite
✓ Usuari demo
✓ Espais
✓ Serveis
✓ Importació del XLSX
✓ Reserves
✓ Persistència de reserves
✓ Validació d'usuari
✓ Validació d'espai
✓ Validació de franges
✓ Detecció de conflictes
✓ Control de capacitat
✓ Disponibilitat
✓ Torns reals de Fitness
✓ Processament històric
✓ Normalització de recursos SAF
✓ Occupancy score
✓ Occupancy level
✓ Recommendation service
✓ API de recomanacions
✓ Endpoints SAFi
✓ Endpoints d'administració
✓ Tests automatitzats
✓ Setup reproductible
```

Pendent:

```text
○ ampliar la cobertura d'espais i franges històriques específiques
```

Els endpoints de recomanacions, SAFi i administració utilitzen el Backend Core existent en lloc de crear una segona base de dades o un backend independent.

---

# 31. Limitacions conegudes

Per mantenir el projecte simple i demostrable durant la Hackathon:

- Fitness és l'activitat amb els torns més acuradament normalitzats.
- Altres espais utilitzen franges més genèriques.
- No hi ha login real.
- S'utilitza `demo-user`.
- No hi ha sistema avançat de permisos.
- No s'utilitza Machine Learning complex.
- El recomanador és estadístic i explicable.
- No totes les variants de recursos del dataset es poden relacionar amb seguretat.
- Els recursos amb correspondència ambigua es descarten.

Aquestes decisions són intencionades per prioritzar un MVP estable, demostrable i basat en dades reals.