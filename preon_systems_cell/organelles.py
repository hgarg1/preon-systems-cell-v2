"""
Cell-scoped organelle runtime implementations.

Covers the protein lifecycle within a single cell execution:
  LlmProtein → Proteasome → CellWorkingState → AnswerProtein → GolgiApparatus → Cytoskeleton → Membrane/Cell
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from preon_systems_cell.models import (
    AnswerProtein,
    CytoplasmEntry,
    CytoplasmSnapshot,
    DestructionRecord,
    GolgiDecision,
    GolgiReport,
    LlmProtein,
    ProteasomeReceipt,
    RetrySignal,
    utc_now,
)


class CellWorkingState:
    """Async-safe named-slot working memory scoped to one cell execution.

    Named slots used by convention:
      "shared_state_buffer"  — fast intermediate results accessible by all proteins
      "result_registry"      — completed outputs for aggregation and reuse
      "execution_context"    — live task state (inputs, constraints, metadata)
    """

    def __init__(self) -> None:
        self._slots: dict[str, CytoplasmEntry] = {}
        self._lock = asyncio.Lock()

    async def write(
        self,
        slot: str,
        value: Any,
        *,
        metadata: dict[str, Any] | None = None,
        overwrite: bool = True,
    ) -> None:
        async with self._lock:
            if not overwrite and slot in self._slots:
                raise KeyError(f"Cytoplasm slot already exists: {slot}")
            self._slots[slot] = CytoplasmEntry(value=value, metadata=metadata or {})

    async def read(self, slot: str) -> Any:
        async with self._lock:
            if slot not in self._slots:
                raise KeyError(f"Cytoplasm slot not found: {slot}")
            return self._slots[slot].value

    async def delete(self, slot: str) -> None:
        async with self._lock:
            self._slots.pop(slot, None)

    async def snapshot(self) -> CytoplasmSnapshot:
        async with self._lock:
            return CytoplasmSnapshot(slots=dict(self._slots))


class Proteasome:
    """Deconstructs a completed LlmProtein, extracts its answer, deposits it into
    CellWorkingState, and returns a consumed copy — enforcing single-use."""

    def __init__(self, working_state: CellWorkingState) -> None:
        self._ws = working_state

    async def deconstruct(
        self,
        protein: LlmProtein,
        *,
        target_slot: str,
    ) -> tuple[LlmProtein, ProteasomeReceipt]:
        if protein.consumed:
            raise ValueError(f"LlmProtein {protein.protein_id} has already been consumed")
        if protein.raw_answer is None:
            raise ValueError(f"LlmProtein {protein.protein_id} has no raw_answer to extract")

        consumed = protein.model_copy(update={"consumed": True})

        await self._ws.write(
            target_slot,
            protein.raw_answer,
            metadata={
                "source": "proteasome",
                "protein_id": protein.protein_id,
                "gene_id": protein.gene_id,
                "provider": protein.provider,
            },
        )

        receipt = ProteasomeReceipt(
            protein_id=protein.protein_id,
            cytoplasm_slot=target_slot,
            raw_answer=protein.raw_answer,
            source_gene_id=protein.gene_id,
            provider=protein.provider,
        )
        return consumed, receipt


ProteinValidator = Callable[[AnswerProtein], Awaitable[bool]]
ProteinRepairer = Callable[[AnswerProtein], Awaitable[AnswerProtein]]


class GolgiApparatus:
    """Validates and shapes AnswerProtein before routing or emission.

    Runs each validator in order. If any fail and a repairer is provided,
    attempts repair and re-validates. Destroys if repair fails or no repairer.
    Validators are pluggable callables so policy can be swapped per cell type.
    """

    def __init__(
        self,
        *,
        validators: list[ProteinValidator],
        repairer: ProteinRepairer | None = None,
    ) -> None:
        self.validators = validators
        self.repairer = repairer

    async def process(self, protein: AnswerProtein) -> GolgiReport:
        reasons: list[str] = []
        for validator in self.validators:
            if not await validator(protein):
                reasons.append(f"Validator failed: {validator.__name__}")

        if not reasons:
            return GolgiReport(decision=GolgiDecision.PASS, protein=protein)

        if self.repairer is not None:
            repaired = await self.repairer(protein)
            repair_reasons: list[str] = []
            for validator in self.validators:
                if not await validator(repaired):
                    repair_reasons.append(f"Validator failed after repair: {validator.__name__}")
            if repair_reasons:
                return GolgiReport(
                    decision=GolgiDecision.DESTROY,
                    reasons=reasons + repair_reasons,
                )
            return GolgiReport(decision=GolgiDecision.REPAIR, reasons=reasons, protein=repaired)

        return GolgiReport(decision=GolgiDecision.DESTROY, reasons=reasons)


class Lysosome:
    """Destroys misfolded or toxic AnswerProteins, rolls back partial CellWorkingState,
    logs each destruction, and optionally emits a retry signal."""

    def __init__(self, working_state: CellWorkingState) -> None:
        self._ws = working_state
        self.destruction_log: list[DestructionRecord] = []

    async def destroy(
        self,
        protein: AnswerProtein,
        *,
        reason: str,
        rollback_slots: list[str] | None = None,
        retry: bool = False,
    ) -> DestructionRecord:
        rolled_back: list[str] = []
        for slot in rollback_slots or []:
            await self._ws.delete(slot)
            rolled_back.append(slot)

        retry_signal: RetrySignal | None = None
        if retry:
            retry_signal = RetrySignal(
                payload={
                    "failed_protein_id": protein.answer_protein_id,
                    "source_gene_id": protein.source_gene_id,
                    "reason": reason,
                },
                metadata={"source": "lysosome"},
            )

        record = DestructionRecord(
            protein_id=protein.answer_protein_id,
            reason=reason,
            rolled_back_slots=rolled_back,
            retry_signal=retry_signal,
        )
        self.destruction_log.append(record)
        return record


class _MembraneEmitter(Protocol):
    async def emit(self, protein: AnswerProtein) -> None: ...


class _CellReceiver(Protocol):
    cell_id: str

    async def receive_answer_protein(self, protein: AnswerProtein) -> None: ...


class Cytoskeleton:
    """Routes AnswerProtein to its declared destination: same-cell CellWorkingState,
    another cell in the registry, or the membrane for external emission."""

    def __init__(
        self,
        *,
        cell_id: str,
        working_state: CellWorkingState,
        membrane: _MembraneEmitter,
        cell_registry: dict[str, _CellReceiver],
    ) -> None:
        self.cell_id = cell_id
        self._ws = working_state
        self._membrane = membrane
        self._cell_registry = cell_registry

    async def route(self, protein: AnswerProtein) -> None:
        dest = protein.destination

        if dest.kind == "cytoplasm":
            if dest.slot is None:
                raise ValueError("cytoplasm destination requires slot")
            await self._ws.write(
                dest.slot,
                protein.answer,
                metadata={
                    "source": "cytoskeleton",
                    "answer_protein_id": protein.answer_protein_id,
                    "source_gene_id": protein.source_gene_id,
                },
            )

        elif dest.kind == "cell":
            if dest.cell_id is None:
                raise ValueError("cell destination requires cell_id")
            target = self._cell_registry.get(dest.cell_id)
            if target is None:
                raise LookupError(f"Target cell not found: {dest.cell_id}")
            await target.receive_answer_protein(protein)

        elif dest.kind == "membrane":
            await self._membrane.emit(protein)

        else:
            raise ValueError(f"Unsupported destination kind: {dest.kind}")
