# response_builder.py: construeix les respostes HTTP (codi, capçaleres i JSON) en bytes.

import hashlib
import json
from typing import Any


class ResponseBuilder:
    """
    Construeix cadenes de bytes seguint el protocol HTTP/1.1 per retornar al client.
    """

    @staticmethod
    def _serialize_data(data: Any) -> Any:
        """
        Funció auxiliar que converteix entitats de domini (que tinguin 'to_dict()')
        o llistes d'entitats en diccionaris i llistes serialitzables a JSON.
        """
        # CLAU: crida to_dict() d'entitats de common/ (on el servidor les usa per respondre);
        # també accepta llistes i diccionaris.
        if data is None:
            return None
        if hasattr(data, "to_dict") and callable(data.to_dict):
            return data.to_dict()
        if isinstance(data, list):
            return [ResponseBuilder._serialize_data(item) for item in data]
        if isinstance(data, dict):
            return {k: ResponseBuilder._serialize_data(v) for k, v in data.items()}
        return data

    @staticmethod
    def build(status_code: int, status_text: str, data: Any = None) -> bytes:
        """
        Construeix una resposta HTTP completa amb codi d'estat, capçaleres i cos JSON.
        """
        headers = [
            f"HTTP/1.1 {status_code} {status_text}",
            "Connection: close",
        ]

        if data is not None and status_code != 204:
            clean_data = ResponseBuilder._serialize_data(data)
            # ensure_ascii=False per mantenir caràcters catalans com à, è, ç, ·
            json_bytes = json.dumps(clean_data, ensure_ascii=False).encode("utf-8")
            body_hash = hashlib.sha256(json_bytes).hexdigest()
            headers.append("Content-Type: application/json; charset=utf-8")
            # CLAU: Content-Length es calcula sobre els BYTES de json_bytes, no sobre caràcters.
            headers.append(f"Content-Length: {len(json_bytes)}")
            # CLAU (Pràctica 3): Content-Hash (SHA-256) garanteix la integritat del cos JSON.
            headers.append(f"Content-Hash: {body_hash}")
            # Unim les capçaleres amb \r\n, afegim línia buida final i el cos de bytes
            # CLAU: estructura HTTP: línia d'estat + capçaleres + línia buida (\r\n\r\n) + cos.
            header_str = "\r\n".join(headers) + "\r\n\r\n"
            return header_str.encode("utf-8") + json_bytes
        else:
            # CLAU: branca sense cos (ex: 204 No Content): sense Content-Type i Content-Length 0.
            headers.append("Content-Length: 0")
            header_str = "\r\n".join(headers) + "\r\n\r\n"
            return header_str.encode("utf-8")

    @staticmethod
    def ok(data: Any = None) -> bytes:
        """200 OK: Petició resolta amb èxit."""
        return ResponseBuilder.build(200, "OK", data)

    @staticmethod
    def created(data: Any = None) -> bytes:
        """201 Created: S'ha creat un nou recurs a la base de dades."""
        return ResponseBuilder.build(201, "Created", data)

    @staticmethod
    def no_content() -> bytes:
        """204 No Content: L'acció s'ha realitzat (ex: eliminació) i no hi ha dades de retorn."""
        return ResponseBuilder.build(204, "No Content", None)

    @staticmethod
    def bad_request(message: str) -> bytes:
        """400 Bad Request: Dades invàlides del client (ex: nom buit, tipus incorrecte)."""
        return ResponseBuilder.build(400, "Bad Request", {"error": message})

    @staticmethod
    def not_found(message: str = "Recurs no trobat") -> bytes:
        """404 Not Found: El recurs sol·licitat no existeix."""
        return ResponseBuilder.build(404, "Not Found", {"error": message})

    @staticmethod
    def internal_error(message: str = "Error intern del servidor") -> bytes:
        """500 Internal Server Error: Excepció inesperada al servidor."""
        return ResponseBuilder.build(500, "Internal Server Error", {"error": message})

    @staticmethod
    def request_timeout(message: str = "Temps d'espera esgotat") -> bytes:
        """408 Request Timeout: El client ha trigat massa a transmetre la petició."""
        return ResponseBuilder.build(408, "Request Timeout", {"error": message})

    @staticmethod
    def payload_too_large(message: str = "Cos de la petició massa gran") -> bytes:
        """413 Payload Too Large: El body de la petició supera el límit permès."""
        return ResponseBuilder.build(413, "Payload Too Large", {"error": message})
