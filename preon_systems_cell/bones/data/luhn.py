from __future__ import annotations


def check(payload: dict) -> dict:
    card_number = str(payload.get("card_number", "")).replace(" ", "").replace("-", "")
    digits = [int(c) for c in card_number if c.isdigit()]
    if not digits:
        return {"valid": False, "error": "no digits found"}
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return {"valid": total % 10 == 0}
