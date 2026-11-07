# SAF Hack - Instructions for AI Coding Agents

## READ THIS BEFORE MAKING ANY CHANGE

Aquest repositori es desenvolupa durant una Hackathon per diverses persones i diversos agents d'IA al mateix temps.

L'objectiu principal és **evitar canvis grans, incompatibilitats i reescriptures innecessàries**.

Aquest document és obligatori per a qualsevol agent que modifiqui el projecte.

---

# 1. Regla principal

> Implementa només la tasca que se t'ha demanat.

NO aprofitis una tasca petita per:

- reestructurar el projecte,
- canviar arquitectura,
- substituir llibreries,
- renombrar carpetes,
- reescriure fitxers sencers,
- canviar endpoints,
- modificar models de dades que no siguin necessaris.

---

# 2. Documents obligatoris

Abans de programar, consulta:

1. `architecture.md`
2. `contracts.md`
3. `agents.md`
4. `idees.md`

Ordre de prioritat en cas de conflicte:

```text
contracts.md
    ↓
architecture.md
    ↓
agents.md
    ↓
idees.md
```

`contracts.md` defineix la interfície entre frontend i backend.

NO modificar els contractes per adaptar-los al teu codi.

Adapta el teu codi al contracte.

---

# 3. Canvis petits

Cada canvi ha de ser:

- petit,
- localitzat,
- fàcil de revisar,
- fàcil de revertir.

Evita modificar fitxers que no tenen relació directa amb la tasca.

---

# 4. No refactoritzar sense permís

NO facis refactors generals.

Exemples prohibits sense instrucció explícita:

```text
"He aprofitat per reorganitzar tot el backend."
"He canviat FastAPI per una altra tecnologia."
"He mogut tots els components."
"He renombrat tots els endpoints per consistència."
"He substituït SQLite per PostgreSQL."
```

La prioritat és tenir una demo funcional, no una arquitectura perfecta.

---

# 5. Backend

Tecnologia obligatòria:

```text
Python
FastAPI
SQLite
```

El backend és la font de veritat.

La lògica de:

- reserves,
- disponibilitat,
- ocupació,
- recomanacions,
- SAFi,
- estadístiques

ha d'estar al backend.

NO posar aquesta lògica al frontend.

---

# 6. Frontend mòbil

Tecnologia prevista:

```text
React Native + Expo
```

El frontend:

- consumeix l'API,
- mostra informació,
- envia accions de l'usuari.

NO:

- calcula recomanacions,
- consulta SQLite,
- llegeix datasets del SAF,
- reprodueix lògica del backend.

---

# 7. Web d'administració

La web d'administració consumeix la mateixa API.

NO crear un backend separat per a administració.

Els endpoints específics utilitzen:

```text
/api/v1/admin/
```

---

# 8. API

Respecta exactament `contracts.md`.

No canviar:

- noms de camps,
- tipus,
- URLs,
- estructura de respostes

sense autorització explícita.

Si falta un contracte necessari:

1. no inventis una solució incompatible,
2. proposa l'endpoint mínim necessari,
3. actualitza `contracts.md` només si aquesta és la tasca assignada.

---

# 9. Dades del SAF

Les dades originals:

- són reals,
- no contenen dades personals,
- són només per a la Hackathon,
- NO es poden publicar,
- NO es poden pujar a repositoris públics,
- NO es poden compartir fora de l'equip,
- NO es poden utilitzar per intentar identificar persones.

Mai afegeixis al Git:

```text
.xlsx
.csv
.json
```

si contenen dades originals o derivades sensibles del repte.

Utilitza exemples sintètics quan necessitis dades de prova publicables.

---

# 10. Recomanador

La primera versió ha de ser simple i explicable.

Prioritzar:

```text
espai
+ dia de la setmana
+ hora
+ ocupació històrica
+ període comparable
```

NO crear models complexos de Machine Learning si no és una tasca explícita.

NO afirmar precisió que no s'ha mesurat.

NO inventar dades.

---

# 11. Trampes del dataset

Qualsevol codi que processi dades ha de respectar les limitacions descrites a `architecture.md`.

Especialment:

- torns de fitness de 75 minuts,
- 10:00 i 15:00 no són necessàriament hores buides,
- pistes i sales tenen unitats diferents,
- recursos duplicats o dividits,
- noms diferents entre fulls,
- reserves de més de 4 hores,
- activitats duplicades,
- sobrerreserves,
- diferències estacionals,
- absència d'identificadors d'usuari.

No generis recomanacions ignorant aquests punts.

---

# 12. SAFi

SAFi no ha d'inventar respostes.

Flux obligatori:

```text
pregunta
→ backend
→ consulta de dades
→ context estructurat
→ LLM
→ resposta
```

El LLM no ha de rebre tot el dataset.

El backend ha de seleccionar les dades rellevants.

Si les dades no permeten respondre, SAFi ha de dir una resposta equivalent a:

> No ho sé amb les dades disponibles.

---

# 13. Dependències

NO afegeixis una dependència nova si es pot resoldre amb una dependència que ja existeix.

Si és imprescindible:

- utilitza una llibreria coneguda,
- afegeix-la al fitxer de dependències corresponent,
- no substitueixis dependències existents sense necessitat.

---

# 14. Fitxers

No eliminis fitxers.

No moguis fitxers.

No renombrïs fitxers.

Excepte si la tasca ho demana explícitament.

---

# 15. Tests

Quan sigui possible, cada funcionalitat de backend ha de tenir almenys una prova simple.

Prioritat de tests:

1. creació de reserva,
2. conflictes de reserva,
3. disponibilitat,
4. recomanacions,
5. endpoints crítics.

No cal una cobertura perfecta durant la Hackathon.

---

# 16. Errors

No amaguis errors.

No utilitzis `try/except` generals només per evitar que l'aplicació falli.

Els errors de l'API han de seguir `contracts.md`.

---

# 17. Estil

Prioritzar codi:

- simple,
- llegible,
- directe,
- fàcil d'explicar al jurat.

Evitar abstraccions innecessàries.

Durant una Hackathon:

> simple i funcional > complex i elegant

---

# 18. Abans d'acabar una tasca

Comprova:

- [ ] He modificat només el necessari.
- [ ] Respecto `architecture.md`.
- [ ] Respecto `contracts.md`.
- [ ] No he publicat dades del SAF.
- [ ] No he canviat endpoints sense permís.
- [ ] No he duplicat lògica del backend al frontend.
- [ ] El projecte continua arrancant.
- [ ] La funcionalitat principal continua funcionant.

---

# 19. Si tens dubtes

NO facis una gran suposició arquitectònica.

Implementa l'opció més petita compatible amb els documents existents.

No intentis "millorar tot el projecte".

Acaba la tasca assignada.
