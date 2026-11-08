# 02 — Backend i contractes API

## Estructura de codi

- `app/routers/catalog.py`: serveis, espais, recurs associat al servei.
- `app/routers/availability.py`: disponibilitat d'espai, setmana per espai o servei, heatmap.
- `app/routers/reservations.py`: creacio, llistat, cancel-lacio.
- `app/routers/recommendations.py`: suggeriments i accions acceptades/ignorades.
- `app/routers/safi.py`: consell, xat determinista, xat amb Ornith.
- `app/routers/admin.py`: KPIs, ocupacio, analitica d'impacte i cancel-lacions.
- `app/services/`: implementacio de les regles; `app/config/`: serveis, horaris i mappings.

## Contracte HTTP

Totes les rutes de negoci estan sota `/api/v1`. Una resposta correcta es:
```json
{"success":true,"data":{},"error":null}
```
Error:
```json
{"success":false,"data":null,"error":{"code":"INVALID_TIME","message":"..."}}
```
El client ha de llegir `data` i mostrar `error.message` quan correspongui.

## Endpoints principals

| Metode | Ruta | Finalitat |
| --- | --- | --- |
| GET | `/health` | Salut del backend |
| GET | `/api/v1/services` | Cataleg de serveis |
| GET | `/api/v1/services/{id}/spaces` | Recursos del servei |
| GET | `/api/v1/services/{id}/availability/week?from=YYYY-MM-DD&to=YYYY-MM-DD` | Disponibilitat setmanal real |
| GET | `/api/v1/availability/heatmap?service_id=...&from=...&to=...` | Ocupacio prevista / desconeguda |
| POST | `/api/v1/reservations` | Reservar |
| GET | `/api/v1/reservations?user_id=demo-user` | Les meves reserves |
| DELETE | `/api/v1/reservations/{id}` | Cancel-lar |
| POST | `/api/v1/recommendations` | Demanar alternativa |
| POST | `/api/v1/recommendations/{id}/action` | Acceptar/ignorar |
| POST | `/api/v1/safi/chat` | Xat determinista |
| POST | `/api/v1/safi/chat-llm` | Xat Ornith amb fallback al client |
| GET | `/api/v1/admin/summary` | KPIs resum |
| GET | `/api/v1/admin/stats` | Estadistiques |
| GET | `/api/v1/admin/reservations` | Reserves gestionades |
| GET | `/api/v1/admin/recommendations/stats` | Impacte de recomanacions |
| GET | `/api/v1/admin/analytics/*` | Tendencies, ocupacio i utilitzacio |

## Exemples

```json
{"user_id":"demo-user","service_id":"fitness","date":"2026-11-10","start":"18:30","end":"19:45"}
```
A `POST /api/v1/reservations`; no enviar `start_time`/`end_time`: els camps del contracte són `start` i `end`.

```json
{"service_id":"fitness","date":"2026-11-10","preferred_start":"18:30","preferred_end":"19:45"}
```
A `POST /api/v1/recommendations`. `recommended_slot` pot ser `null`.

Consulta l'esquema executable complet a `http://127.0.0.1:8000/docs` i el fitxer arrel `contracts.md`. Els clients han d'usar `service_id` per a consultes multiespai.
