# Pràctica 3: Seguretat i Criptografia (TLS / OpenSSL / Content-Hash)

## 1. Generació del Certificat del Servidor a mà amb OpenSSL

El servidor utilitza un certificat X.509 autosignat generat manualment amb **OpenSSL** a la carpeta `certs/`:

```bash
mkdir -p certs

# 1. Generar la clau privada RSA-4096 (key.pem) i el certificat autosignat (cert.pem)
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"

# 2. (Opcional) Empaquetar el certificat i la clau privada en un sol fitxer PKCS#12 (.p12)
openssl pkcs12 -export -out certs/server.p12 -inkey certs/key.pem -in certs/cert.pem -passout pass:1234
```

> Les claus privades (`certs/*.pem`, `certs/*.key`, `certs/*.p12`) estan excloses a `.gitignore` per no pujar mai secrets al repositori.

---

## 2. Xifratge TLS al Servidor i al Client (`ssl`)

### Servidor (`server/server.py`)
El servidor crea un context `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)` i carrega el certificat (`cert.pem` + `key.pem`), passant `ssl=ssl_context` a `asyncio.start_server`:

```python
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="certs/cert.pem", keyfile="certs/key.pem")
server = await asyncio.start_server(handler.handle_client, SERVER_HOST, SERVER_PORT, ssl=context)
```

### Client (`client/src/protocol/http_client.py` i `client/load_test_client.py`)
Com que el certificat del servidor és autosignat (*self-signed*), el client crea el context amb `ssl._create_unverified_context()` i embolcalla el socket TCP abans de connectar-se:

```python
context = ssl._create_unverified_context()
sock = context.wrap_socket(raw_sock, server_hostname=self.host)
```

---

## 3. Delimitació (`Content-Length`) vs. Integritat (`Content-Hash`)

En el protocol HTTP/1.1 del projecte s'utilitzen dues capçaleres complementàries per al cos JSON:

| Capçalera | Funció | Com es calcula |
| :--- | :--- | :--- |
| **`Content-Length`** | **Delimitació (Framing):** Indica quants bytes exactes ha de llegir el receptor (`reader.readexactly(content_length)`). | `len(body_bytes)` |
| **`Content-Hash`** | **Integritat (SHA-256):** Verifica que els bytes del cos JSON no s'han corromput ni modificat. | `hashlib.sha256(body_bytes).hexdigest()` |

Si el `Content-Hash` rebut pel servidor no coincideix amb el SHA-256 real del cos, el servidor rebutja la petició amb **`400 Bad Request`**.
