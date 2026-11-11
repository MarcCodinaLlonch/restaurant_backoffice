# Anàlisi de l'impacte de la BD síncrona a l'event loop

> **Idioma:** [English](DB_ACCESS_ANALYSIS_ENG.md) | [Català](DB_ACCESS_ANALYSIS_CAT.md)

L'enunciat diu que l'accés a la BD pot continuar sent síncron, però que s'ha d'analitzar l'impacte de les operacions bloquejants sobre l'event loop. Aquest document fa aquesta anàlisi i justifica la decisió presa.

---

## 1. El problema

asyncio fa servir **un sol fil** (l'event loop) per a tots els clients.
- Quan una Task fa `await` (per exemple, `await reader.readuntil(...)`), cedeix el torn i el loop atén una altra Task.
- Una consulta amb SQLAlchemy + `psycopg2` és **síncrona**: el fil espera la resposta de PostgreSQL **sense cedir el torn**.
- **Conseqüència:** mentre dura la consulta, cap altre client avança. Si una consulta tardés 200 ms, durant aquests 200 ms el servidor estaria aturat per a tothom.

---

## 2. La decisió: cridar la BD directament

```python
# connection_handler.py
logger.info("%s %s from %s", request.method, request.raw_path, client_address)
# CLAU: el Router (i la BD) és síncron i es crida directament, sense await.
return self._router.handle_request(request)
```

Per què és una bona decisió per a aquesta aplicació:
- **El que és lent de debò és la xarxa, no la BD.** Un client que tarda a enviar la petició, o que no envia res, és el cas que bloquejava la P1. Això sí que es fa amb `await` (`readuntil`, `readexactly`, `drain`), i un client lent no atura els altres.
- **Les consultes són curtes**, de pocs mil·lisegons en local. El bloqueig existeix, però no es nota (vegeu la secció 3).
- **La capa de negoci i la persistència de la P1 no canvien gens.** És el requisit *"maintain the existing business rules and service layer"*.
- **Dues peticions mai toquen la BD alhora**: el Router s'executa sencer sense cap `await`. No hi ha fils, ni condicions de carrera, ni res a sincronitzar.
- **És el codi més simple:** no hi ha cap capa intermèdia entre la xarxa i el Router.

---

## 3. Evidència experimental

L'experiment `experiments/03_blocking_db_impact.py` arrenca el servidor real (`ClientConnectionHandler`) amb un Router fals que bloqueja el fil durant un temps fix (`time.sleep`, com una consulta `psycopg2`), i hi llança **10 clients alhora**. No necessita PostgreSQL:

```bash
python experiments/03_blocking_db_impact.py
```

| Durada de cada consulta | Temps total (10 clients) | Què vol dir |
|---|---|---|
| **2 ms** (com les nostres en local) | **~0,03 s** | El bloqueig no es nota. |
| **200 ms** (BD lenta o remota) | **~2,01 s** | Les peticions van en fila: 10 × 0,2 s. |

**Conclusió:** el temps total és aproximadament *clients × durada de la consulta*. Amb consultes curtes, això és negligible. Si la BD fos lenta, seria un coll d'ampolla.

L'experiment `experiments/02_blocking_call.py` ho mostra d'una altra manera: un *heartbeat* que s'atura mentre dura una crida bloquejant.

---

## 4. Alternatives (si la BD fos lenta)

| Opció | Com funciona | Cost |
|---|---|---|
| **1. BD síncrona cridada directament (la nostra)** | El Router s'executa dins l'event loop | El loop es bloqueja durant cada consulta (pocs ms) |
| 2. `asyncio.to_thread(router.handle_request, request)` | La consulta s'executa en un fil del *ThreadPool* | Introdueix fils, el GIL i un límit de concurrència |
| 3. SQLAlchemy asíncron + `asyncpg` (repte opcional) | Cada consulta és un `await` (`AsyncSession`) | "L'async és contagiós": Repositories, Unit of Work, Services i Router passen a `async def`. Cal carregar les relacions per endavant (`lazy="selectin"`) per evitar l'error `MissingGreenlet`. |

Per a aquesta aplicació, amb consultes curtes, l'opció 1 dona el mateix resultat que les altres dues amb molt menys codi. **Si la BD fos remota o lenta, el pas següent seria l'opció 3**, perquè elimina el bloqueig sense fer servir fils.
