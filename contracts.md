# SAF Hack - API Contracts

## 1. Objectiu

Aquest document defineix els contractes entre:

- aplicació mòbil,
- web pública,
- panell web d'administració,
- backend FastAPI.

Tots els equips han de respectar aquests formats.

**No canviar un contracte existent sense coordinar-ho amb la resta de l'equip.**

Base URL:

```text
/api/v1
```

Totes les respostes utilitzen JSON.

El backend és la font de veritat per a:

- disponibilitat,
- reserves,
- ocupació,
- recomanacions,
- SAFi,
- estadístiques,
- heatmaps.

Els frontends no han de recalcular aquesta informació.

---

# 2. Format general

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

# 3. Identificadors de servei i espai

És important diferenciar:

```text
service.id
```

de:

```text
service.space_id
```

Exemple:

```json
{
  "id": "fitness",
  "name": "Fitness",
  "space_id": "sala-fitnes-sala-cardio"
}
```

`fitness` identifica el servei visible per l'usuari.

`sala-fitnes-sala-cardio` identifica l'espai real utilitzat pel backend.

Les peticions antigues poden continuar utilitzant `space_id`. Les
operacions agregades noves utilitzen `service_id`; quan hi ha una reserva
concreta, el backend conserva també el `space_id` del subespai assignat.

No s'ha d'utilitzar `service.space_id` per agregar un servei.

---

# 4. Espais i serveis

## GET /spaces

Retorna els espais disponibles.

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "sala-fitnes-sala-cardio",
      "name": "Sala fitnes + sala cardio",
      "type": "fitness",
      "capacity": 120,
      "reservable": true
    }
  ],
  "error": null
}
```

---

## GET /services

Retorna els serveis que es mostren a l'aplicació.
La resposta inclou els vuit serveis configurats pel backend:
`fitness`, `pool-25m`, `pool-16m`, `padel`, `tennis`, `squash`,
`football` i `guided-activities`. Cada servei té un `id` únic i un
`space_id` representatiu per compatibilitat. `reservable` és `true`
només quan el servei té recursos reservables. La resposta afegeix
`resource_count` i `capacity_mode` (`unit` o `people`) dels recursos
actius.

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "fitness",
      "name": "Fitness",
      "description": "Sala de fitness i cardio",
      "space_id": "sala-fitnes-sala-cardio",
      "reservable": true,
      "resource_count": 1,
      "capacity_mode": "people"
    },
    {
      "id": "pool-25m",
      "name": "Piscina 25 m",
      "description": "Piscina de 25 metres",
      "space_id": "piscina-25-metres-carrer-1",
      "reservable": true
    },
    {
      "id": "pool-16m",
      "name": "Piscina 16 m",
      "description": "Piscina de 16 metres",
      "space_id": "piscina-de-16-metres",
      "reservable": true
    },
    {
      "id": "padel",
      "name": "Pàdel",
      "description": "Pistes de pàdel",
      "space_id": "pistes-de-padel-pista-1",
      "reservable": true
    },
    {
      "id": "tennis",
      "name": "Tennis",
      "description": "Pistes de tennis",
      "space_id": "tennis-tennis-1",
      "reservable": true
    },
    {
      "id": "squash",
      "name": "Esquaix",
      "description": "Pistes d'esquaix",
      "space_id": "esquaix-esquaix-2",
      "reservable": true
    },
    {
      "id": "football",
      "name": "Futbol",
      "description": "Camps de futbol",
      "space_id": "futbol-7-camp-1",
      "reservable": true
    },
    {
      "id": "guided-activities",
      "name": "Activitats dirigides",
      "description": "Sales d'activitats dirigides",
      "space_id": "sales-activitats-dirigides-sala-1",
      "reservable": true
    }
  ],
  "error": null
}
```

---

## GET /services/{service_id}/spaces

Retorna els subespais actius i les seves capacitats configurades. Un recurs
amb mapping virtual només és reservable quan la inicialització ha creat el
seu espai operatiu; `is_virtual: true` conserva la traçabilitat que la seva
identitat prové del mapping SAF i no d'una fila del full d'espais.
Pàdel Pista 2 i les dues meitats documentades del Camp 4 utilitzen aquesta
representació d'una unitat reservable.

