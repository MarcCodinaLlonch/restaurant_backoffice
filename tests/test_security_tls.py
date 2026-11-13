"""
test_security_tls.py: Proves de la Pràctica 3 (TLS 1.3 + AES-GCM i digest SHA-256 obligatori).
"""

import asyncio
import ssl
import subprocess
from pathlib import Path

import pytest

from client.src.protocol.http_client import HttpClient, decode_response, encode_request
from common.security.digest import DIGEST_HEADER, compute_digest, verify_digest
from server.src.network import ClientConnectionHandler
from server.src.protocol.response_builder import ResponseBuilder

HOST = "127.0.0.1"


class FakeRouter:
    """Router síncron de prova per validar TLS i digest sense PostgreSQL."""

    def handle_request(self, request) -> bytes:
        if request.raw_path == "/categories" and request.method == "GET":
            return ResponseBuilder.ok([{"id": 1, "category_name": "Begudes"}])
        if request.raw_path == "/categories" and request.method == "POST":
            return ResponseBuilder.created({"id": 2, **request.body})
        return ResponseBuilder.not_found("Route not found")


@pytest.fixture(scope="module")
def sample_certs(tmp_path_factory) -> dict[str, Path]:
    """Genera cert.pem i key.pem temporals amb la mateixa comanda OpenSSL de classe."""
    cert_dir = tmp_path_factory.mktemp("certs")
    cert_pem = cert_dir / "cert.pem"
    key_pem = cert_dir / "key.pem"

    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            str(key_pem),
            "-out",
            str(cert_pem),
            "-days",
            "365",
            "-nodes",
            "-subj",
            "/CN=localhost",
        ],
        check=True,
        capture_output=True,
    )
    return {"cert": cert_pem, "key": key_pem}


@pytest.fixture
async def tls_server_port(sample_certs):
    """Arrenca el servidor amb ssl.PROTOCOL_TLS_SERVER carregant cert.pem i key.pem."""
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.load_cert_chain(
        certfile=str(sample_certs["cert"]),
        keyfile=str(sample_certs["key"]),
    )
    handler = ClientConnectionHandler(router=FakeRouter(), read_timeout=1.0, max_body_size=1024)
    server = await asyncio.start_server(handler.handle_client, HOST, 0, ssl=ssl_ctx)
    port = server.sockets[0].getsockname()[1]
    async with server:
        yield port


async def test_tls_client_with_unverified_context_connects_and_encrypts(tls_server_port: int):
    """El client amb ssl._create_unverified_context() es connecta al servidor TLS autosignat."""
    client = HttpClient(host=HOST, port=tls_server_port, timeout=2.0, use_ssl=True)
    response = await asyncio.to_thread(client.get, "/categories")
    assert response.is_success
    assert response.data == [{"id": 1, "category_name": "Begudes"}]
    assert client.last_tls_info is not None
    assert client.last_tls_info[0] == "TLSv1.3"


async def test_tls_session_uses_tls13_and_aes_gcm(tls_server_port: int):
    """La sessió TLS negocia TLSv1.3 (ECDHE) i xifratge simètric AES-GCM."""
    ssl_ctx = ssl._create_unverified_context()
    reader, writer = await asyncio.open_connection(HOST, tls_server_port, ssl=ssl_ctx)
    try:
        ssl_obj = writer.get_extra_info("ssl_object")
        assert ssl_obj is not None
        assert ssl_obj.version() == "TLSv1.3"
        cipher_info = ssl_obj.cipher()
        assert cipher_info is not None
        cipher_name = cipher_info[0]
        assert "AES" in cipher_name and "GCM" in cipher_name
    finally:
        writer.close()
        await writer.wait_closed()


async def test_request_without_digest_is_rejected(tls_server_port: int):
    """Un POST amb cos i sense capçalera Content-Hash és rebutjat amb 400 Bad Request."""
    ssl_ctx = ssl._create_unverified_context()
    body = b'{"name": "Entrants"}'
    raw_req = (
        f"POST /categories HTTP/1.1\r\n"
        f"Host: {HOST}:{tls_server_port}\r\n"
        f"Content-Type: application/json; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n\r\n"
    ).encode("utf-8") + body

    reader, writer = await asyncio.open_connection(HOST, tls_server_port, ssl=ssl_ctx)
    writer.write(raw_req)
    await writer.drain()
    raw_resp = await reader.read()
    writer.close()
    await writer.wait_closed()

    decoded = decode_response(raw_resp)
    assert decoded.status_code == 400
    assert "falta la capçalera" in (decoded.error_message or "")


