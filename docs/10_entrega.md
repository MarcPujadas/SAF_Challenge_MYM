# 10 — Guia d'entrega al jurat

## Objectiu

El jurat ha de poder **descarregar, executar i entendre** SAFi sense dependre dels ordinadors dels participants.

## Contingut del ZIP

```text
SAF_Challenge_MYM/
  backend/                 FastAPI, SQLite/schema, serveis, proves
  frontend/                Expo/React Native
  web/                     Portal React/Vite
  scripts/                 Preparacio Windows i utilitats
  docs/                    Arquitectura, API, dades, app/web, previsions, LLM, tests
  demo/                    Instruccions de gravacio (video no inclos per defecte)
  iniciar_app.bat           Obre app en Expo Web
  iniciar_web.bat           Obre portal web
  README.md                Guia de primer us
```

**Descarrega la versio exacta de `main` des de GitHub:** `https://github.com/MarcPujadas/SAF_Challenge_MYM/archive/refs/heads/main.zip`.

## Proposta demo audiovisual (90–120 s)

1. Introduccio SAFi / problema de les hores punta.
2. Mostrar serveis, reserva i disponibilitat real a l'app.
3. Heatmap, explicant explicitament previsio vs disponibilitat.
4. Recomanacio de SAFi i reserva confirmada.
5. Chatbot i, breument, dashboard administratiu.
6. Tancar amb impacte potencial i limitacions verificables.

Enregistreu accions reals de l'app/web; no simuleu una reserva ni presenteu dades de seed com si fossin historics reals. Si gravem amb mode demo, identificar-lo en la presentacio.

## Abans de pujar o enviar

1. Executa les comprovacions de `09_proves_limitacions.md`.
2. Prova els dos `.bat` en un Windows net o un entorn diferent.
3. Comprova que el ZIP no conte `backend/.env`, claus, `.venv`, `node_modules`, `*.db` ni datasets privats.
4. **No adjuntis fonts del SAF sense autoritzacio**; el seed sintetic cobreix la demo.
5. Comprova que els endpoints/ports no entren en conflicte.
6. Adjunta el video real només si l'heu enregistrat i revisat.
7. Mantenir un hash/commit de referencia perque el jurat revisi la mateixa versio del codi.

## Branques

La font oficial de l'entrega es **`main`**. Les branques divergents poden contenir feina antiga o experimental. No esborrar una branca sense comparar-ne els commits exclusius. `scripts/netejar_branques.ps1` ofereix un procediment segur per a les branques remotament **ja fusionades**; no destrueix automaticament les divergents.
