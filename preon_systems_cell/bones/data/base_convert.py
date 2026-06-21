from __future__ import annotations

_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


def convert(payload: dict) -> dict:
    value = str(payload.get("value", ""))
    try:
        from_base = int(payload.get("from_base", 10))
        to_base = int(payload.get("to_base", 10))
    except (ValueError, TypeError) as exc:
        return {"error": str(exc)}
    if not (2 <= from_base <= 36):
        return {"error": f"from_base must be 2–36, got {from_base}"}
    if not (2 <= to_base <= 36):
        return {"error": f"to_base must be 2–36, got {to_base}"}
    try:
        decimal = int(value, from_base)
    except ValueError:
        return {"error": f"{value!r} is not valid in base {from_base}"}
    if decimal == 0:
        return {"result": "0"}
    negative = decimal < 0
    decimal = abs(decimal)
    parts: list[str] = []
    while decimal:
        parts.append(_DIGITS[decimal % to_base])
        decimal //= to_base
    if negative:
        parts.append("-")
    return {"result": "".join(reversed(parts))}