```json
{
  "success": true,
  "data": [
    {
      "service_id": "tennis",
      "space_id": "tennis-tennis-1",
      "resource_label": "Pista 1",
      "person_capacity": null,
      "reservation_capacity": 1,
      "capacity_mode": "resource_units",
      "is_active": true,
      "is_virtual": false,
      "reservable": true
    }
  ],
  "error": null
}
```

# 5. Disponibilitat

## GET /availability

Consulta les franges disponibles d'un espai per a una data.

### Query parameters

```text
space_id=sala-fitnes-sala-cardio
date=2026-11-10
```

### Response

```json
{
  "success": true,
  "data": {
    "space_id": "sala-fitnes-sala-cardio",
    "date": "2026-11-10",
    "slots": [
      {
        "start": "18:30",
        "end": "19:45",
        "available": true,
        "remaining_capacity": 30,
        "occupancy_level": "high",
        "occupancy_score": 82
      },
      {
        "start": "19:45",
        "end": "21:00",
        "available": true,
        "remaining_capacity": 64,
        "occupancy_level": "medium",
        "occupancy_score": 51
      }
    ]
  },
  "error": null
}
```

### occupancy_level

Valors possibles:

```text
low
medium
high
very_high
unknown
```

### occupancy_score

Quan existeixen dades:

```text
0 - 100
```

Quan no existeixen dades suficients:

```json
{
  "occupancy_score": null,
  "occupancy_level": "unknown"
}
```

`available` i `remaining_capacity` representen disponibilitat actual
calculada des de SQLite, les reserves confirmades i la capacitat de
l'espai. `occupancy_score` i `occupancy_level` són una previsió basada
en l'històric processat; no determinen la disponibilitat de reserva.

### Errors possibles

```text
INVALID_DATE
INVALID_SPACE
```

## GET /availability/week

Consulta la disponibilitat actual de totes les franges vàlides dels dies
inclosos, ambdós inclusivament. Només utilitza espais, capacitat i
reserves confirmades de SQLite; no inclou cap mètrica històrica.

### Query parameters

```text
space_id=tennis-tennis-1
from=2026-11-09
to=2026-11-15
```

### Response

```json
{
  "success": true,
  "data": {
    "space_id": "tennis-tennis-1",
    "from": "2026-11-09",
    "to": "2026-11-15",
    "days": [
      {
        "date": "2026-11-09",
        "slots": [
          {
            "start": "07:15",
            "end": "08:30",
            "available": true,
            "remaining_capacity": 1
          }
        ]
      }
    ]
  },
  "error": null
}
```

Cada dia inclou totes les franges vàlides encara que no hi hagi reserves.
Una franja sense reserves retorna la capacitat completa de l'espai.
Les franges completes retornen `available: false` i
`remaining_capacity: 0`.

### Errors possibles

```text
INVALID_DATE
INVALID_DATE_RANGE
INVALID_SPACE
```

---

## GET /services/{service_id}/availability/week

Calcula disponibilitat actual des de SQLite, les reserves confirmades i
les capacitats dels subespais associats; no consulta l'històric.

### Query parameters

```text
from=2026-11-09
to=2026-11-15
```

La resposta inclou `capacity_mode`. Per a `unit`, cada slot inclou
`available_units` i `total_units`; per a `people`, aquests dos camps són
`null` i s'inclou `remaining_people_capacity`. `spaces` detalla la
disponibilitat dels subespais que admeten el slot.

```json
{
  "success": true,
  "data": {
    "service_id": "tennis",
    "from": "2026-11-10",
    "to": "2026-11-10",
    "capacity_mode": "unit",
    "days": [
      {
        "date": "2026-11-10",
        "slots": [
          {
            "start": "18:30",
            "end": "19:45",
            "available": true,
            "capacity_mode": "unit",
            "available_units": 3,
            "total_units": 5,
            "remaining_people_capacity": null,
            "spaces": [
              {"space_id": "tennis-tennis-1", "available": false},
              {"space_id": "tennis-tennis-2", "available": true}
            ]
          }
        ]
      }
    ]
  },
  "error": null
}
```

# 6. Heatmap d'ocupació

## GET /availability/heatmap

Retorna ocupació històrica processada per dies i franges.

### Query parameters

```text
space_id=sala-fitnes-sala-cardio
from=2026-04-01
to=2026-04-30
```

