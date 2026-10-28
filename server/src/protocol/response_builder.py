# response_builder.py: Generador de respostes HTTP sobre TCP.
#
# CONCEPTE CLAU PER A DAM (Estructura de la Resposta HTTP/1.1):
# Una resposta HTTP vàlida conté:
# 1. Línia d'estat: 'HTTP/1.1 <CODI> <MISSATGE>\r\n' (ex: HTTP/1.1 200 OK)
# 2. Capçaleres clau-valor amb la seva terminació CRLF: '\r\n'
# 3. Una línia buida CRLF ('\r\n') que marca el final de les capçaleres.
# 4. El cos (body) de dades, normalment JSON serialitzat en UTF-8.

import json
from typing import Any, Optional


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
        if data is None:
            return None
        if hasattr(data, "to_dict") and callable(getattr(data, "to_dict")):
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
            headers.append("Content-Type: application/json; charset=utf-8")
            headers.append(f"Content-Length: {len(json_bytes)}")
            # Unim les capçaleres amb \r\n, afegim línia buida final i el cos de bytes
            header_str = "\r\n".join(headers) + "\r\n\r\n"
            return header_str.encode("utf-8") + json_bytes
        else:
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
        """400 Bad Request: Dades invàlides enviades pel client (ex: nom buit, tipus incorrecte)."""
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

    @staticmethod
    def service_unavailable(message: str = "Servei no disponible temporalment") -> bytes:
        """503 Service Unavailable: El servidor ha assolit el límit màxim de connexions."""
        return ResponseBuilder.build(503, "Service Unavailable", {"error": message})