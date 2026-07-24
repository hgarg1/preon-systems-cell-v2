from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from preon_systems_cell.models import ProteinType
from preon_systems_cell.resilience import FailureType, RuntimeFailure


_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


def protein_json_schema(
    protein_type: ProteinType,
    *,
    output_schema: dict[str, str] | None = None,
) -> dict[str, Any]:
    scalar_types = {
        "string": "string",
        "number": "number",
        "integer": "integer",
        "boolean": "boolean",
        "array": "array",
        "object": "object",
    }
    if protein_type == ProteinType.REASONING:
        properties = {
            "final_answer": {"type": "string"},
            "reasoning_summary": {"type": ["string", "null"]},
        }
        required = ["final_answer"]
    elif protein_type == ProteinType.RETRIEVAL:
        properties = {
            "result": {},
            "sources": {"type": "array", "minItems": 1, "items": {"type": "object"}},
        }
        required = ["result", "sources"]
    elif protein_type == ProteinType.TRANSFORMATION:
        properties = {
            name: {"type": scalar_types.get(declared.lower(), "string")}
            for name, declared in (output_schema or {}).items()
        }
        required = list(properties)
    elif protein_type == ProteinType.AGGREGATION:
        properties = {
            "result": {},
            "disagreements": {"type": "array", "items": {}},
        }
        required = ["result", "disagreements"]
    else:
        properties = {
            "score": {"type": "number", "minimum": 0, "maximum": 1},
            "criteria": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            "rationale": {"type": "string"},
        }
        required = ["score", "criteria", "rationale"]
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": (
            protein_type != ProteinType.TRANSFORMATION or not output_schema
        ),
    }


@dataclass(frozen=True)
class NormalizedProteinOutput:
    payload: dict[str, Any]
    repaired: bool = False


class ProteinOutputNormalizer:
    def normalize(
        self,
        raw: str | dict[str, Any],
        protein_type: ProteinType,
        *,
        output_schema: dict[str, str] | None = None,
        criteria: list[str] | None = None,
        inputs: list[Any] | None = None,
    ) -> NormalizedProteinOutput:
        repaired = False
        if isinstance(raw, dict):
            parsed = dict(raw)
        else:
            text = raw.strip()
            fenced = _FENCE.match(text)
            if fenced:
                text = fenced.group(1).strip()
                repaired = True
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                if protein_type == ProteinType.REASONING and text:
                    return NormalizedProteinOutput(
                        {"result": text, "final_answer": text, "reasoning_summary": None},
                        repaired=False,
                    )
                raise RuntimeFailure(
                    f"{protein_type.value} provider output is not valid JSON",
                    failure_type=FailureType.VALIDATION,
                )
            if not isinstance(value, dict):
                raise RuntimeFailure(
                    f"{protein_type.value} provider output must be a JSON object",
                    failure_type=FailureType.VALIDATION,
                )
            parsed = value

        if protein_type == ProteinType.REASONING:
            result = parsed.get("final_answer", parsed.get("result"))
            if not isinstance(result, str) or not result.strip():
                self._invalid("reasoning output requires final_answer or result")
            parsed.setdefault("result", result)
            parsed.setdefault("final_answer", result)
        elif protein_type == ProteinType.RETRIEVAL:
            if not parsed.get("result"):
                self._invalid("retrieval output requires result")
            sources = parsed.get("sources")
            if not isinstance(sources, list) or not sources:
                self._invalid("retrieval output requires non-empty sources")
        elif protein_type == ProteinType.TRANSFORMATION:
            for name in (output_schema or {}):
                if name not in parsed:
                    self._invalid(f"transformation output missing field {name!r}")
            parsed.setdefault("result", {key: parsed[key] for key in (output_schema or parsed)})
        elif protein_type == ProteinType.AGGREGATION:
            if not parsed.get("result"):
                self._invalid("aggregation output requires result")
            parsed.setdefault("inputs", list(inputs or []))
            parsed.setdefault("disagreements", [])
        elif protein_type == ProteinType.EVALUATION:
            score = parsed.get("score")
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 1:
                self._invalid("evaluation output requires score between 0 and 1")
            applied = parsed.get("criteria", criteria or [])
            if not isinstance(applied, list) or not applied:
                self._invalid("evaluation output requires criteria")
            parsed["criteria"] = applied
            parsed.setdefault("result", parsed.get("rationale", f"score={score}"))
        return NormalizedProteinOutput(parsed, repaired=repaired)

    @staticmethod
    def _invalid(message: str) -> None:
        raise RuntimeFailure(message, failure_type=FailureType.VALIDATION)