Es pot enviar `service_id` en lloc de `space_id`, però no tots dos alhora.
El heatmap per servei només agrega serveis amb forecast validat; els altres
retornen `occupancy_score: null`, `occupancy_level: "unknown"` i
`unavailable_reason: "aggregated_forecast_not_validated"`. No s'utilitza
cap subespai com a proxy. Les respostes de servei també inclouen
`occupancy_ratio` quan existeix, `samples` i la font històrica. Fitness pot
utilitzar `historical_occupancy.csv` quan no hi ha mètriques de persones
vàlides a `historical_usage`; en aquest cas manté l'índex històric relatiu,
`occupancy_ratio` és `null` i `source` identifica `historical_occupancy.csv`.

Els filtres permeten limitar les dades per espai i període. `from` i
`to` són inclusius; si s'omet un dels dos, es consulta només la data
indicada. Si s'ometen tots dos, es retornen les dates disponibles a
l'històric. La resposta inclou tots els dies del rang.

Fitness utilitza les seves franges conegudes. Per als altres espais només
es retornen franges presents en el seu històric, incloses les franges
vàlides que no tinguin una mostra per al dia consultat. En aquest últim
cas, `occupancy_score` és `null` i `occupancy_level` és `"unknown"`.
Cada valor es basa en mostres històriques comparables del mateix dia de
la setmana, espai i hora, no en reserves creades per l'aplicació per a la
data futura consultada. Si s'omet `space_id`, el score d'una hora
combina els espais amb mostres disponibles per a aquell dia de la setmana.

### Response

```json
{
  "success": true,
  "data": {
    "space_id": "sala-fitnes-sala-cardio",
    "days": [
      {
        "date": "2026-04-07",
        "slots": [
          {
            "hour": "09:45",
            "occupancy_score": 31,
            "occupancy_level": "low"
          },
          {
            "hour": "18:30",
            "occupancy_score": 91,
            "occupancy_level": "very_high"
          }
        ]
      }
    ]
  },
  "error": null
}
```

### Heatmap per servei

```json
{
  "success": true,
  "data": {
    "service_id": "fitness",
    "aggregate": true,
    "source": "historical_usage",
    "occupancy_ratio_available": true,
    "days": [
      {
        "date": "2026-04-07",
        "slots": [
          {
            "hour": "18:30",
            "occupancy_score": 60,
            "occupancy_level": "medium",
            "occupancy_ratio": 0.6,
            "samples": 2
          }
        ]
      }
    ]
  },
  "error": null
}
```

### Sense dades

Si no hi ha espais ni franges conegudes en l'històric, es retornen tots
els dies demanats amb `slots: []`. Les franges conegudes sense mostres
per a un dia es retornen amb score `null` i nivell `"unknown"`.

```json
{
  "success": true,
  "data": {
    "space_id": "sala-fitnes-sala-cardio",
    "days": [
      {
        "date": "2026-11-10",
        "slots": [
          {
            "hour": "18:30",
            "occupancy_score": null,
            "occupancy_level": "unknown"
          }
        ]
      }
    ]
  },
  "error": null
}
```

### Errors possibles

Data incorrecta:

```text
INVALID_DATE
```

Rang invertit:

```text
INVALID_DATE_RANGE
```

---

# 7. Recomanacions

## POST /recommendations

Demana al backend una recomanació de franja basada en l'ocupació històrica.

La recomanació queda registrada al backend perquè posteriorment es pugui saber si l'usuari l'ha acceptat o ignorat. El payload antic amb `space_id`
es manté; el payload agregat pot enviar `service_id` en lloc de `space_id`.

Els espais amb `spaces.type == "court"` (pàdel, tennis, esquaix, futbol i altres pistes equivalents) no reben recomanacions SAFi d'ocupació. En aquests casos l'endpoint respon HTTP 200 amb:

```json
{
  "recommendation_id": null,
  "recommended_slot": null,
  "recommendation_available": false,
  "unavailable_reason": "unsupported_space_type"
}
```

No es desa cap recomanació a SQLite. La disponibilitat i les reserves d'aquests espais continuen funcionant normalment.

Per al MVP, l'usuari associat és:

```text
demo-user
```

### Request

```json
{
  "service_id": "fitness",
  "date": "2026-11-10",
  "preferred_start": "18:30",
  "preferred_end": "19:45"
}
```

Les pistes i els serveis sense forecast agregat validat retornen score
`null`, nivell `unknown`, `recommendation_available: false` i no desen
cap recomanació.

### Payload antic per espai

