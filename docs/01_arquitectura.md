# 01 — Arquitectura de SAFi

## Objectiu i peces

```text
Usuari SAF (app Expo/React Native)      Personal SAF (web React/Vite)
              |                                    |
              +----------------+-------------------+
                               | HTTP/JSON
                               v
                       FastAPI /api/v1
             +-----------------+------------------+
             |                 |                  |
         Cataleg         Disponibilitat       SAFi / LLM
         Serveis          i reserves          Ornith UAB
             |                 |                  |
             +---------- SQLite ------------------+
                               |
                       Històric processat
                       (només quan existeix)
```

El backend es **l'unica font de veritat** per a disponibilitat i reserves. L'app i la web no obren SQLite directament.

## Components concrets

- `backend/app/main.py`: FastAPI, CORS, errors coherents, inicialitzacio de SQLite.
- `backend/app/routers/safi_admin.py`: agrega routers del cataleg, disponibilitat, reserves, recomanacions, SAFi i administracio.
- `backend/app/services/`: lògica de negoci per recurs/servei, horaris, reserva, historiques, recomanacions i estadistiques.
- `backend/app/database/database.py`: esquema SQLite, indices, migracions incrementals i usuari demo.
- `frontend/src/services/api/`: client HTTP Expo. `frontend/src/screens/`: UX principal; `components/safi/SafiFloatingCard.tsx`: recomanacions flotants.
- `web/src/services/api.ts`: client HTTP web, desempaqueta `{success,data,error}`; `web/src/pages/`: reserva i panell administratiu.

## Flux d'una reserva

1. `GET /api/v1/services`: seleccionar **servei** (p. ex. Fitness o Pàdel).
2. `GET /api/v1/services/{service_id}/availability/week`: slots, capacitat i disponibilitat actual segons reserves confirmades.
3. Opcional: `POST /api/v1/recommendations` consulta ocupacio **historica** i proposa una alternativa quan hi ha dades validades.
4. `POST /api/v1/reservations` amb `user_id`, `service_id`, `date`, `start`, `end`; el backend valida i autoassigna un recurs físic.
5. `GET /api/v1/reservations` per consultar; `DELETE /api/v1/reservations/{id}` per cancel-lar.

El mode multiespai permet tenir un servei amb diversos recursos (pistes, carrils, sales). `space_id` com a representant segueix existint per compatibilitat però **no** s'ha de fer servir com a substitut de l'agregacio del servei.

## Criteri de fiabilitat

**Disponibilitat actual** = places/recursos segons reserves actuals en SQLite.
**Previsio d'ocupacio** = estimacio estadistica derivada d'historics, quan n'hi ha.
**Reserves de la demo** = dades operatives, no assistencia observada.
No barrejar cap d'aquests tres conceptes.

## Límits

Sense autenticacio real ni autoritzacio d'administradors. Web i app comparteixen el mateix backend. La integracio LLM no te permisos per executar reserves ni modificar l'estat per si sola. Consulteu `07_llm.md` i `09_proves_limitacions.md`.
