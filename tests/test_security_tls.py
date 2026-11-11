"""
test_security_tls.py: Proves de la Pràctica 3 (TLS/SSL amb certificat autosignat i Content-Hash).
"""

import asyncio
import hashlib
import ssl
import subprocess
from pathlib import Path

import pytest

from client.src.protocol.http_client import HttpClient, decode_response, encode_request
from server.src.network import ClientConnectionHandler
from server.src.protocol.response_builder import ResponseBuilder

HOST = "127.0.0.1"


class FakeRouter:
    """Router síncron de prova per validar TLS i Content-Hash sense PostgreSQL."""

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


async def test_content_hash_valid_and_tampered_request(tls_server_port: int):
    """El servidor accepta peticions amb Content-Hash vàlid i rebutja amb 400 si s'altera."""
    ssl_ctx = ssl._create_unverified_context()

    # 1. Petició POST vàlida (encode_request calcula Content-Length i Content-Hash SHA-256)
    valid_req = encode_request("POST", "/categories", HOST, tls_server_port, {"name": "Entrants"})
    assert b"Content-Hash: " in valid_req

    reader, writer = await asyncio.open_connection(HOST, tls_server_port, ssl=ssl_ctx)
    writer.write(valid_req)
    await writer.drain()
    raw_resp = await reader.read()
    writer.close()
    await writer.wait_closed()
    assert decode_response(raw_resp).status_code == 201

    # 2. Petició amb el cos modificat però mantenint el Content-Hash antic -> 400 Bad Request
    tampered_req = valid_req.replace(b'"Entrants"', b'" Pirata "')
    reader, writer = await asyncio.open_connection(HOST, tls_server_port, ssl=ssl_ctx)
    writer.write(tampered_req)
    await writer.drain()
    raw_tampered_resp = await reader.read()
    writer.close()
    await writer.wait_closed()
    decoded_err = decode_response(raw_tampered_resp)
    assert decoded_err.status_code == 400
    assert "Content-Hash" in (decoded_err.error_message or "")


def test_response_content_hash_integrity_verification():
    """decode_response verifica el Content-Hash de la resposta i detecta si s'ha manipulat."""
    body = b'{"status":"ok"}'
    good_hash = hashlib.sha256(body).hexdigest()
    raw_good = (
        f"HTTP/1.1 200 OK\r\nContent-Length: {len(body)}\r\nContent-Hash: {good_hash}\r\n\r\n"
    ).encode("utf-8") + body
    assert decode_response(raw_good).is_success

    raw_bad = (
        f"HTTP/1.1 200 OK\r\nContent-Length: {len(body)}\r\nContent-Hash: {'0' * 64}\r\n\r\n"
    ).encode("utf-8") + body
    bad_resp = decode_response(raw_bad)
    assert bad_resp.status_code == 500
    assert "Content-Hash" in (bad_resp.error_message or "")