```json
{
  "space_id": "sala-fitnes-sala-cardio",
  "date": "2026-11-10",
  "preferred_start": "18:30",
  "preferred_end": "19:45"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "recommendation_id": "rec_ab12cd34ef56",
    "requested_slot": {
      "start": "18:30",
      "occupancy_score": 89,
      "occupancy_level": "very_high"
    },
    "recommended_slot": {
      "start": "19:45",
      "occupancy_score": 52,
      "occupancy_level": "medium"
    },
    "message": "Les 19:45 acostumen a tenir menys ocupació que les 18:30.",
    "confidence": "medium",
    "basis": {
      "service_id": "fitness",
      "weekday": "Tuesday",
      "historical_period": "2026-04-01 to 2026-10-31"
    }
  },
  "error": null
}
```

Si no existeix una alternativa millor:

```json
{
  "recommended_slot": null
}
```

### confidence

Valors possibles:

```text
low
medium
high
```

El backend no ha de retornar `high` si les dades són insuficients o poc comparables.

### Errors possibles

```text
INVALID_TIME
INVALID_SPACE
INVALID_USER
OCCUPANCY_DATA_UNAVAILABLE
```

---

# 8. Registrar decisió sobre una recomanació

## POST /recommendations/{recommendation_id}/action

Registra si l'usuari ha seguit o ignorat una recomanació de SAFi.

Aquesta informació permet mesurar:

- percentatge de recomanacions acceptades,
- canvi de franja provocat per SAFi,
- redistribució potencial de demanda.

### Request

```json
{
  "action": "accepted"
}
```

Valors possibles:

```text
accepted
ignored
```

### Response

```json
{
  "success": true,
  "data": {
    "recommendation_id": "rec_ab12cd34ef56",
    "action": "accepted"
  },
  "error": null
}
```

Només es guarda una decisió per recomanació.

Si es torna a enviar una acció per la mateixa recomanació, es conserva l'última decisió.

### Errors possibles

```text
INVALID_RECOMMENDATION_ACTION
RECOMMENDATION_NOT_FOUND
```

---

# 9. Crear reserva

## POST /reservations

Crea una reserva real i la guarda a SQLite. El payload antic basat en
`space_id` continua suportat. Amb `service_id` i `space_id: null`, el
backend assigna el primer subespai disponible amb ordre estable. Si
s'envien tots dos, valida que el subespai pertanyi al servei.

Al futbol, `futbol-7-camp-4` entra en conflicte amb
`futbol-7-camp-4-1` i `futbol-7-camp-4-2`: reservar el camp complet impedeix
reservar qualsevol meitat, mentre que reservar una meitat permet reservar
l'altra. Les dues meitats també entren en conflicte amb el camp complet.

### Request

```json
{
  "user_id": "demo-user",
  "service_id": "tennis",
  "space_id": null,
  "participants_count": null,
  "date": "2026-11-10",
  "start": "18:30",
  "end": "19:45"
}
```

### Payload antic per espai

```json
{
  "user_id": "demo-user",
  "space_id": "sala-fitnes-sala-cardio",
  "date": "2026-11-10",
  "start": "19:45",
  "end": "21:00"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "reservation_id": "res_12345",
    "status": "confirmed",
    "user_id": "demo-user",
    "service_id": "tennis",
    "space_id": "tennis-tennis-1",
    "space_name": "Pista 1",
    "participants_count": null,
    "date": "2026-11-10",
    "start": "19:45",
    "end": "21:00"
  },
  "error": null
}
```

### Errors possibles

```text
SLOT_NOT_AVAILABLE
INVALID_SPACE
INVALID_USER
INVALID_DATE
INVALID_TIME
RESERVATION_CONFLICT
```

---

# 10. Consultar reserves

## GET /reservations

Per defecte només retorna reserves confirmades. Per consultar l'historial complet,
incloses les cancel·lades, es pot enviar `include_cancelled=true`.

### Query parameters

```text
user_id=demo-user
```

Només retorna reserves amb `status: "confirmed"`. Les cancel·lades es
conserven al sistema amb `status: "cancelled"` però no formen part de la
llista de reserves actives.

### Response

```json
{
  "success": true,
  "data": [
    {
      "reservation_id": "res_12345",
      "space_id": "sala-fitnes-sala-cardio",
      "space_name": "Sala fitnes + sala cardio",
      "date": "2026-11-10",
      "start": "19:45",
      "end": "21:00",
      "status": "confirmed"
    }
  ],
  "error": null
}
```

---

# 11. Cancel·lar reserva

## DELETE /reservations/{reservation_id}

