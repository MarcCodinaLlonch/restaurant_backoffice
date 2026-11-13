# Practice 3: Security & Cryptography (TLS 1.3 / OpenSSL / Content-Hash)

## 1. Manual Server Certificate Generation with OpenSSL (with SAN)

The server uses a self-signed X.509 certificate generated manually with **OpenSSL** in the `certs/` directory, including the **Subject Alternative Name (SAN)** extension (`DNS:localhost,IP:127.0.0.1`) required by Python's hostname verification:

```bash
mkdir -p certs

# 1. Generate the RSA-2048 private key (key.pem) and self-signed certificate with SAN (cert.pem)
MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout certs/key.pem -out certs/cert.pem -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

# 2. (Optional) Bundle the certificate and private key into a single PKCS#12 (.p12) archive
openssl pkcs12 -export -out certs/server.p12 -inkey certs/key.pem -in certs/cert.pem -passout pass:1234
```

> Private keys and certificates (`certs/*.pem`, `certs/*.key`, `certs/*.p12`) are ignored in `.gitignore` so secrets are never committed to version control.

---

## 2. What TLS Does for Us and How the Client Verifies the Server

Clients only hold a public copy of **`certs/cert.pem`** (`CLIENT_CA_FILE=certs/cert.pem`, never the private key `key.pem`) and pass it as the trusted certificate to `ssl.create_default_context(cafile=self.ca_file)`.

When the client connects to the server (`server/server.py`), the TLS handshake performs **4 automatic steps**:

1. **Server Authentication (RSA / X.509):** The server sends `certs/cert.pem` and signs the handshake with its private key `certs/key.pem`.
2. **Client Verification (`cafile` + SAN):** The client verifies the signature using the public key in `cert.pem` and checks that `server_hostname` matches the **SAN** (`DNS:localhost` or `IP:127.0.0.1`). If the server is untrusted or the hostname mismatches, the connection is aborted with `SSLCertVerificationError` before any application data is sent.
3. **Ephemeral ECDHE Key Exchange (Diffie-Hellman):** Client and server negotiate a unique per-connection session key without the key ever travelling across the network.
4. **AES-GCM Symmetric Encryption:** All subsequent HTTP/JSON traffic is encrypted with `TLS_AES_256_GCM_SHA384`.

Both the server (`server/src/network/connection_handler.py`) and the client (`HttpClient.last_tls_info`) record the negotiated session parameters:

```text
INFO server.src.network.connection_handler: TLS session with ('127.0.0.1', 54321): TLSv1.3, TLS_AES_256_GCM_SHA384
```

> **Note on `_create_unverified_context()` and client identity limitation:**
> - The assignment allows `ssl._create_unverified_context()`, but we chose to verify the server certificate with `ssl.create_default_context(cafile=...)` because disabling verification would allow a *man-in-the-middle* attack with any forged certificate.
> - Clients do not have their own certificates (no mTLS), so the server does not cryptographically identify individual clients at the TLS layer; the assignment explicitly accepts this for the REST architecture.

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
| **Server TLS with OpenSSL certificate (with SAN)** | `server/server.py` (`PROTOCOL_TLS_SERVER` + `load_cert_chain`) | `test_tls_client_verifies_server_certificate_and_connects` |
| **Client verification of server certificate & SAN** | `client/src/protocol/http_client.py` (`create_default_context(cafile=...)`) | `test_client_rejects_untrusted_server_certificate`, `test_client_rejects_hostname_mismatch`, `test_http_client_returns_error_on_untrusted_certificate` |
| **Key exchange (ECDHE) & AES-GCM symmetric encryption** | `server/src/network/connection_handler.py` & `HttpClient.last_tls_info` | `test_tls_session_uses_tls13_and_aes_gcm` |
| **Reject plaintext (non-TLS) clients** | TLS layer in `asyncio.start_server(..., ssl=ssl_context)` | `test_plaintext_client_cannot_talk_to_tls_server` |
| **Mandatory SHA-256 digest on requests with body** | `common/security/digest.py` + `server/src/protocol/async_request_reader.py` | `test_request_without_digest_is_rejected`, `test_request_with_tampered_digest_is_rejected` |
| **Mandatory SHA-256 digest on responses with body** | `server/src/protocol/response_builder.py` + `decode_response` | `test_response_without_digest_is_integrity_error`, `test_response_content_hash_integrity_verification` |
| **Constant-time digest verification (`compare_digest`)** | `common/security/digest.py` (`compute_digest`, `verify_digest`) | `test_digest_module_unit_behavior` |