async def test_request_with_tampered_digest_is_rejected(tls_server_port: int):
    """El servidor accepta peticions amb digest vàlid i rebutja amb 400 si el cos s'altera."""
    ssl_ctx = ssl._create_unverified_context()

    # 1. Petició POST vàlida
    valid_req = encode_request("POST", "/categories", HOST, tls_server_port, {"name": "Entrants"})
    assert f"{DIGEST_HEADER}: ".encode() in valid_req

    reader, writer = await asyncio.open_connection(HOST, tls_server_port, ssl=ssl_ctx)
    writer.write(valid_req)
    await writer.drain()
    raw_resp = await reader.read()
    writer.close()
    await writer.wait_closed()
    assert decode_response(raw_resp).status_code == 201

    # 2. Petició amb el cos modificat però mantenint el digest antic -> 400 Bad Request
    tampered_req = valid_req.replace(b'"Entrants"', b'" Pirata "')
    reader, writer = await asyncio.open_connection(HOST, tls_server_port, ssl=ssl_ctx)
    writer.write(tampered_req)
    await writer.drain()
    raw_tampered_resp = await reader.read()
    writer.close()
    await writer.wait_closed()
    decoded_err = decode_response(raw_tampered_resp)
    assert decoded_err.status_code == 400
    assert "no coincideix" in (decoded_err.error_message or "")


def test_response_without_digest_is_integrity_error():
    """decode_response rebutja una resposta amb cos si li falta la capçalera de digest."""
    body = b'{"status":"ok"}'
    raw_no_digest = (
        f"HTTP/1.1 200 OK\r\nContent-Length: {len(body)}\r\n\r\n".encode("utf-8") + body
    )
    resp = decode_response(raw_no_digest)
    assert resp.status_code == 500
    assert "falta la capçalera" in (resp.error_message or "")


def test_response_content_hash_integrity_verification():
    """decode_response verifica el digest de la resposta i detecta si s'ha manipulat."""
    body = b'{"status":"ok"}'
    good_hash = compute_digest(body)
    raw_good = (
        f"HTTP/1.1 200 OK\r\nContent-Length: {len(body)}\r\n{DIGEST_HEADER}: {good_hash}\r\n\r\n"
    ).encode("utf-8") + body
    assert decode_response(raw_good).is_success

    raw_bad = (
        f"HTTP/1.1 200 OK\r\nContent-Length: {len(body)}\r\n{DIGEST_HEADER}: {'0' * 64}\r\n\r\n"
    ).encode("utf-8") + body
    bad_resp = decode_response(raw_bad)
    assert bad_resp.status_code == 500
    assert "no coincideix" in (bad_resp.error_message or "")


async def test_plaintext_client_cannot_talk_to_tls_server(tls_server_port: int):
    """Un client TCP sense TLS que envia HTTP en clar no rep cap resposta HTTP vàlida."""
    reader, writer = await asyncio.open_connection(HOST, tls_server_port)
    try:
        writer.write(b"GET /categories HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()
        try:
            raw = await reader.read()
        except ConnectionError:
            raw = b""
        assert not raw.startswith(b"HTTP/1.1")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionError:
            pass


def test_digest_module_unit_behavior():
    """Proves unitàries de compute_digest i verify_digest (common/security/digest.py)."""
    payload = b'{"dish_name": "Paella"}'
    altered = b'{"dish_name": "Paello"}'

    digest1 = compute_digest(payload)
    digest2 = compute_digest(payload)
    assert digest1 == digest2
    assert compute_digest(altered) != digest1

    assert verify_digest(payload, digest1) is True
    assert verify_digest(payload, digest1.upper()) is True
    assert verify_digest(payload, f"  {digest1}  ") is True
    assert verify_digest(payload, None) is False
    assert verify_digest(payload, "") is False
    assert verify_digest(payload, "   ") is False
    assert verify_digest(payload, compute_digest(altered)) is False