### Response

```json
{
  "success": true,
  "data": {
    "reservation_id": "res_12345",
    "status": "cancelled"
  },
  "error": null
}
```

### Errors possibles

```text
RESERVATION_NOT_FOUND
RESERVATION_ALREADY_CANCELLED
```

---

# 12. SAFi durant la reserva

## POST /safi/advice

Retorna un missatge curt basat en dades per mostrar durant el procés de reserva.

No necessita utilitzar un LLM.

### Request

```json
{
  "service_id": "fitness",
  "date": "2026-11-10",
  "start": "18:30"
}
```

També s'accepta el payload antic amb `space_id`. No es poden enviar tots
dos identificadors alhora. Els serveis sense forecast validat retornen
`occupancy_score: null` i una resposta equivalent a «No ho sé amb les
dades disponibles».

### Payload antic per espai

```json
{
  "space_id": "sala-fitnes-sala-cardio",
  "date": "2026-11-10",
  "start": "18:30"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "type": "warning",
    "message": "A les 18:30 de dimarts l'ocupació acostuma a ser alta.",
    "alternative": {
      "start": "19:45",
      "message": "Les 19:45 solen estar més tranquil·les."
    },
    "occupancy_score": 89
  },
  "error": null
}
```

Si no existeix una alternativa millor:

```json
{
  "alternative": null
}
```

Si no existeixen dades suficients:

```json
{
  "success": true,
  "data": {
    "type": "info",
    "message": "No ho sé amb les dades disponibles.",
    "alternative": null,
    "occupancy_score": null
  },
  "error": null
}
```

### type

```text
info
recommendation
warning
```

---

# 13. SAFi Chat

## POST /safi/chat

### Request

```json
{
  "user_id": "demo-user",
  "message": "Quan hi ha menys gent al fitness demà?"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "message": "Segons les dades disponibles, les 19:45 tenen menys ocupació prevista.",
    "sources": [
      {
        "type": "historical_occupancy",
        "service_id": "fitness",
        "date_reference": "dimarts"
      }
    ],
    "can_answer": true
  },
  "error": null
}
```

Si no existeixen dades suficients:

```json
{
  "success": true,
  "data": {
    "message": "No ho sé amb les dades disponibles.",
    "sources": [],
    "can_answer": false
  },
  "error": null
}
```

SAFi no ha d'inventar informació quan les dades disponibles no permetin respondre.

## POST /safi/chat-llm

Utilitza Ornith per redactar una resposta a partir de tools internes del backend.
Les tools només poden consultar previsió històrica, disponibilitat actual o
reserves confirmades de l'usuari indicat al request. L'identificador d'usuari
no es rep mai del model. Aquest endpoint no crea ni cancel·la reserves.
Les tools consulten per `service_id` mitjançant
`get_service_occupancy_forecast`, `get_service_booking_availability` i
`get_user_reservations`; no resolen el servei a un `services.space_id`
representatiu. La previsió només usa `historical_usage`; la disponibilitat
només usa SQLite i reserves confirmades.

### Request

Mateix cos que `POST /safi/chat`:

```json
{
  "user_id": "demo-user",
  "message": "Quina ocupació històrica hi ha al fitness demà a les 18:30?"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "message": "La previsió històrica indica una ocupació molt alta.",
    "sources": [
      {
        "type": "historical_occupancy",
        "space_id": "sala-fitnes-sala-cardio"
      }
    ],
    "can_answer": true,
    "provider": "uab-ornith"
  },
  "error": null
}
```

Si no es consulta cap dada utilitzable, la resposta segueix el contracte de
SAFi sense dades: `can_answer` és `false`, `sources` és `[]` i el missatge és
equivalent a "No ho sé amb les dades disponibles."

Errors:

- `LLM_UNAVAILABLE` (`503`): Ornith no està configurat, falla o supera el timeout.
- `LLM_ERROR` (`502`): Ornith retorna una resposta incompatible amb el protocol.

La clau d'Ornith s'ha de configurar al servidor mitjançant `UTH_KEY`; no forma
part del request ni de la resposta.

---

# 14. Usuari actual

## GET /users/me

Per al MVP retorna l'usuari de demo.

### Response

```json
{
  "success": true,
  "data": {
    "id": "demo-user",
    "name": "Usuari Demo"
  },
  "error": null
}
```

Això permet afegir autenticació real més endavant sense modificar la resta del frontend.

---

