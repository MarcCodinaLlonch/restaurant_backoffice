# Practice 3: Security & Cryptography (TLS 1.3 / OpenSSL / Content-Hash)

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

## 2. What TLS Does for Us (`ssl`)

When the server (`ssl.PROTOCOL_TLS_SERVER` in `server/server.py`) and the client (`ssl._create_unverified_context()` in `client/src/protocol/http_client.py`) establish a TLS connection, the protocol automatically performs three cryptographic steps:

1. **Server Certificate (RSA / X.509):** The server presents `certs/cert.pem` and proves possession of `certs/key.pem`.
2. **Ephemeral ECDHE Key Exchange (Elliptic-Curve Diffie-Hellman):** Client and server negotiate a unique per-connection session key with *Forward Secrecy*.
3. **AES-GCM Symmetric Encryption:** All subsequent HTTP/REST traffic is encrypted and authenticated using `TLS_AES_256_GCM_SHA384`.

Both the server (`server/src/network/connection_handler.py`) and the client (`HttpClient.last_tls_info`) record the negotiated protocol version and cipher suite:

```text
INFO server.src.network.connection_handler: TLS session with ('127.0.0.1', 54321): TLSv1.3, TLS_AES_256_GCM_SHA384
```

---

## 3. Framing (`Content-Length`) and Mandatory Integrity (`Content-Hash`)

All SHA-256 digest logic is centralized in **`common/security/digest.py`** (`DIGEST_HEADER = "Content-Hash"`, `compute_digest`, and `verify_digest`).

| Header | Role | Computation / Verification |
| :--- | :--- | :--- |
| **`Content-Length`** | **Framing / Sizing:** Tells the receiver the exact number of bytes to read (`reader.readexactly(content_length)`). | `len(body_bytes)` |
| **`Content-Hash`** | **Mandatory Integrity (SHA-256):** Verifies that the JSON payload bytes were not altered. | `compute_digest(body)` (`hashlib.sha256`) and `verify_digest(body, received)` using constant-time **`hmac.compare_digest`**. |

- **Mandatory on both sides:** Every request or response with a body (`Content-Length > 0`) must include `Content-Hash`. If the header is missing or does not match the payload, the server replies with **`400 Bad Request`** and the client returns an integrity error `ApiResponse`.

---

## 4. Summary: Requirement → Implementation → Test

| Assignment Requirement | Where It Is Implemented | Verifying Test (`tests/test_security_tls.py`) |
| :--- | :--- | :--- |
| **Server TLS with OpenSSL certificate** | `server/server.py` (`PROTOCOL_TLS_SERVER` + `load_cert_chain`) | `test_tls_client_with_unverified_context_connects_and_encrypts` |
| **Client TLS with `_create_unverified_context()`** | `client/src/protocol/http_client.py` & `client/load_test_client.py` | `test_tls_client_with_unverified_context_connects_and_encrypts` |
| **Key exchange (ECDHE) & AES-GCM symmetric encryption** | `server/src/network/connection_handler.py` & `HttpClient.last_tls_info` | `test_tls_session_uses_tls13_and_aes_gcm` |
| **Reject plaintext (non-TLS) clients** | TLS layer in `asyncio.start_server(..., ssl=ssl_context)` | `test_plaintext_client_cannot_talk_to_tls_server` |
| **Mandatory SHA-256 digest on requests with body** | `common/security/digest.py` + `server/src/protocol/async_request_reader.py` | `test_request_without_digest_is_rejected`, `test_request_with_tampered_digest_is_rejected` |
| **Mandatory SHA-256 digest on responses with body** | `server/src/protocol/response_builder.py` + `decode_response` | `test_response_without_digest_is_integrity_error`, `test_response_content_hash_integrity_verification` |
| **Constant-time digest verification (`compare_digest`)** | `common/security/digest.py` (`compute_digest`, `verify_digest`) | `test_digest_module_unit_behavior` |
