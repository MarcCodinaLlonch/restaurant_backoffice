# Documentació del Protocol de Comunicació (TCP REST-Inspired)

## Restaurant BackOffice — Versió 2.0.0

Aquest document descriu l'especificació completa del protocol d'aplicació utilitzat per a la comunicació entre el **Client** i el **Servidor** del sistema de gestió de restaurants.

---

## 1. Visió General i Fonaments Teòrics

El protocol està inspirat en **HTTP/1.1 REST** implementat directament sobre la capa de transport **TCP (Transmission Control Protocol)** mitjançant sockets bloquejants en Python.

### Per què no utilitzar Pickle de Python?
Pickle permet serialitzar objectes natius de Python fàcilment, però presenta greus problemes de seguretat (execució remota de codi maliciós en deserialitzar dades no confiables) i genera un acoblament estricte entre les versions i llenguatges del client i del servidor.

### Solució adoptada:
1. **Format de text amb codificació UTF-8**: Missatges llegibles per humans i interoperables amb qualsevol tecnologia o llenguatge futur.
2. **Serialització de dades en JSON**: Totes les càrregues útils (payloads) viatgen en format JSON estàndard.
3. **Delimitació de missatges**:
   - Cada línia de capçalera finalitza amb la seqüència estàndard CRLF (`\r\n`).
   - El final de les capçaleres es determina amb una línia buida (`\r\n\r\n`).
   - Si la petició o la resposta conté un cos (body), la capçalera `Content-Length` indica exactament quants bytes s'han de llegir del socket.
4. **Model Stateless (Sense estat)**: Cada petició és atòmica i independent. El client obre una connexió TCP, envia la petició, rep la resposta i es tanca la connexió (`Connection: close`).

---

## 2. Format dels Missatges

### 2.1 Format de la Petició (Request)

Una petició consta de:
1. **Línia de petició (Request Line)**: `<MÈTODE> <RUTA_RECURS> <VERSIÓ_PROTOCOL>\r\n`
2. **Capçaleres (Headers)**: Una o més línies `<Clau>: <Valor>\r\n`
3. **Separador de capçaleres**: Línia buida `\r\n`
4. **Cos (Body)**: Dades JSON en UTF-8 (opcional, requerit en POST i PUT).

```http
POST /categories HTTP/1.1\r\n
Host: 127.0.0.1:8080\r\n
Accept: application/json\r\n
Content-Type: application/json; charset=utf-8\r\n
Content-Length: 29\r\n
\r\n
{"category_name": "Postres"}
```

### 2.2 Format de la Resposta (Response)