# 15. API d'administració

Tots els endpoints d'administració utilitzen:

```text
/api/v1/admin/...
```

---

## GET /admin/summary

Retorna un resum de les reserves generades pel sistema.

### Response

```json
{
  "success": true,
  "data": {
    "total_reservations": 71,
    "reservations_today": 5,
    "busiest_space": {
      "id": "sala-fitnes-sala-cardio",
      "name": "Sala Fitness"
    },
    "busiest_hour": "18:30"
  },
  "error": null
}
```

Si no existeixen reserves:

```json
{
  "success": true,
  "data": {
    "total_reservations": 0,
    "reservations_today": 0,
    "busiest_space": null,
    "busiest_hour": null
  },
  "error": null
}
```

---

## GET /admin/stats

Retorna estadístiques de les reserves creades a l'aplicació i hores calculades a partir de l'ocupació històrica processada.

Les hores punta i tranquil·les **no s'han d'inferir a partir del nombre de reserves creades per l'app**.

### Response

```json
{
  "success": true,
  "data": {
    "total_reservations": 71,
    "reservations_created_by_app": 71,
    "most_used_spaces": [
      {
        "space_id": "sala-fitnes-sala-cardio",
        "name": "Sala Fitness",
        "total_reservations": 52
      }
    ],
    "busiest_hour": "18:30",
    "quietest_hour": "09:45"
  },
  "error": null
}
```

Si no existeixen dades històriques suficients:

```json
{
  "busiest_hour": null,
  "quietest_hour": null
}
```

---

## GET /admin/occupancy

Retorna mètriques d'ocupació calculades a partir de les dades històriques processades.

### Query parameters

```text
from=2026-04-01
to=2026-04-30
space_id=sala-fitnes-sala-cardio
```

Els filtres són opcionals.

### Response

```json
{
  "success": true,
  "data": {
    "period": {
      "from": "2026-04-01",
      "to": "2026-04-30"
    },
    "spaces": [
      {
        "space_id": "sala-fitnes-sala-cardio",
        "average_occupancy_score": 67,
        "peak_hour": "18:30",
        "lowest_hour": "09:45"
      }
    ]
  },
  "error": null
}
```

### Espai sol·licitat sense dades

Quan es demana explícitament un espai però no existeixen dades per al període:

```json
{
  "success": true,
  "data": {
    "period": {
      "from": "2026-04-01",
      "to": "2026-04-30"
    },
    "spaces": [
      {
        "space_id": "sala-fitnes-sala-cardio",
        "average_occupancy_score": null,
        "peak_hour": null,
        "lowest_hour": null
      }
    ]
  },
  "error": null
}
```

### Errors possibles

```text
INVALID_DATE
INVALID_DATE_RANGE
```

---

## Decision analytics d'administració

Els endpoints següents retornen dades dins de l'envelope estàndard `success`,
`data`, `error`. Els filtres `from` i `to` són opcionals, inclusius i utilitzen
el format `YYYY-MM-DD`; `space_id` també és opcional. Una data no vàlida retorna
`INVALID_DATE` i un rang on `from` és posterior a `to` retorna
`INVALID_DATE_RANGE`.

Les mètriques d'ocupació i tendència provenen exclusivament de
`historical_occupancy.csv` processat i utilitzen `occupancy_score` (0-100).
`samples` és el nombre de mostres històriques incloses a l'agregació. Els nivells
segueixen els llindars compartits: `low` (<35), `medium` (35-64), `high`
(65-84) i `very_high` (85-100). Sense mostres, les llistes històriques són
buïdes; no es creen puntuacions.

### GET /admin/analytics/occupancy-by-weekday

Retorna la puntuació mitjana històrica per dia de la setmana i espai.

```json
{
  "success": true,
  "data": {
    "period": {"from": "2026-04-01", "to": "2026-04-30"},
    "spaces": [
      {
        "space_id": "sala-fitnes-sala-cardio",
        "weekdays": [
          {
            "day_of_week": "Monday",
            "average_occupancy_score": 67,
            "occupancy_level": "high",
            "samples": 12
          }
        ]
      }
    ]
  },
  "error": null
}
```

### GET /admin/analytics/occupancy-slots

Retorna fins a cinc franges històriques més saturades i cinc més tranquil·les
per espai. Les franges sense score no s'inclouen.

