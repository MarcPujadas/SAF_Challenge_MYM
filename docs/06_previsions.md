# 06 — Disponibilitat, heatmap i motor de recomanacions

## Tres dades que no s'han de confondre

1. **Disponibilitat operativa:** resultat actual de les reserves confirmades, capacitat de persones o unitats, horaris i conflictes per recurs.
2. **Ocupacio historica prevista:** calcul estadistic de franges equivalents en dades del passat, no una lectura en temps real.
3. **Reserva creada per l'app:** es registra a `reservations` per calcular disponibilitat operativa i estadistiques de reserves; no demostra assistencia fisica.

## Motor d'horaris i serveis

Les regles viuen a `backend/app/config/schedules.py` i `app/services/schedule_service.py`. Fitness utilitza torns de 75 minuts; altres serveis fan servir configuracions generals que poden requerir validacio. `service_spaces` permet diversos subespais dins d'un servei i separa capacitat de persones de recursos reservables.

`GET /services/{service_id}/availability/week` retorna `days[]`, `slots[]`, `available` i camps de capacitat. És el que es mostra com a **disponibilitat real** a Reserva.

## Heatmap

`GET /availability/heatmap?service_id=fitness&from=2026-11-09&to=2026-11-15` retorna dies i franges amb score i nivell d'ocupacio.

- `occupancy_score`: index comparatiu 0–100, no percentatge d'aforament per defecte.
- `occupancy_level`: `low`, `medium`, `high`, `very_high`, `unknown`.
- `unknown`: no hi ha dades suficients / agregacio no validada; mostrar-ho explícitament.
- Fitness te el cami agregat validat per a estimacio relativa; altres serveis no tenen per defecte una previsio agregada equivalent.

## Recomanacio

`POST /recommendations` amb servei, data i franja. El servei compara el score d'aquella franja amb alternatives proximes quan les dades permeten una comparacio valida. Pot no proposar cap canvi: `recommended_slot: null`. Les recomanacions acceptades/ignorades es registren en taules separades amb `POST /recommendations/{id}/action`.

El xat Ornith utilitza eines internes per consultar dades i redactar respostes, no per inventar percentatges ni reserves.

## Dataset de prova

Per fer una demostracio sense les fonts privades del SAF, `seed_demo.py` genera un historic determinista **SINTETIC**, no observat. Els heatmaps resultants serveixen per mostrar l'experiencia, no per demostrar l'eficacia predictiva real. Separar estrictament demo de produccio en qualsevol video o presentacio.

## Limitacions metodologiques

La projeccio de l'historic ha de preservar el mapping de recursos i la procedencia. Les unitats de reserva no equivalen a persones. No s'ha de calcular ocupacio percentual a partir de recomptes que no permeten inferir-la; els casos sense cobertura han de retornar `unknown`. Sense un seguiment de visites fisicament observades no es pot afirmar que la recomanacio hagi reduit l'ocupacio real.
