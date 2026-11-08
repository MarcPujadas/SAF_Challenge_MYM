# 08 — Instal-lacio i execucio (Windows)

## Requisits previs

- Windows 10/11 amb PowerShell i CMD.
- Python 3.12 o superior, accesible amb `py -3` o `python`; el primer Windows venv es crea automaticament.
- Node.js **22** o superior amb `npm`; instal-lar-lo prèviament des de https://nodejs.org.
- Acces a Internet **durant la primera execucio** per `pip`/`npm`. Un cop instal-lat, els servidors s'executen en local.
- Ports lliures: backend 8000, portal web 5173, servidor Expo habitualment 8081.

## Passos (mateix PC, sense telefon)

1. Descomprimeix el ZIP de SAFi en una ruta normal, sense permisos restringits.
2. Fes doble clic a **`iniciar_app.bat`** per iniciar l'app en Expo Web, **o** a **`iniciar_web.bat`** per obrir el portal i dashboard.
3. La primera vegada es crea `backend/.venv`, s'instal-len les dependències i es crea una base de dades de demostracio sintètica (sense dades privades).
4. Espera els missatges de FastAPI i de Vite/Expo. No tanquis les consoles mentre facis la demo.
5. Comprova `http://127.0.0.1:8000/health` i, en el cas del portal, `http://127.0.0.1:5173`.

Els dos iniciadors poden compartir un backend existent si `/health` respon. Per aturar-ho, tanca les finestres dels servidors.

## Execucio manual

```powershell
cd backend
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m scripts.seed_demo
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

En una segona consola, app:
```powershell
cd frontend
Copy-Item .env.example .env
npm ci
npx expo install react-dom react-native-web @expo/metro-runtime
npx expo start --web
```

O portal web:
```powershell
cd web
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

## Executar la versio de telefon (opcional)

La ruta recomanada per al jurat es Expo Web. Si vols Expo Go en un telefon de la mateixa LAN, executa Uvicorn amb `--host 0.0.0.0`, esbrina la IPv4 del PC amb `ipconfig` i posa `EXPO_PUBLIC_API_URL=http://IP_DEL_PC:8000` a `frontend/.env` i `EXPO_PUBLIC_USE_MOCKS=false`. Reinicia Expo amb `npx expo start -c`; prova `http://IP_DEL_PC:8000/health` des del navegador del telefon. Depen de la configuracio Wi-Fi i el firewall, i no es la ruta principal de la demo.

## Clau LLM

`backend/.env`: `UTH_KEY=...`. Despres d'afegir-la, reinicia Uvicorn. No posis mai aquesta clau a un fitxer public o `EXPO_PUBLIC_*`.

## Problemes habituals

- **Python o node no reconegut:** instal-la'l i reobre les consoles.
- **npm ci / pip falla:** revisa Internet i la versio de Node/Python.
- **Port 8000 ocupat:** si ja hi ha un backend SAFi sa, els iniciadors el reutilitzen; si es un altre servei, tanca'l.
- **Frontend carregant indefinidament:** comprova `/health`, l'API i la consola del navegador.
- **Sense serveis:** executa `cd backend` i `.venv\Scripts\python.exe -m scripts.seed_demo`.
- **Heatmap desconegut:** no es un error necessàriament: fonts insuficients o servei sense previsio validada.
- **Sense respostes Ornith:** comprova `backend/.env`; el xat determinista segueix funcionant.

No s'ha testat aquest paquet en tots els Windows possibles. Per assegurar la portabilitat, prova'l en un ordinador net abans de l'entrega definitiva.