Una resposta consta de:
1. **Línia d'estat (Status Line)**: `<VERSIÓ_PROTOCOL> <CODI_ESTAT> <TEXT_ESTAT>\r\n`
2. **Capçaleres (Headers)**: Informació del tipus de contingut i longitud.
3. **Separador de capçaleres**: Línia buida `\r\n`
4. **Cos (Body)**: Dades JSON en UTF-8 (si s'escau).

```http
HTTP/1.1 201 Created\r\n
Connection: close\r\n
Content-Type: application/json; charset=utf-8\r\n
Content-Length: 38\r\n
\r\n
{"id": 4, "category_name": "Postres"}
```

---

## 3. Codis d'Estat i Gestió d'Errors

| Codi | Nom | Significat |
| :--- | :--- | :--- |
| **200** | OK | Petició processada correctament. Retorna dades en format JSON. |
| **201** | Created | Recurs creat amb èxit a la base de dades. Retorna el recurs creat amb el seu ID assignat. |
| **204** | No Content | Operació realitzada amb èxit (ex: DELETE). No retorna cos. |
| **400** | Bad Request | Dades invàlides enviades pel client (nom buit, preu negatiu, format incorrecte). |
| **404** | Not Found | El recurs sol·licitat no existeix a la base de dades o la ruta és desconeguda. |
| **500** | Internal Server Error | Error inesperat durant l'execució al servidor. |
| **503** | Service Unavailable | Retornat pel client quan el servidor TCP no és accessible. |

En cas d'error (4xx o 5xx), el cos de la resposta sempre conté un objecte JSON amb la clau `"error"`:
```json
{
  "error": "El nom de la categoria no pot estar buit."
}
```

---

## 4. Recursos i Operacions Suportades

### 4.1 Categories (`/categories`)

| Mètode | Ruta | Descripció | Cos Petició (JSON) | Codi Resposta |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/categories` | Llistar totes les categories | Cap | `200 OK` |
| `GET` | `/categories/{id}` | Obtenir categoria per ID | Cap | `200 OK` / `404` |
| `POST` | `/categories` | Crear una nova categoria | `{"category_name": "string"}` | `201 Created` / `400` |
| `PUT` | `/categories/{id}` | Modificar categoria | `{"category_name": "string"}` | `200 OK` / `404` |
| `DELETE` | `/categories/{id}` | Eliminar categoria | Cap | `204 No Content` / `404` |

---

### 4.2 Al·lèrgens (`/allergens`)

| Mètode | Ruta | Descripció | Cos Petició (JSON) | Codi Resposta |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/allergens` | Llistar tots els al·lèrgens | Cap | `200 OK` |
| `GET` | `/allergens/{id}` | Obtenir al·lèrgen per ID | Cap | `200 OK` / `404` |
| `POST` | `/allergens` | Crear un nou al·lèrgen | `{"allergen_name": "string"}` | `201 Created` / `400` |
| `PUT` | `/allergens/{id}` | Modificar al·lèrgen | `{"allergen_name": "string"}` | `200 OK` / `404` |
| `DELETE` | `/allergens/{id}` | Eliminar al·lèrgen | Cap | `204 No Content` / `404` |

---

### 4.3 Plats (`/dishes`)

| Mètode | Ruta | Descripció | Cos Petició (JSON) | Codi Resposta |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/dishes` | Llistar plats (admet `?active=true` o `?name=text`) | Cap | `200 OK` |
| `GET` | `/dishes/{id}` | Obtenir plat per ID (amb al·lèrgens N:M) | Cap | `200 OK` / `404` |
| `POST` | `/dishes` | Crear nou plat (relació 1:N amb categoria) | `{"dish_name": "string", "id_category": int, "description": "str", "is_active": bool}` | `201 Created` / `400` |
| `PUT` | `/dishes/{id}` | Modificar plat | Camps a modificar en JSON | `200 OK` / `404` |
| `DELETE` | `/dishes/{id}` | Eliminar plat | Cap | `204 No Content` / `404` |
| `POST` | `/dishes/{id}/allergens` | Afegir al·lèrgen a plat (relació N:M) | `{"id_allergen": int}` | `200 OK` / `400` |

---

### 4.4 Empleats (`/employees`)

| Mètode | Ruta | Descripció | Cos Petició (JSON) | Codi Resposta |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/employees` | Llistar tots els empleats (admet `?role=rol` o `?name=x&surname=y`) | Cap | `200 OK` |
| `GET` | `/employees/{id}` | Obtenir empleat per ID | Cap | `200 OK` / `404` |
| `POST` | `/employees` | Crear empleat (i credencials 1:1 opcionals) | `{"name": "str", "surname": "str", "national_id": "str", "role": "str", "email": "str", "password": "str"}` | `201 Created` / `400` |
| `PUT` | `/employees/{id}` | Modificar empleat | Camps a modificar en JSON | `200 OK` / `404` |
| `DELETE` | `/employees/{id}` | Eliminar empleat (esborrat en cascada) | Cap | `204 No Content` / `404` |

---

### 4.5 Menús (`/menus`)

| Mètode | Ruta | Descripció | Cos Petició (JSON) | Codi Resposta |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/menus` | Llistar menús (admet `?name=x` o `?min_price=x&max_price=y`) | Cap | `200 OK` |
| `GET` | `/menus/{id}` | Obtenir menú per ID (amb llista de plats N:M) | Cap | `200 OK` / `404` |
| `POST` | `/menus` | Crear nou menú | `{"menu_name": "string", "price": float}` | `201 Created` / `400` |
| `PUT` | `/menus/{id}` | Modificar menú | Camps a modificar en JSON | `200 OK` / `404` |
| `DELETE` | `/menus/{id}` | Eliminar menú | Cap | `204 No Content` / `404` |
| `POST` | `/menus/{id}/dishes` | Afegir plat a menú (relació N:M) | `{"id_dish": int}` | `200 OK` / `400` |
| `DELETE` | `/menus/{id}/dishes/{dish_id}` | Eliminar plat d'un menú | Cap | `204 No Content` / `404` |

---

### 4.6 Vendes (`/sales`)

| Mètode | Ruta | Descripció | Cos Petició (JSON) | Codi Resposta |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/sales` | Llistar vendes (admet `?page=1`, `?date=YYYY-MM-DD`, `?employee_id=X`, `?menu_id=Y`, `?date_from=A&date_to=B`) | Cap | `200 OK` |
| `GET` | `/sales/{menu_id}/{emp_id}/{date}` | Obtenir venda per PK composta | Cap | `200 OK` / `404` |
| `POST` | `/sales` | Enregistrar venda (N:M amb atributs) | `{"id_menu": int, "id_employee": int, "sale_date": "YYYY-MM-DD", "quantity_sold": int}` | `201 Created` / `400` |
| `PUT` | `/sales/{menu_id}/{emp_id}/{date}` | Actualitzar quantitat venuda | `{"quantity_sold": int}` | `200 OK` / `400` / `404` |
| `DELETE` | `/sales/{menu_id}/{emp_id}/{date}` | Eliminar venda per PK composta | Cap | `204 No Content` / `404` |

---

## 5. Exemples Reals d'Operacions CRUD

### 5.1 Create (Crear Categoria)
**Petició Client:**
```
POST /categories HTTP/1.1
Host: 127.0.0.1:8080
Accept: application/json
Content-Type: application/json; charset=utf-8
Content-Length: 30

{"category_name": "Amanides"}
```
**Resposta Servidor:**
```
HTTP/1.1 201 Created
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 39

{"id": 1, "category_name": "Amanides"}
```

### 5.2 Read / List (Llistar Plats Actius)
**Petició Client:**
```
GET /dishes?active=true HTTP/1.1
Host: 127.0.0.1:8080
Accept: application/json
Connection: close
```
**Resposta Servidor:**
```
HTTP/1.1 200 OK
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 135

[{"id": 1, "dish_name": "Amanida Cèsar", "description": "Enciam fresc i salsa cèsar", "is_active": true, "id_category": 1, "category_name": "Amanides", "allergens": []}]
```

### 5.3 Update (Modificar Menú)
**Petició Client:**
```
PUT /menus/1 HTTP/1.1
Host: 127.0.0.1:8080
Accept: application/json
Content-Type: application/json; charset=utf-8
Content-Length: 38

{"menu_name": "Menú Migdia", "price": 14.50}
```
**Resposta Servidor:**
```
HTTP/1.1 200 OK
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 58

{"id": 1, "menu_name": "Menú Migdia", "price": 14.5, "dishes": []}
```

### 5.4 Delete (Eliminar Al·lèrgen)
**Petició Client:**
```
DELETE /allergens/3 HTTP/1.1
Host: 127.0.0.1:8080
Connection: close
```
**Resposta Servidor:**
```
HTTP/1.1 204 No Content
Connection: close
Content-Length: 0
```
