from __future__ import annotations

_STATUSES: dict[int, tuple[str, str]] = {
    100: ("Continue", "1xx Informational"),
    101: ("Switching Protocols", "1xx Informational"),
    102: ("Processing", "1xx Informational"),
    200: ("OK", "2xx Success"),
    201: ("Created", "2xx Success"),
    202: ("Accepted", "2xx Success"),
    204: ("No Content", "2xx Success"),
    206: ("Partial Content", "2xx Success"),
    301: ("Moved Permanently", "3xx Redirection"),
    302: ("Found", "3xx Redirection"),
    303: ("See Other", "3xx Redirection"),
    304: ("Not Modified", "3xx Redirection"),
    307: ("Temporary Redirect", "3xx Redirection"),
    308: ("Permanent Redirect", "3xx Redirection"),
    400: ("Bad Request", "4xx Client Error"),
    401: ("Unauthorized", "4xx Client Error"),
    403: ("Forbidden", "4xx Client Error"),
    404: ("Not Found", "4xx Client Error"),
    405: ("Method Not Allowed", "4xx Client Error"),
    408: ("Request Timeout", "4xx Client Error"),
    409: ("Conflict", "4xx Client Error"),
    410: ("Gone", "4xx Client Error"),
    415: ("Unsupported Media Type", "4xx Client Error"),
    422: ("Unprocessable Entity", "4xx Client Error"),
    429: ("Too Many Requests", "4xx Client Error"),
    500: ("Internal Server Error", "5xx Server Error"),
    501: ("Not Implemented", "5xx Server Error"),
    502: ("Bad Gateway", "5xx Server Error"),
    503: ("Service Unavailable", "5xx Server Error"),
    504: ("Gateway Timeout", "5xx Server Error"),
    505: ("HTTP Version Not Supported", "5xx Server Error"),
}

_CATEGORIES = {1: "1xx Informational", 2: "2xx Success", 3: "3xx Redirection", 4: "4xx Client Error", 5: "5xx Server Error"}


def lookup(payload: dict) -> dict:
    code = int(payload.get("code", 0))
    if code in _STATUSES:
        meaning, category = _STATUSES[code]
        return {"meaning": meaning, "category": category, "code": code}
    category = _CATEGORIES.get(code // 100, "Unknown")
    return {"meaning": "Unknown", "category": category, "code": code}
