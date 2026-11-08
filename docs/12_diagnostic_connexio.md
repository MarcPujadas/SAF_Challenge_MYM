# Connexió de l'app al backend

## Si `/health` respon, però l'app mostra error

No es suficient comprovar `/health`: també han de respondre `/api/v1/services`, `/api/v1/reservations?user_id=demo-user` i `/api/v1/services/fitness/availability/week?from=2026-11-09&to=2026-11-09`.

Executa a **Windows**, a l'arrel del projecte:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verificar_api.ps1
```

Si el comprovador falla, revisa les finestres de FastAPI i el fitxer SQLite. Si passa, revisa la URL exacta de l'app.

### Navegador al mateix Windows

Executa `iniciar_app.bat`. La variable d'Expo apunta a `http://127.0.0.1:8000`. Refresca Expo amb `--clear` i comprova que no tens una instància antiga al port 8081.

### Expo Go al telefon Android/iPhone

Utilitza `iniciar_app_mobil.bat`, que inicia FastAPI escoltant a `0.0.0.0:8000`, intenta detectar la IP LAN de Windows i configura Expo per aquesta IP. Obre `http://IP_PC:8000/health` **des del navegador del telefon**. Cal estar a la mateixa Wi-Fi i que el tallafoc permeti la connexio.

Si ja tenies un backend obert nomes a `127.0.0.1`, tanca'l abans d'executar el launcher per a mobil; el mateix port no pot tenir simultaniament dos Uvicorn.

### Com interpretar errors

- `NETWORK_ERROR`: URL/IP incorrecta, connexio de xarxa, CORS o backend inaccessible.
- `SERVER_ERROR`: servidor HTTP respon, pero la resposta no es JSON de l'API SAFi.
- `INVALID_*`: error del contracte o de dades al backend, **no** de xarxa.
- `LLM_UNAVAILABLE`: sense clau Ornith o gateway caigut; el chat determinista continua disponible.

El client actual mostra l'URL que ha intentat utilitzar. Per defecte la versio web usa loopback; Expo Go intenta obtenir la IP del servidor Metro, o usa l'adreça explícita proporcionada per `iniciar_app_mobil.bat`.

## Important

No poseu la clau del LLM a `frontend/.env`: ha d'estar a `backend/.env` com `UTH_KEY=...`. No envieu la clau al jurat.
