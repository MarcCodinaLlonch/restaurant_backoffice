# Communication Protocol Specification (REST-Inspired over TCP)

> 🌐 **Language:** **English (PROTOCOL_ENG.md)** | [Català (PROTOCOL_CAT.md)](PROTOCOL_CAT.md)

## Restaurant BackOffice — Version 3.0.0 (AsyncIO Multi-Client)

This document defines the complete technical specification of the application-level communication protocol established between the **Client** and the **Server** of the restaurant management system.

---

## 1. Overview and Theoretical Foundations

The protocol is inspired by **HTTP/1.1 REST**, implemented directly on top of the **TCP (Transmission Control Protocol)** transport layer using an asynchronous non-blocking concurrent server powered by Python's standard `asyncio` library.

### Asynchronous Concurrency and Transport (v3.0.0):
1. **Non-blocking Model:** The server processes multiple simultaneous client connections over a single CPU thread via Python's Event Loop and `asyncio.start_server`.
2. **One Task per Client:** Each client runs inside an isolated coroutine task; idle or slow clients do not block or degrade performance for others.
3. **Safe Stream Framing:**
   - `readuntil(b"\r\n\r\n")` for asynchronous header extraction.
   - `readexactly(content_length)` for deterministic body reception according to the `Content-Length` header.
4. **Stateless Connection Model:** Each request is atomic and independent (`Connection: close`).

---

## 2. Message Wire Format

### 2.1 Request Format

An incoming request consists of:
1. **Request Line:** `<METHOD> <RESOURCE_PATH> <PROTOCOL_VERSION>\r\n`
2. **Headers:** One or more lines in `<Key>: <Value>\r\n` format.
3. **Header Terminator:** An empty line `\r\n`.
4. **Body:** UTF-8 encoded JSON string (optional for GET/DELETE, required for POST/PUT).

```http
POST /categories HTTP/1.1\r\n
Host: 127.0.0.1:8088\r\n
Accept: application/json\r\n
Content-Type: application/json; charset=utf-8\r\n
Content-Length: 29\r\n
\r\n
{"category_name": "Desserts"}
```

### 2.2 Response Format

An outgoing response consists of:
1. **Status Line:** `<PROTOCOL_VERSION> <STATUS_CODE> <STATUS_TEXT>\r\n`
2. **Headers:** Content metadata and payload length.
3. **Header Terminator:** An empty line `\r\n`.
4. **Body:** UTF-8 encoded JSON string.

```http
HTTP/1.1 201 Created\r\n
Connection: close\r\n
Content-Type: application/json; charset=utf-8\r\n
Content-Length: 38\r\n
\r\n
{"id": 4, "category_name": "Desserts"}
```

---

## 3. Status Codes and Error Handling

| Code | Status Text | Description |
| :--- | :--- | :--- |
| **200** | OK | Request processed successfully. Returns the requested JSON data. |
| **201** | Created | Resource created successfully in the database. Returns the newly created entity with its assigned ID. |
| **204** | No Content | Action executed successfully (e.g., DELETE). Returns no response body. |
| **400** | Bad Request | Client validation failure (e.g., empty name, negative price, duplicate unique key). |
| **404** | Not Found | Requested resource ID does not exist or route is unrecognized. |
| **408** | Request Timeout | Client exceeded `READ_TIMEOUT_SECONDS` (5s) before sending a complete HTTP request. |
| **413** | Payload Too Large | Request payload body exceeds the configured limit `MAX_BODY_SIZE` (1 MB). |
| **500** | Internal Server Error | Unhandled server exception during request processing. |
| **503** | Service Unavailable | Server at maximum concurrent capacity (`MAX_CONNECTIONS` reached) or unreachable. |

In the event of an error (4xx or 5xx), the response body consistently returns a JSON object with an `"error"` key:
```json
{
  "error": "Category name cannot be empty."
}
```

---

## 4. Supported Resources and Operations

### 4.1 Categories (`/categories`)

| Method | Path | Description | Request Body (JSON) | Response Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/categories` | List all categories | None | `200 OK` |
| `GET` | `/categories/{id}` | Retrieve category by ID | None | `200 OK` / `404` |
| `POST` | `/categories` | Create new category | `{"category_name": "string"}` | `201 Created` / `400` |
| `PUT` | `/categories/{id}` | Update category | `{"category_name": "string"}` | `200 OK` / `404` |
| `DELETE` | `/categories/{id}` | Delete category | None | `204 No Content` / `404` |

---

### 4.2 Allergens (`/allergens`)

| Method | Path | Description | Request Body (JSON) | Response Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/allergens` | List all allergens | None | `200 OK` |
| `GET` | `/allergens/{id}` | Retrieve allergen by ID | None | `200 OK` / `404` |
| `POST` | `/allergens` | Create new allergen | `{"allergen_name": "string"}` | `201 Created` / `400` |
| `PUT` | `/allergens/{id}` | Update allergen | `{"allergen_name": "string"}` | `200 OK` / `404` |
| `DELETE` | `/allergens/{id}` | Delete allergen | None | `204 No Content` / `404` |

---

### 4.3 Dishes (`/dishes`)

