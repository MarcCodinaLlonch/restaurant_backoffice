"""
Tests per al lector asíncron de peticions HTTP (read_request).
Comprova casos d'èxit, desconnexió neta, timeouts, capçaleres incompletes i límits de seguretat.
"""

import asyncio

import pytest

from server.src.protocol.async_request_reader import read_request
from server.src.protocol.errors import PayloadTooLargeError, ProtocolError
from server.src.protocol.response_builder import ResponseBuilder


@pytest.mark.asyncio
async def test_read_request_get_without_body():
    """Comprova la lectura d'un GET senzill sense cos."""
    reader = asyncio.StreamReader()
    reader.feed_data(b"GET /categories HTTP/1.1\r\nHost: localhost\r\n\r\n")
    reader.feed_eof()

    req = await read_request(reader)
    assert req is not None
    assert req.method == "GET"
    assert req.raw_path == "/categories"
    assert req.headers["host"] == "localhost"
    assert req.body is None


@pytest.mark.asyncio
async def test_read_request_post_with_json_body():
    """Comprova la lectura d'un POST amb cos JSON delimitat per Content-Length."""
    body_json = b'{"name": "Begudes"}'
    raw_data = (
        b"POST /categories HTTP/1.1\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: " + str(len(body_json)).encode() + b"\r\n\r\n" + body_json
    )
    reader = asyncio.StreamReader()
    reader.feed_data(raw_data)
    reader.feed_eof()

    req = await read_request(reader)
    assert req is not None
    assert req.method == "POST"
    assert req.body == {"name": "Begudes"}


@pytest.mark.asyncio
async def test_read_request_clean_eof_returns_none():
    """Si el client connecta i tanca netament sense enviar cap byte, retorna None."""
    reader = asyncio.StreamReader()
    reader.feed_eof()

    req = await read_request(reader)
    assert req is None


@pytest.mark.asyncio
async def test_read_request_incomplete_headers_raises_protocol_error():
    """Si el client tanca a mitges les capçaleres, ha de llançar ProtocolError."""
    reader = asyncio.StreamReader()
    reader.feed_data(b"GET /dishes HTT")
    reader.feed_eof()

    with pytest.raises(ProtocolError):
        await read_request(reader)


@pytest.mark.asyncio
async def test_read_request_body_exceeds_max_limit():
    """Si el Content-Length supera el límit configurat, ha de llançar PayloadTooLargeError."""
    reader = asyncio.StreamReader()
    reader.feed_data(b"POST /upload HTTP/1.1\r\nContent-Length: 500\r\n\r\n")
    reader.feed_eof()

    with pytest.raises(PayloadTooLargeError):
        await read_request(reader, max_body_size=100)


@pytest.mark.asyncio
async def test_read_request_invalid_content_length():
    """Si el Content-Length conté caràcters no numèrics o negatius, ha de llançar ProtocolError."""
    reader = asyncio.StreamReader()
    reader.feed_data(b"POST /dishes HTTP/1.1\r\nContent-Length: invalid\r\n\r\n")
    reader.feed_eof()

    with pytest.raises(ProtocolError):
        await read_request(reader)


def test_response_builder_new_status_codes():
    """Comprova que els nous codis d'error HTTP es generen segons l'estàndard."""
    resp_408 = ResponseBuilder.request_timeout()
    assert b"HTTP/1.1 408 Request Timeout" in resp_408
    assert b"Temps d'espera esgotat" in resp_408

    resp_413 = ResponseBuilder.payload_too_large()
    assert b"HTTP/1.1 413 Payload Too Large" in resp_413

    resp_503 = ResponseBuilder.service_unavailable()
    assert b"HTTP/1.1 503 Service Unavailable" in resp_503
