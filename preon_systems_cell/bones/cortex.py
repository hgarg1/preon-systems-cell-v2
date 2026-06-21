from __future__ import annotations

import pathlib
from typing import Any

import yaml

from preon_systems_cell.bones.compiler import EnzymeCompiler
from preon_systems_cell.bones.models import BoneContract, BoneStep, CompiledEnzyme, EnzymeGene


class BoneCortex:
    """Cortical bone: capability graph + compiled enzyme registry + binding map.

    The organism's skeleton. Knows what the organism can do (contracts) and how to
    do it right now (enzyme bindings). Neither layer knows about the other's internals.
    """

    def __init__(self) -> None:
        self._contracts: dict[str, BoneContract] = {}
        self._aliases: dict[str, str] = {}
        self._enzymes: dict[str, CompiledEnzyme] = {}
        self._bindings: dict[str, str] = {}

    def register_contract(self, contract: BoneContract) -> None:
        self._contracts[contract.bone_id] = contract
        for alias in contract.aliases:
            self._aliases[alias] = contract.bone_id
        if contract.default_enzyme:
            self._bindings[contract.bone_id] = contract.default_enzyme

    def register_enzyme(self, enzyme: CompiledEnzyme) -> None:
        self._enzymes[enzyme.enzyme_id] = enzyme

    def bind(self, bone_id: str, enzyme_id: str) -> None:
        """Override the default enzyme binding for a bone at runtime."""
        self._bindings[self._resolve(bone_id)] = enzyme_id

    def resolve(self, bone_id: str) -> BoneContract | None:
        return self._contracts.get(self._resolve(bone_id))

    def can_satisfy(self, bone_id: str, payload: dict[str, Any]) -> bool:
        resolved = self._resolve(bone_id)
        enzyme_id = self._bindings.get(resolved)
        if enzyme_id is None:
            return False
        enzyme = self._enzymes.get(enzyme_id)
        if enzyme is None:
            return False
        return not enzyme.validate_input(payload)

    def execute(self, bone_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        resolved = self._resolve(bone_id)
        if resolved not in self._contracts:
            raise KeyError(f"no bone contract registered for {bone_id!r}")
        enzyme_id = self._bindings.get(resolved)
        if enzyme_id is None:
            raise KeyError(f"no enzyme bound to bone {bone_id!r}")
        enzyme = self._enzymes.get(enzyme_id)
        if enzyme is None:
            raise KeyError(f"enzyme {enzyme_id!r} not found in cortex")
        errors = enzyme.validate_input(payload)
        if errors:
            raise ValueError(f"bone {bone_id!r} input validation failed: {errors}")
        return enzyme.execute(payload)

    def list_bones(self) -> list[str]:
        return sorted(self._contracts.keys())

    def list_enzymes(self) -> list[str]:
        return sorted(self._enzymes.keys())

    def graph(self) -> dict[str, Any]:
        """Full capability graph structured by capability_family."""
        tree: dict[str, Any] = {}
        for bone in self._contracts.values():
            node = tree
            for part in bone.capability_path[:-1]:
                node = node.setdefault(part, {})
            node[bone.capability_path[-1]] = bone.bone_id
        return tree

    def _resolve(self, bone_id: str) -> str:
        return self._aliases.get(bone_id, bone_id)


class Osteocyte:
    """Monitors skeletal health: tracks usage frequency and execution outcomes per bone."""

    def __init__(self) -> None:
        self._usage: dict[str, int] = {}
        self._failures: dict[str, int] = {}

    def record_execution(self, bone_id: str, *, success: bool) -> None:
        self._usage[bone_id] = self._usage.get(bone_id, 0) + 1
        if not success:
            self._failures[bone_id] = self._failures.get(bone_id, 0) + 1

    def usage_summary(self) -> dict[str, dict[str, int]]:
        all_bones = set(self._usage) | set(self._failures)
        return {
            bone_id: {
                "executions": self._usage.get(bone_id, 0),
                "failures": self._failures.get(bone_id, 0),
            }
            for bone_id in sorted(all_bones)
        }


class Osteoclast:
    """Identifies obsolete skeletal structures for removal.

    Phase 1: identification only. Removal is a governed action requiring Osteoblast approval.
    """

    def candidates_for_removal(self, cortex: BoneCortex, osteocyte: Osteocyte) -> list[str]:
        used = set(osteocyte.usage_summary().keys())
        return [bone_id for bone_id in cortex.list_bones() if bone_id not in used]


def load_defaults() -> BoneCortex:
    """Load default bone contracts and enzyme genes from defaults.yaml.

    Called once at OrganismRuntime startup. Compiles all enzymes and registers
    all bone contracts. The result is the organism's initial skeletal structure.
    """
    yaml_path = pathlib.Path(__file__).parent / "defaults.yaml"
    with yaml_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    cortex = BoneCortex()
    compiler = EnzymeCompiler()

    for enzyme_data in data.get("enzymes", []):
        steps = [BoneStep(**s) for s in enzyme_data.get("steps", [])]
        gene = EnzymeGene(
            enzyme_id=enzyme_data["enzyme_id"],
            kind=enzyme_data["kind"],
            input_schema=enzyme_data.get("input_schema", {}),
            output_key=enzyme_data.get("output_key", "result"),
            expression=enzyme_data.get("expression"),
            steps=steps,
            ref=enzyme_data.get("ref"),
        )
        compiled = compiler.compile(gene)
        cortex.register_enzyme(compiled)

    for contract_data in data.get("bone_contracts", []):
        contract = BoneContract(
            bone_id=contract_data["bone_id"],
            capability_family=contract_data["capability_family"],
            capability_path=contract_data["capability_path"],
            input_schema=contract_data.get("input_schema", {}),
            output_schema=contract_data.get("output_schema", {}),
            constraints=contract_data.get("constraints", []),
            default_enzyme=contract_data.get("default_enzyme"),
            aliases=contract_data.get("aliases", []),
        )
        cortex.register_contract(contract)

    return cortex
