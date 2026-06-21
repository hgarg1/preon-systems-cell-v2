from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field


class BoneStep(BaseModel):
    """One step in a composition enzyme; its output variable is available to all subsequent steps."""
    output: str
    expression: str


class EnzymeGene(BaseModel):
    """Gene definition compiled once at startup into a callable CompiledEnzyme."""
    enzyme_id: str
    kind: Literal["expression", "composition", "dynamic_expression", "python_ref"]
    input_schema: dict[str, str]  # field_name -> "number" | "string" | "integer" | "boolean"
    output_key: str
    expression: str | None = None
    steps: list[BoneStep] = Field(default_factory=list)
    ref: str | None = None  # "module.path:function" — python_ref kind only


class BoneContract(BaseModel):
    """Pure capability contract. Defines what the organism can do, never how."""
    bone_id: str
    capability_family: str
    capability_path: list[str]
    input_schema: dict[str, str]
    output_schema: dict[str, str]
    constraints: list[str] = Field(default_factory=list)
    default_enzyme: str | None = None
    aliases: list[str] = Field(default_factory=list)


@dataclass
class CompiledEnzyme:
    """Mineralized enzyme: frozen, callable, fast. The osteocyte embedded in cortical bone."""
    enzyme_id: str
    input_schema: dict[str, str]
    output_key: str
    _fn: Callable[[dict[str, Any]], dict[str, Any]]

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._fn(payload)

    def validate_input(self, payload: dict[str, Any]) -> list[str]:
        return [f"missing required field: {field}" for field in self.input_schema if field not in payload]