| Method | Path | Description | Request Body (JSON) | Response Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/dishes` | List dishes (supports `?active=true` or `?name=text`) | None | `200 OK` |
| `GET` | `/dishes/{id}` | Retrieve dish by ID (with N:M allergens) | None | `200 OK` / `404` |
| `POST` | `/dishes` | Create dish (1:N relationship with category) | `{"dish_name": "str", "id_category": int, "description": "str", "is_active": bool}` | `201 Created` / `400` |
| `PUT` | `/dishes/{id}` | Update dish attributes | JSON fields to update | `200 OK` / `404` |
| `DELETE` | `/dishes/{id}` | Delete dish | None | `204 No Content` / `404` |
| `POST` | `/dishes/{id}/allergens` | Add allergen to dish (N:M relationship) | `{"id_allergen": int}` | `200 OK` / `400` |

---

### 4.4 Employees (`/employees`)

| Method | Path | Description | Request Body (JSON) | Response Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/employees` | List employees (supports `?role=rol` or `?name=x&surname=y`) | None | `200 OK` |
| `GET` | `/employees/{id}` | Retrieve employee by ID | None | `200 OK` / `404` |
| `POST` | `/employees` | Create employee (and optional 1:1 credentials) | `{"name": "str", "surname": "str", "national_id": "str", "role": "str", "email": "str", "password": "str"}` | `201 Created` / `400` |
| `PUT` | `/employees/{id}` | Update employee | JSON fields to update | `200 OK` / `404` |
| `DELETE` | `/employees/{id}` | Delete employee (cascade deletion) | None | `204 No Content` / `404` |

---

### 4.5 Menus (`/menus`)

| Method | Path | Description | Request Body (JSON) | Response Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/menus` | List menus (supports `?name=x` or `?min_price=x&max_price=y`) | None | `200 OK` |
| `GET` | `/menus/{id}` | Retrieve menu by ID (with N:M dishes) | None | `200 OK` / `404` |
| `POST` | `/menus` | Create new menu | `{"menu_name": "string", "price": float}` | `201 Created` / `400` |
| `PUT` | `/menus/{id}` | Update menu | JSON fields to update | `200 OK` / `404` |
| `DELETE` | `/menus/{id}` | Delete menu | None | `204 No Content` / `404` |
| `POST` | `/menus/{id}/dishes` | Add dish to menu (N:M relationship) | `{"id_dish": int}` | `200 OK` / `400` |
| `DELETE` | `/menus/{id}/dishes/{dish_id}` | Remove dish from menu | None | `204 No Content` / `404` |

---

### 4.6 Sales (`/sales`)

| Method | Path | Description | Request Body (JSON) | Response Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/sales` | List sales (supports `?page=1`, `?date=YYYY-MM-DD`, `?employee_id=X`, `?menu_id=Y`, `?date_from=A&date_to=B`) | None | `200 OK` |
| `GET` | `/sales/{menu_id}/{emp_id}/{date}` | Retrieve sale by composite PK | None | `200 OK` / `404` |
| `POST` | `/sales` | Register sale (N:M with attributes) | `{"id_menu": int, "id_employee": int, "sale_date": "YYYY-MM-DD", "quantity_sold": int}` | `201 Created` / `400` |
| `PUT` | `/sales/{menu_id}/{emp_id}/{date}` | Update quantity sold | `{"quantity_sold": int}` | `200 OK` / `400` / `404` |
| `DELETE` | `/sales/{menu_id}/{emp_id}/{date}` | Delete sale by composite PK | None | `204 No Content` / `404` |

---

## 5. End-to-End CRUD Examples

### 5.1 Create Entity (POST /categories)
**Client Request:**
```
POST /categories HTTP/1.1
Host: 127.0.0.1:8088
Accept: application/json
Content-Type: application/json; charset=utf-8
Content-Length: 28

{"category_name": "Salads"}
```
**Server Response:**
```
HTTP/1.1 201 Created
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 37

{"id": 1, "category_name": "Salads"}
```

### 5.2 Read Entity / List (GET /dishes?active=true)
**Client Request:**
```
GET /dishes?active=true HTTP/1.1
Host: 127.0.0.1:8088
Accept: application/json
Connection: close
```
**Server Response:**
```
HTTP/1.1 200 OK
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 133

[{"id": 1, "dish_name": "Caesar Salad", "description": "Fresh lettuce & dressing", "is_active": true, "id_category": 1, "category_name": "Salads", "allergens": []}]
```

### 5.3 Update Entity (PUT /menus/1)
**Client Request:**
```
PUT /menus/1 HTTP/1.1
Host: 127.0.0.1:8088
Accept: application/json
Content-Type: application/json; charset=utf-8
Content-Length: 37

{"menu_name": "Lunch Menu", "price": 14.50}
```
**Server Response:**
```
HTTP/1.1 200 OK
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 57

{"id": 1, "menu_name": "Lunch Menu", "price": 14.5, "dishes": []}
```

### 5.4 Delete Entity (DELETE /allergens/3)
**Client Request:**
```
DELETE /allergens/3 HTTP/1.1
Host: 127.0.0.1:8088
Connection: close
```
**Server Response:**
```
HTTP/1.1 204 No Content
Connection: close
Content-Length: 0
```
