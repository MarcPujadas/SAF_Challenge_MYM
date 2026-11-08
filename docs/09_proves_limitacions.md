# 09 — Tests, validacio i limitacions

## Tests automatitzats

`backend/tests/` inclou proves de reserves, recursos, imports, recomanacions, SAFi, analitica i multiespai. Execucio:
```powershell
cd backend
.venv\Scripts\python.exe -m pytest -q
```

`frontend/` usa TypeScript:
```powershell
cd frontend
npm ci
npx tsc --noEmit
```

`web/`:
```powershell
cd web
npm ci
npm run build
```

CI a `.github/workflows/ci.yml`. Passar CI es una comprovacio automatitzada, **no** equival a validar tots els fluxos visuals en Windows real.

## Checklist manual d'entrega

- Backend `/health` i `/docs` accessibles.
- App en Expo Web: Home, Serveis, Reserva, heatmap, SAFi Chat.
- Portal web: reserves i dashboard visibles.
- Crear reserva de Fitness en slot disponible, comprovar persistencia i duplicats.
- Consultar les reserves amb `demo-user` i cancel-lar-ne una des de l'app.
- Comprovar que les targetes del heatmap no confonen disponibilitat amb previsio.
- Verificar recomanacions per Fitness i resposta `unknown` per serveis sense historic validat.
- Validar el comportament del xat amb i sense clau Ornith.
- Provar a Windows amb ZIP acabat de descomprimir.

## Limitacions conegudes

- Identitat temporal `demo-user`; sense login autenticat, rols ni control d'accés administratiu.
- Dataset public de demo sintètic. No representa dades reals ni assistencia observada.
- Importadors reals depenen d'arxius SAF privats no inclosos al repositori.
- Prediccio agregada principalment validada per a Fitness; altres serveis poden mostrar `unknown`.
- Horaris genèrics i caps de setmana pendents de contrastar amb les normes actuals del SAF.
- El sistema no implementa un predictor ML entrenat en viu; les recomanacions son estadistiques/explicables.
- La capa Expo Web es una alternativa per a demo de PC i no substitueix les proves amb una compilacio nativa.
- El dashboard exposa valors operatius, no certifica afluencia real.
- Connexio del telefon fisic requereix IP LAN, firewall i xarxa comuna.

No afirmar que aquestes limitacions estiguin resoltes fins verificar-ho.
