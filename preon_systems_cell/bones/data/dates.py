from __future__ import annotations

from datetime import date, datetime, timezone


def diff(payload: dict) -> dict:
    try:
        a = date.fromisoformat(str(payload.get("date_a", "")))
        b = date.fromisoformat(str(payload.get("date_b", "")))
        return {"days": (b - a).days}
    except (ValueError, TypeError) as exc:
        return {"error": str(exc)}


def convert_timestamp(payload: dict) -> dict:
    value = str(payload.get("value", ""))
    try:
        epoch = int(value)
        dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
        return {"epoch": epoch, "iso": dt.isoformat()}
    except ValueError:
        pass
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return {"epoch": int(dt.timestamp()), "iso": dt.isoformat()}
    except (ValueError, Exception) as exc:
        return {"error": str(exc)}
