# Pràctica 3: Seguretat i Criptografia (TLS 1.3 / OpenSSL / Content-Hash)

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

## 2. Què fa TLS per nosaltres (`ssl`)

Quan el servidor (`ssl.PROTOCOL_TLS_SERVER` a `server/server.py`) i el client (`ssl._create_unverified_context()` a `client/src/protocol/http_client.py`) estableixen la connexió TLS, el protocol realitza automàticament les tres fases criptogràfiques:

1. **Certificat del servidor (RSA / X.509):** El servidor presenta `certs/cert.pem` i demostra que posseeix la clau privada `certs/key.pem`.
2. **Intercanvi de clau efímer ECDHE (Diffie-Hellman sobre corba el·líptica):** Client i servidor acorden una clau de sessió única per a aquella connexió amb *Forward Secrecy*.
3. **Xifratge simètric AES-GCM:** Tot el trànsit HTTP/REST posterior viatja xifrat i autenticat amb `TLS_AES_256_GCM_SHA384`.

Tant el servidor (`server/src/network/connection_handler.py`) com el client (`HttpClient.last_tls_info`) registren la versió i el xifratge negociats:

```text
INFO server.src.network.connection_handler: TLS session with ('127.0.0.1', 54321): TLSv1.3, TLS_AES_256_GCM_SHA384
```

---

## 3. Delimitació (`Content-Length`) i Integritat Obligatòria (`Content-Hash`)

Tota la lògica del digest SHA-256 està centralitzada a **`common/security/digest.py`** (`DIGEST_HEADER = "Content-Hash"`, `compute_digest` i `verify_digest`).

| Capçalera | Funció | Com es calcula / verifica |
| :--- | :--- | :--- |
| **`Content-Length`** | **Delimitació (Framing):** Indica quants bytes exactes ha de llegir el receptor (`reader.readexactly(content_length)`). | `len(body_bytes)` |
| **`Content-Hash`** | **Integritat obligatòria (SHA-256):** Verifica que els bytes del cos JSON no s'han alterat. | `compute_digest(body)` (`hashlib.sha256`) i `verify_digest(body, received)` amb **`hmac.compare_digest`** (temps constant). |

- **Obligatori als dos costats:** Tota petició o resposta amb cos (`Content-Length > 0`) ha d'incloure `Content-Hash`. Si falta la capçalera o el digest no coincideix, el servidor respon amb **`400 Bad Request`** i el client retorna un `ApiResponse` d'error d'integritat.

---

## 4. Resum: Requisit → Implementació → Test

| Requisit de l'enunciat | On està implementat | Test que ho demostra (`tests/test_security_tls.py`) |
| :--- | :--- | :--- |
| **TLS al servidor amb certificat OpenSSL** | `server/server.py` (`PROTOCOL_TLS_SERVER` + `load_cert_chain`) | `test_tls_client_with_unverified_context_connects_and_encrypts` |
| **Client TLS amb `_create_unverified_context()`** | `client/src/protocol/http_client.py` i `client/load_test_client.py` | `test_tls_client_with_unverified_context_connects_and_encrypts` |
| **Intercanvi de clau (ECDHE) i xifratge simètric AES-GCM** | `server/src/network/connection_handler.py` i `HttpClient.last_tls_info` | `test_tls_session_uses_tls13_and_aes_gcm` |
| **Rebuig de clients sense TLS (text pla)** | Capa TLS d'`asyncio.start_server(..., ssl=ssl_context)` | `test_plaintext_client_cannot_talk_to_tls_server` |
| **Digest SHA-256 obligatori en peticions amb cos** | `common/security/digest.py` + `server/src/protocol/async_request_reader.py` | `test_request_without_digest_is_rejected`, `test_request_with_tampered_digest_is_rejected` |
| **Digest SHA-256 obligatori en respostes amb cos** | `server/src/protocol/response_builder.py` + `decode_response` | `test_response_without_digest_is_integrity_error`, `test_response_content_hash_integrity_verification` |
| **Càlcul i verificació en temps constant (`compare_digest`)** | `common/security/digest.py` (`compute_digest`, `verify_digest`) | `test_digest_module_unit_behavior` |
