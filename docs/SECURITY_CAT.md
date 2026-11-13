# Pràctica 3: Seguretat i Criptografia (TLS 1.3 / OpenSSL / Content-Hash)

## 1. Generació del Certificat del Servidor a mà amb OpenSSL (amb SAN)

El servidor utilitza un certificat X.509 autosignat generat manualment amb **OpenSSL** a la carpeta `certs/`, incloent-hi l'extensió **Subject Alternative Name (SAN)** (`DNS:localhost,IP:127.0.0.1`) que exigeix la verificació de nom de Python:

```bash
mkdir -p certs

# 1. Generar la clau privada RSA-2048 (key.pem) i el certificat autosignat amb SAN (cert.pem)
MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout certs/key.pem -out certs/cert.pem -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

# 2. (Opcional) Empaquetar el certificat i la clau privada en un sol fitxer PKCS#12 (.p12)
openssl pkcs12 -export -out certs/server.p12 -inkey certs/key.pem -in certs/cert.pem -passout pass:1234
```

> Les claus i certificats (`certs/*.pem`, `certs/*.key`, `certs/*.p12`) estan exclosos a `.gitignore` per no pujar mai secrets al repositori.

---

## 2. Què fa TLS per nosaltres i com verifica el Client el Servidor

 Els clients només tenen una còpia pública de **`certs/cert.pem`** (`CLIENT_CA_FILE=certs/cert.pem`, mai la clau privada `key.pem`) i la passen com a certificat de confiança a `ssl.create_default_context(cafile=self.ca_file)`.

Quan el client es connecta al servidor (`server/server.py`), el handshake TLS executa **4 passos automàtics**:

1. **Autenticació del servidor (RSA / X.509):** El servidor envia `certs/cert.pem` i signa el handshake amb la seva clau privada `certs/key.pem`.
2. **Verificació al client (`cafile` + SAN):** El client verifica la signatura amb la clau pública de `cert.pem` i comprova que el `server_hostname` coincideixi amb el **SAN** (`DNS:localhost` o `IP:127.0.0.1`). Si el servidor és fals o el nom no coincideix, la connexió s'avorta amb `SSLCertVerificationError` abans d'enviar cap dada.
3. **Intercanvi de clau efímer ECDHE (Diffie-Hellman):** Client i servidor acorden una clau de sessió única per a aquella connexió sense que la clau viatgi mai per la xarxa.
4. **Xifratge simètric AES-GCM:** Tot el trànsit HTTP/JSON posterior viatja xifrat amb `TLS_AES_256_GCM_SHA384`.

Tant el servidor (`server/src/network/connection_handler.py`) com el client (`HttpClient.last_tls_info`) registren la sessió negociada:

```text
INFO server.src.network.connection_handler: TLS session with ('127.0.0.1', 54321): TLSv1.3, TLS_AES_256_GCM_SHA384
```

> **Nota sobre `_create_unverified_context()` i limitació d'identitat de client:**
> - L'enunciat permet l'ús de `ssl._create_unverified_context()`, però en aquest projecte s'ha optat per verificar el certificat del servidor amb `ssl.create_default_context(cafile=...)` perquè desactivar la verificació permetria un atac *man-in-the-middle* amb qualsevol certificat fals.
> - Els clients no tenen certificat propi (no fem mTLS), de manera que el servidor no identifica criptogràficament qui és cada client a la capa TLS; l'enunciat ho accepta explícitament per a l'arquitectura REST.

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
| **TLS al servidor amb certificat OpenSSL (amb SAN)** | `server/server.py` (`PROTOCOL_TLS_SERVER` + `load_cert_chain`) | `test_tls_client_verifies_server_certificate_and_connects` |
| **Verificació del certificat del servidor i SAN al client** | `client/src/protocol/http_client.py` (`create_default_context(cafile=...)`) | `test_client_rejects_untrusted_server_certificate`, `test_client_rejects_hostname_mismatch`, `test_http_client_returns_error_on_untrusted_certificate` |
| **Intercanvi de clau (ECDHE) i xifratge simètric AES-GCM** | `server/src/network/connection_handler.py` i `HttpClient.last_tls_info` | `test_tls_session_uses_tls13_and_aes_gcm` |
| **Rebuig de clients sense TLS (text pla)** | Capa TLS d'`asyncio.start_server(..., ssl=ssl_context)` | `test_plaintext_client_cannot_talk_to_tls_server` |
| **Digest SHA-256 obligatori en peticions amb cos** | `common/security/digest.py` + `server/src/protocol/async_request_reader.py` | `test_request_without_digest_is_rejected`, `test_request_with_tampered_digest_is_rejected` |
| **Digest SHA-256 obligatori en respostes amb cos** | `server/src/protocol/response_builder.py` + `decode_response` | `test_response_without_digest_is_integrity_error`, `test_response_content_hash_integrity_verification` |
| **Càlcul i verificació en temps constant (`compare_digest`)** | `common/security/digest.py` (`compute_digest`, `verify_digest`) | `test_digest_module_unit_behavior` |
