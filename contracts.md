# SAF Hack - API Contracts

## 1. Objectiu

Aquest document defineix els contractes entre:

- aplicació mòbil,
- panell web d'administració,
- backend FastAPI.

Tots els equips han de respectar aquests formats.

**No canviar un contracte existent sense coordinar-ho amb la resta de l'equip.**

Base URL de desenvolupament:

```text
/api/v1
```

Totes les respostes utilitzen JSON.

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

# 3. Espais i serveis

## GET /spaces

Retorna els espais disponibles.

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "fitness",
      "name": "Sala Fitness",
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
      "description": "Sala de fitness del SAF",
      "space_id": "fitness",
      "reservable": true
    }
  ],
  "error": null
}
```

---

# 4. Disponibilitat

## GET /availability

### Query parameters

```text
space_id=fitness
date=2026-11-08
```

### Response

```json
{
  "success": true,
  "data": {
    "space_id": "fitness",
    "date": "2026-11-08",
    "slots": [
      {
        "start": "17:00",
        "end": "18:15",
        "available": true,
        "remaining_capacity": 30,
        "occupancy_level": "high",
        "occupancy_score": 82
      },
      {
        "start": "19:00",
        "end": "20:15",
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

---

# 5. Heatmap

## GET /availability/heatmap

### Query parameters

Opcional:

```text
space_id=fitness
from=2026-11-09
to=2026-11-15
```

### Response

```json
{
  "success": true,
  "data": {
    "space_id": "fitness",
    "days": [
      {
        "date": "2026-11-09",
        "slots": [
          {
            "hour": "09:00",
            "occupancy_score": 31,
            "occupancy_level": "low"
          },
          {
            "hour": "18:00",
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

---

# 6. Recomanacions

## POST /recommendations

Demana al backend les millors opcions per a una reserva.

### Request

```json
{
  "space_id": "fitness",
  "date": "2026-11-10",
  "preferred_start": "18:00",
  "preferred_end": "20:00"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "requested_slot": {
      "start": "18:00",
      "occupancy_score": 89,
      "occupancy_level": "very_high"
    },
    "recommended_slot": {
      "start": "19:00",
      "occupancy_score": 52,
      "occupancy_level": "medium"
    },
    "message": "Les 19:00 acostumen a tenir menys ocupació que les 18:00.",
    "confidence": "medium",
    "basis": {
      "space": "Sala Fitness",
      "weekday": "Tuesday",
      "historical_period": "comparable recent months"
    }
  },
  "error": null
}
```

### confidence

```text
low
medium
high
```

El backend no ha de retornar `high` si les dades són insuficients o poc comparables.

---

# 7. Crear reserva

## POST /reservations

### Request

```json
{
  "user_id": "demo-user",
  "space_id": "fitness",
  "date": "2026-11-10",
  "start": "19:00",
  "end": "20:15"
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
    "space_id": "fitness",
    "date": "2026-11-10",
    "start": "19:00",
    "end": "20:15"
  },
  "error": null
}
```

### Errors possibles

```text
SLOT_NOT_AVAILABLE
INVALID_SPACE
INVALID_TIME
RESERVATION_CONFLICT
```

---

# 8. Consultar reserves

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
      "space_id": "fitness",
      "space_name": "Sala Fitness",
      "date": "2026-11-10",
      "start": "19:00",
      "end": "20:15",
      "status": "confirmed"
    }
  ],
  "error": null
}
```

---

# 9. Cancel·lar reserva

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

Pot quedar fora del MVP si falta temps.

---

# 10. SAFi durant la reserva

## POST /safi/advice

Aquest endpoint retorna un missatge curt per mostrar durant el procés de reserva.

No necessita utilitzar el LLM si una resposta estructurada és suficient.

### Request

```json
{
  "space_id": "fitness",
  "date": "2026-11-10",
  "start": "18:00"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "type": "warning",
    "message": "Aquesta hora acostuma a tenir una ocupació molt alta.",
    "alternative": {
      "start": "19:00",
      "message": "Les 19:00 solen tenir menys ocupació."
    },
    "occupancy_score": 89
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

# 11. SAFi Chat

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
    "message": "Segons les dades disponibles, les 19:00 tenen menys ocupació prevista que les 18:00.",
    "sources": [
      {
        "type": "historical_occupancy",
        "space_id": "fitness",
        "date_reference": "Tuesday"
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

---

# 12. Usuari actual

## GET /users/me

Per al MVP pot retornar sempre l'usuari de demo.

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

Això permet afegir autenticació real més endavant sense canviar el frontend.

---

# 13. API d'administració

Tots els endpoints d'administració utilitzen:

```text
/api/v1/admin/...
```

## GET /admin/summary

### Response

```json
{
  "success": true,
  "data": {
    "total_reservations": 430,
    "reservations_today": 71,
    "busiest_space": {
      "id": "fitness",
      "name": "Sala Fitness"
    },
    "busiest_hour": "18:00"
  },
  "error": null
}
```

---

## GET /admin/occupancy

### Query parameters

```text
from=2026-11-01
to=2026-11-30
space_id=fitness
```

Tots són opcionals excepte quan el backend necessiti limitar el rang.

### Response

```json
{
  "success": true,
  "data": {
    "period": {
      "from": "2026-11-01",
      "to": "2026-11-30"
    },
    "spaces": [
      {
        "space_id": "fitness",
        "average_occupancy_score": 67,
        "peak_hour": "18:00",
        "lowest_hour": "09:00"
      }
    ]
  },
  "error": null
}
```

---

## GET /admin/reservations

Retorna reserves creades dins de SAF Hack.

### Response

```json
{
  "success": true,
  "data": [
    {
      "reservation_id": "res_12345",
      "space_id": "fitness",
      "date": "2026-11-10",
      "start": "19:00",
      "status": "confirmed"
    }
  ],
  "error": null
}
```

---

# 14. Regles del contracte

1. El frontend no inventa camps.
2. El backend no canvia noms de camps sense actualitzar aquest document.
3. Totes les dates utilitzen `YYYY-MM-DD`.
4. Totes les hores utilitzen format `HH:MM` de 24 hores.
5. Els identificadors són strings.
6. `occupancy_score` va de 0 a 100.
7. Si una dada no existeix, utilitzar `null` o `unknown`, no inventar-la.
8. SAFi ha de poder indicar que no disposa d'informació suficient.
9. Els missatges mostrats a l'usuari han de ser curts.
10. El backend és responsable de tota la lògica de negoci.
