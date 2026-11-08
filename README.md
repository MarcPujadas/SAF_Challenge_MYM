# SAFi — UAB The Hack 2026

SAFi ajuda els usuaris del Servei d'Activitat Fisica (SAF) de la UAB a **consultar disponibilitat, reservar serveis i triar franges amb menys ocupacio prevista**. Inclou una aplicacio Expo/React Native, un portal web de reserves i administracio, i un backend Python/FastAPI amb SQLite.

## Inici rapid a Windows (doble clic)

**Requisits:** Windows 10/11, Python 3.12+ i Node.js 22+ amb npm; Internet per instal-lar dependències la primera vegada.

| Accio | Fitxer |
| --- | --- |
| Executar l'aplicacio SAFi a l'ordinador (Expo Web) | `iniciar_app.bat` |
| Executar el portal web i panell d'administracio | `iniciar_web.bat` |

Els dos iniciadors configuren l'entorn Python, instal-len dependències, creen dades **sintetiques** de demo si no hi ha dades locals i inicien el backend si encara no esta executant-se. Cal esperar que els servidors acabin d'arrencar; no tanquis les finestres de terminal.

- Backend: http://127.0.0.1:8000/health
- Swagger API: http://127.0.0.1:8000/docs
- Portal web: http://127.0.0.1:5173
- App Expo Web: URL que mostra Expo al terminal (habitualment port 8081).

**L'app al navegador** no requereix un telefon ni una connexio Wi-Fi entre dispositius. Per a un telefon fisic, cal configurar la IP local del PC a `frontend/.env` i iniciar Expo en mode LAN. Vegeu [instal-lacio](docs/08_instalacio.md).

## Clau del LLM (Ornith UAB)

Copia `backend/.env.example` a **`backend/.env`** i afegeix-hi la clau:

```env
UTH_KEY=LA_TEVA_CLAU_PRIVADA
```

El fitxer `backend/.env` esta ignorat per Git i **no s'ha d'incloure a l'entrega publica**. Sense clau, el xat de SAFi utilitza el fallback determinista. Detalls a [docs/07_llm.md](docs/07_llm.md).

## Estructura

- `backend/`: FastAPI, SQLite, serveis, imports, seed de demostracio i tests.
- `frontend/`: aplicacio Expo/React Native.
- `web/`: portal de reserves i dashboard de direccio (React/Vite).
- `scripts/`: preparacio de Windows.
- `docs/`: arquitectura, funcionament intern, contractes, fonts, tests i limitacions.
- `demo/`: guia per enregistrar una demostracio verificable.
- `iniciar_app.bat`, `iniciar_web.bat`: iniciadors Windows.

## Documentacio

1. [Arquitectura](docs/01_arquitectura.md)
2. [Backend i API](docs/02_backend_api.md)
3. [Base de dades i fonts](docs/03_dades.md)
4. [App](docs/04_app.md)
5. [Web i administrador](docs/05_web_dashboard.md)
6. [Disponibilitat, previsio i SAFi](docs/06_previsions.md)
7. [LLM i seguretat](docs/07_llm.md)
8. [Instal-lacio Windows](docs/08_instalacio.md)
9. [Proves i limitacions](docs/09_proves_limitacions.md)
10. [Guia d'entrega](docs/10_entrega.md)

També es conserven les especificacions originals `architecture.md`, `contracts.md` i `backend/README.md`, que poden contenir decisions historriques; per preparar l'entrega, prioritza la documentacio `docs/`.

## Fonts, privacitat i limitacions

Els fitxers originals del SAF i les dades històriques privades **no es publiquen**. Quan arrenca sense ells, `backend/scripts/seed_demo.py` genera recursos i ocupacio **SINTETICS**, marcats com a demo: no son mesures reals ni validen prediccions del SAF. Per a imports reals, consulta [docs/03_dades.md](docs/03_dades.md).

Aquesta es una prova de concepte: identificacio demo (`demo-user`), sense sistema de permisos, no totes les previsions agregades validades i horaris que cal contrastar amb el SAF. No presentar dades sintetiques com a reals.
