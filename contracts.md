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

Per consultar disponibilitat, crear reserves o demanar recomanacions s'ha d'utilitzar sempre:

```text
service.space_id
```

No hardcodejar `fitness` com a identificador d'espai.

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
      "reservable": true
    },
    {
      "id": "pool-25m",
      "name": "Piscina 25 m",
      "description": "Piscina de 25 metres",
      "space_id": "piscina-25-metres-carrer-1",
      "reservable": true
    },
    {
      "id": "padel",
      "name": "Pàdel",
      "description": "Pistes de pàdel",
      "space_id": "pistes-de-padel-pista-1",
      "reservable": true
    }
  ],
  "error": null
}
```

---

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

### Errors possibles

```text
INVALID_DATE
INVALID_SPACE
```

---

# 6. Heatmap d'ocupació

## GET /availability/heatmap

Retorna ocupació històrica processada per dies i franges.

### Query parameters

```text
space_id=sala-fitnes-sala-cardio
from=2026-04-01
to=2026-04-30
```

Els filtres permeten limitar les dades per espai i període.

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

### Sense dades

Si no existeixen dades per als filtres sol·licitats:

```json
{
  "success": true,
  "data": {
    "space_id": "sala-fitnes-sala-cardio",
    "days": []
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

La recomanació queda registrada al backend perquè posteriorment es pugui saber si l'usuari l'ha acceptat o ignorat.

Per al MVP, l'usuari associat és:

```text
demo-user
```

### Request

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
      "space_id": "sala-fitnes-sala-cardio",
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

Crea una reserva real i la guarda a SQLite.

### Request

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
    "space_id": "sala-fitnes-sala-cardio",
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

### Query parameters

```text
user_id=demo-user
```

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
        "space_id": "sala-fitnes-sala-cardio",
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
6. `service.id` i `service.space_id` són conceptes diferents.
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