# Practice 3: Security & Cryptography (TLS / OpenSSL / Content-Hash)

## 1. Manual Server Certificate Generation with OpenSSL

The server uses a self-signed X.509 certificate generated manually with **OpenSSL** in the `certs/` directory:

```bash
mkdir -p certs

# 1. Generate the RSA-4096 private key (key.pem) and self-signed certificate (cert.pem)
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"

# 2. (Optional) Bundle the certificate and private key into a single PKCS#12 (.p12) archive
openssl pkcs12 -export -out certs/server.p12 -inkey certs/key.pem -in certs/cert.pem -passout pass:1234
```

> Private keys (`certs/*.pem`, `certs/*.key`, `certs/*.p12`) are ignored in `.gitignore` so secrets are never committed to version control.

---

## 2. TLS Encryption on Server and Client (`ssl`)

### Server (`server/server.py`)
The server creates an `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)` context and loads the certificate (`cert.pem` + `key.pem`), passing `ssl=ssl_context` to `asyncio.start_server`:

```python
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="certs/cert.pem", keyfile="certs/key.pem")
server = await asyncio.start_server(handler.handle_client, SERVER_HOST, SERVER_PORT, ssl=context)
```

### Client (`client/src/protocol/http_client.py` and `client/load_test_client.py`)
Because the server certificate is self-signed, the client creates an unverified SSL context with `ssl._create_unverified_context()` and wraps the TCP socket before connecting:

```python
context = ssl._create_unverified_context()
sock = context.wrap_socket(raw_sock, server_hostname=self.host)
```

---

## 3. Framing (`Content-Length`) vs. Integrity (`Content-Hash`)

The HTTP/1.1 protocol uses two complementary headers whenever a JSON body is sent:

| Header | Role | Computation |
| :--- | :--- | :--- |
| **`Content-Length`** | **Framing / Sizing:** Tells the receiver the exact number of bytes to read (`reader.readexactly(content_length)`). | `len(body_bytes)` |
| **`Content-Hash`** | **Integrity (SHA-256):** Verifies that the JSON payload bytes were not corrupted or tampered with. | `hashlib.sha256(body_bytes).hexdigest()` |

If the `Content-Hash` received by the server does not match the actual SHA-256 of the body, the server rejects the request with **`400 Bad Request`**.
