# 03 — Base de dades, datasets i procedencia

## SQLite

Ruta d'execucio: `backend/app/database/safhack.db` (es crea localment, ignorada per Git).

| Taula | Funcio |
| --- | --- |
| `users` | Usuari de demo `demo-user` |
| `spaces` | Espais fisics i recursos reservables |
| `services` | Cataleg visible |
| `service_spaces` | Relacio servei-recurs, capacitat persones/unitats i virtualitat |
| `reservations` | Reserves actuals, recurs assignat i estat |
| `data_sources` | Procedencia de les dades |
| `historical_usage` | Import historic normalitzat, mapping i traçabilitat |
| `recommendations` | Suggeriments guardats |
| `recommendation_actions` | Acceptacions / ignorades |

Les relacions multiespai i les capacitats es configuren a `app/config/service_spaces.py`. Les reserves poden autoassignar recurs. Hi ha conflictes entre camp de futbol complet i les seves meitats.

## Dades reals SAF: NO incloses al repositori public

Els fitxers originals privats que utilitzen els importadors son:
```text
backend/data/local/saf-espais-2026-equips.xlsx
backend/data/local/historical_occupancy.csv
backend/data/local/guided_activity_sessions.csv
```
Per a un entorn autoritzat amb fonts privades, guarda-les localment i executa des de `backend/`:
```powershell
.venv\Scripts\python.exe -m scripts.setup_data
```
**Atencio:** importar dades reals requereix disposar dels fitxers originals i els permisos corresponents. No s'han de pujar a GitHub ni adjuntar-los a un ZIP public sense autoritzacio expressa.

## Demo independent sense dades reals

`python -m scripts.seed_demo` crea un cataleg sintetic i, si no hi ha dades historiques locals, un CSV historic **sintetic** per a Fitness (valors simulats deterministes). No el presenta com a assistencia real.

- El seed es idempotent: no elimina reserves ni substitueix CSV ja existents.
- Les dades sintetiques es generen a `backend/data/local/` (fora de Git).
- Per a una base neta elimina la SQLite local i el CSV sintetic **nomes si son dades de prova**, i torna a executar el seed.
- En entorns reals, dona prioritat al dataset autoritzat i a la validacio d'integritat (`scripts.validate_data_integrity`).

## Semantica de dades

Les reserves actives de SQLite mostren **demanda registrada a l'app**; el recompte historic SAF no es una mesura directa de persones presents. `occupancy_score` pot ser un index relatiu 0-100 i **no** necessàriament un percentatge d'aforament. Recursos amb mappings ambigus queden en revisio i no han de contaminar previsio.