```json
{
  "success": true,
  "data": {
    "period": {"from": null, "to": null},
    "spaces": [
      {
        "space_id": "sala-fitnes-sala-cardio",
        "most_saturated": [
          {
            "day_of_week": "Monday",
            "hour": "18:30",
            "occupancy_score": 100,
            "occupancy_level": "very_high",
            "samples": 4
          }
        ],
        "quietest": []
      }
    ]
  },
  "error": null
}
```

### GET /admin/analytics/utilization

Retorna una entrada per cada espai del filtre (o present a l'històric) amb
`utilization_percentage`. L'històric actual no inclou capacitat comparable, de
manera que aquest percentatge és `null`, `status` és `insufficient_data` i
`reason` és `historical_capacity_unavailable`. `occupancy_score` no s'interpreta
com un percentatge de capacitat.

```json
{
  "success": true,
  "data": {
    "period": {"from": null, "to": null},
    "spaces": [
      {
        "space_id": "sala-fitnes-sala-cardio",
        "utilization_percentage": null,
        "status": "insufficient_data",
        "reason": "historical_capacity_unavailable",
        "samples": 120
      }
    ]
  },
  "error": null
}
```

### GET /admin/analytics/occupancy-trend

Accepta també `group_by=week|month` (per defecte `week`). Per setmana,
`period` és la data del dilluns corresponent; per mes, és `YYYY-MM`. Un altre
valor retorna `INVALID_GROUP_BY`.

```json
{
  "success": true,
  "data": {
    "period": {"from": "2026-04-01", "to": "2026-04-30"},
    "group_by": "week",
    "series": [
      {
        "space_id": "sala-fitnes-sala-cardio",
        "period": "2026-04-06",
        "average_occupancy_score": 67,
        "occupancy_level": "high",
        "samples": 24
      }
    ]
  },
  "error": null
}
```

### GET /admin/analytics/cancellations

Utilitza les files de reserves reals de SQLite, no l'històric d'ocupació.
`total_reservations` inclou tots els estats; els comptadors de confirmades i
cancel·lades són explícits. La taxa és
`cancelled_reservations / total_reservations × 100` i és `null` sense reserves.
`most_cancelled_slots` conté fins a cinc combinacions dia/hora amb cancel·lacions.

```json
{
  "success": true,
  "data": {
    "period": {"from": "2026-04-01", "to": "2026-04-30"},
    "spaces": [
      {
        "space_id": "sala-fitnes-sala-cardio",
        "total_reservations": 20,
        "confirmed_reservations": 15,
        "cancelled_reservations": 5,
        "cancellation_rate": 25.0,
        "most_cancelled_slots": [
          {
            "day_of_week": "Monday",
            "hour": "18:30",
            "cancelled_reservations": 3
          }
        ]
      }
    ]
  },
  "error": null
}
```

### GET /admin/analytics/safi-impact

Agrega recomanacions i l'acció actual guardada per a cada recomanació. El
percentatge d'acceptació utilitza només recomanacions amb decisió. La reducció
mitjana només inclou accions `accepted` amb franges diferents i scores vàlids
(0-100) on el score recomanat és menor. `accepted_high_to_lower_recommendations`
compta aquestes reduccions amb score demanat de 65 o més. Sense cap reducció
vàlida, `average_saturation_reduction` és `null`. Les accions emmagatzemen
l'estat actual, no un historial de canvis d'acció.
Els filtres `space_id` i `service_id` són opcionals. Si s'envia
`service_id`, el resultat s'agrupa per servei i es retorna a `services`;
sense aquest filtre es manté el resultat existent a `spaces`.

```json
{
  "success": true,
  "data": {
    "period": {"from": "2026-04-01", "to": "2026-04-30"},
    "spaces": [
      {
        "space_id": "sala-fitnes-sala-cardio",
        "recommendations_generated": 20,
        "accepted": 12,
        "ignored": 5,
        "without_action": 3,
        "decision_rate": 85.0,
        "acceptance_rate": 70.6,
        "accepted_high_to_lower_recommendations": 8,
        "accepted_recommendations_with_score_reduction": 10,
        "average_saturation_reduction": 18.5
      }
    ]
  },
  "error": null
}
```

---

## GET /admin/recommendations/stats

Retorna estadístiques sobre les recomanacions generades per SAFi i les decisions dels usuaris.

Permet mesurar l'impacte real de les recomanacions i fins a quin punt els usuaris les segueixen.

### Query parameters opcionals

```text
space_id=sala-fitnes-sala-cardio
service_id=fitness
from=2026-11-01
to=2026-11-30
```

Es poden combinar els filtres.

### Response

```json
{
  "success": true,
  "data": {
    "period": {
      "from": "2026-11-01",
      "to": "2026-11-30"
    },
    "space_id": "sala-fitnes-sala-cardio",
    "service_id": "fitness",
    "total_recommendations": 120,
    "accepted": 73,
    "ignored": 31,
    "without_action": 16,
    "decision_rate": 86.7,
    "acceptance_rate": 70.2,
    "average_score_improvement": 24.3
  },
  "error": null
}
```

### Significat de les mètriques

`total_recommendations`

Nombre total de recomanacions generades.

`accepted`

Recomanacions que l'usuari ha acceptat.

`ignored`

Recomanacions que l'usuari ha ignorat.

`without_action`

Recomanacions per a les quals encara no existeix una decisió registrada.

`decision_rate`

Percentatge de recomanacions que ja tenen una decisió:

```text
(accepted + ignored) / total_recommendations × 100
```

`acceptance_rate`

Percentatge de recomanacions acceptades entre les recomanacions que ja tenen una decisió:

```text
accepted / (accepted + ignored) × 100
```

Les recomanacions sense acció no formen part d'aquest càlcul.

`average_score_improvement`

Reducció mitjana del `occupancy_score` entre la franja original i la franja recomanada.

Exemple:

```text
franja original = 80
franja recomanada = 40
millora = 40 punts
```

Només es tenen en compte recomanacions on existeixen els dos scores.

Si no hi ha recomanacions comparables:

```json
{
  "average_score_improvement": null
}
```

### Sense dades

```json
{
  "success": true,
  "data": {
    "period": {
      "from": null,
      "to": null
    },
    "space_id": null,
    "total_recommendations": 0,
    "accepted": 0,
    "ignored": 0,
    "without_action": 0,
    "decision_rate": 0.0,
    "acceptance_rate": 0.0,
    "average_score_improvement": null
  },
  "error": null
}
```

### Errors possibles

Data incorrecta:

```text
INVALID_DATE
```

Rang invertit:

```text
INVALID_DATE_RANGE
```


## GET /admin/reservations

Retorna les reserves actives creades dins de SAF Hack.

Les reserves cancel·lades no s'inclouen.

### Response

```json
{
  "success": true,
  "data": [
    {
      "reservation_id": "res_12345",
      "space_id": "sala-fitnes-sala-cardio",
      "date": "2026-11-10",
      "start": "19:45",
      "status": "confirmed"
    }
  ],
  "error": null
}
```

---

# 16. Errors de dates

Les dates utilitzen sempre:

```text
YYYY-MM-DD
```

Si una data no té un format vàlid:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_DATE",
    "message": "Date must use YYYY-MM-DD."
  }
}
```

Quan un endpoint utilitza:

```text
from
to
```

i:

```text
from > to
```

retorna:

```text
INVALID_DATE_RANGE
```

No s'han d'intercanviar automàticament les dates.

---

# 17. Regles del contracte

1. El frontend no inventa camps.
2. El backend no canvia noms de camps sense actualitzar aquest document.
3. Totes les dates utilitzen `YYYY-MM-DD`.
4. Totes les hores utilitzen format `HH:MM` de 24 hores.
5. Els identificadors són strings.
6. `service.id` i `service.id` són conceptes diferents.
7. Les APIs de disponibilitat, recomanació i reserva utilitzen `space_id`.
8. `occupancy_score` va de 0 a 100.
9. Si una dada no existeix, utilitzar `null`, `[]` o `unknown` segons el contracte.
10. No inventar valors d'ocupació quan no existeixen dades.
11. SAFi ha de poder indicar que no disposa d'informació suficient.
12. Els missatges mostrats a l'usuari han de ser curts.
13. El backend és responsable de tota la lògica de negoci.
14. App i web consumeixen les mateixes APIs.
15. App i web no accedeixen directament a SQLite.
16. App i web no calculen localment occupancy scores, heatmaps o recomanacions.
17. Els filtres d'administració s'envien al backend.
18. No utilitzar el nombre de reserves de l'app com a substitut de l'ocupació històrica.
19. Una recomanació registrada utilitza el seu `recommendation_id` per guardar posteriorment `accepted` o `ignored`.
20. Qualsevol canvi incompatible en aquests formats s'ha de coordinar abans amb la resta de l'equip.