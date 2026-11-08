# 11 — Auditoria de branques (8/11/2026)

`main` incorpora el backend multiespai (PR #14), el frontend multiespai/redisseny de Marcos (PR #16) i una còpia selectiva de **web/** de Hajar amb correccions dels contractes. **No** s'ha fusionat la branca web sencera perquè porta un backend antic i un fitxer SQLite.

## Neteja segura

El connector GitHub d'aquesta sessio **no permet esborrar branques remotes**. Hi ha una utilitat `scripts/netejar_branques.ps1` que, executada amb Git i permisos d'escriptura, mostra primer les branques **completament fusionades** a `origin/main`. Només amb `-Apply`, i confirmant cadascuna, les elimina.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/netejar_branques.ps1
powershell -ExecutionPolicy Bypass -File scripts/netejar_branques.ps1 -Apply
```

## Branques divergents que cal preservar i revisar manualment

- `hajar/frontend-ui`: prototip anterior d'app web, no compatible directament amb frontend actual.
- `hajar/web-dashboard`: el subtree web s'ha recuperat i corregit, però la branca també conté backend i SQLite antics.
- `marc/guided-activities-wip`: scripts d'activitats dirigides no verificats/integrats.
- `marc/safi-ornith-poc`: prova inicial d'Ornith/servicis; no s'ha validat com a millora sobre l'actual.
- `marcos/mobile-api-integration` i `marcos/mobile-heatmap-v3`: implementacions anteriors que poden divergir del frontend consolidat.
- `yassin/backend-hardening`: un commit divergent, pendent d'auditoria abans d'integrar.

**No esborris les anteriors** fins comparar-ne els commits no inclosos a `main`. El script no les esborrara per defecte. Les branques fully-merged/behind no tenen commits exclusius i son candidates a neteja segura.
