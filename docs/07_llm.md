# 07 — SAFi, Ornith i configuracio de secrets

## On es posa la clau

**Fitxer: `backend/.env`** (dins del backend, no al frontend ni a la web).

```env
UTH_KEY=ENGANXA_AQUI_LA_CLAU_REAL_D_ORNITH
```

L'script `iniciar_app.bat` / `iniciar_web.bat` crea `backend/.env` amb `UTH_KEY=` buit si no existeix. Omple'l tu, desa'l i **reinicia** la finestra del backend. Alternativament copia `backend/.env.example` a `backend/.env`.

- **Mai** incloure la clau a `README.md`, a captures de pantalla, a commits, a fitxers públics o a `frontend/.env`.
- `backend/.env` està exclòs amb `.gitignore`.
- Si s'ha filtrat, cal revocar-la i generar-ne una altra.

## Flux intern

`frontend/src/services/api/index.ts` prova `POST /api/v1/safi/chat-llm`. El backend `app/routers/safi.py` crida `app/services/llm_service.py`. El gateway configurat per projecte es Ornith UAB (model `ornith`), autenticat amb `UTH_KEY`. El LLM pot utilitzar consultes del backend per sustentar les respostes.

Si no hi ha clau o el gateway no esta disponible, el client mòbil recau en `POST /api/v1/safi/chat`, que es determinista i no necessita LLM. El backend diferencia `LLM_UNAVAILABLE` (503) de `LLM_ERROR` (502).

**No presentar el xat determinista com si fos una generacio Ornith real.** A la demo, explica si s'ha configurat la clau.

## Seguretat i abast

El model no ha de crear ni cancel-lar reserves; aquesta accio requereix els endpoints de reserva de l'app o web. La disponibilitat de SQLite, la previsio historica i la informació del cataleg són els recursos de referencia. Les respostes sense evidencies han de reconeixer la manca de dades.

El portal d'administracio encara no incorpora autenticacio real: no exposar la demo a Internet.
