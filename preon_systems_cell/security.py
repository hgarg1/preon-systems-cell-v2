from __future__ import annotations

from typing import Any

from preon_systems_cell.models import DataClass


_SENSITIVE_KEYS = {
    "answer",
    "content",
    "input",
    "inputs",
    "output",
    "payload",
    "prompt",
    "raw_answer",
    "result",
    "secret",
    "token",
}


def bounded_redact(value: Any, data_class: DataClass, *, key: str | None = None) -> Any:
    if (
        data_class == DataClass.RESTRICTED
        and key is not None
        and key.lower() in _SENSITIVE_KEYS
    ):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(item_key): bounded_redact(item, data_class, key=str(item_key))
            for item_key, item in list(value.items())[:100]
        }
    if isinstance(value, list):
        return [bounded_redact(item, data_class) for item in value[:100]]
    if isinstance(value, tuple):
        return [bounded_redact(item, data_class) for item in value[:100]]
    if isinstance(value, str) and len(value) > 8_000:
        return value[:8_000] + "…[TRUNCATED]"
    return value
