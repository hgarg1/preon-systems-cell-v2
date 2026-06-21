from __future__ import annotations


def handle(payload: dict) -> dict:
    return {
        "result": "contract_call_prepared",
        "contract": payload.get("contract"),
        "action": payload.get("action"),
    }
