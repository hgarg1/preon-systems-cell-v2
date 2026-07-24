"""Phase 4 cell-local execution planning and coordination.

Plans are genome-declared bounded DAGs. The coordinator owns dependency
scheduling, safe conditions, input mapping, parallel-ready waves, and bounded
iteration. Biological execution details remain callbacks owned by the runtime.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from preon_systems_cell.models import (
    CellExecutionPlan,
    CellExecutionRun,
    ExecutionStep,
    ExecutionStepResult,
    ExecutionStepStatus,
    GenomeModule,
    Protein,
    ProteinStatus,
    utc_now,
)
from preon_systems_cell.organelles import CellWorkingState
from preon_systems_cell.resilience import FailureType, RuntimeFailure
from preon_systems_cell.execution_service import cancellation_checkpoint
from preon_systems_cell.execution_service import DEFAULT_EXECUTION_SERVICE


class PlanValidationError(ValueError):
    """Raised when a structurally valid plan cannot run against its genome."""


class ConditionEvaluationError(ValueError):
    """Raised when a condition uses unsupported syntax or missing state."""


_FAILED_STEP_STATUSES = {
    ExecutionStepStatus.FAILED,
    ExecutionStepStatus.RESOURCE_EXHAUSTED,
    ExecutionStepStatus.CANCELLED,
    ExecutionStepStatus.TIMED_OUT,
}


@dataclass
class StepAttempt:
    protein: Protein | None
    status: ExecutionStepStatus
    events: list[Any] = field(default_factory=list)
    error: str | None = None
    failure_type: FailureType | None = None


@dataclass
class CoordinationOutcome:
    run: CellExecutionRun
    final_protein: Protein | None
    events: list[Any]
    working_state: CellWorkingState


def validate_plan_modules(plan: CellExecutionPlan, modules: Mapping[str, GenomeModule]) -> None:
    unknown = sorted({step.module_id for step in plan.steps} - set(modules))
    if unknown:
        raise PlanValidationError(f"execution plan references unknown modules: {', '.join(unknown)}")


def _attribute(value: Any, name: str) -> Any:
    if isinstance(value, Mapping):
        if name not in value:
            raise ConditionEvaluationError(f"condition value has no field {name!r}")
        return value[name]
    raise ConditionEvaluationError(f"cannot read field {name!r} from {type(value).__name__}")


_COMPARE_OPS: dict[type[ast.cmpop], Callable[[Any, Any], bool]] = {
    ast.Eq: lambda left, right: left == right,
    ast.NotEq: lambda left, right: left != right,
    ast.Lt: lambda left, right: left < right,
    ast.LtE: lambda left, right: left <= right,
    ast.Gt: lambda left, right: left > right,
    ast.GtE: lambda left, right: left >= right,
    ast.In: lambda left, right: left in right,
    ast.NotIn: lambda left, right: left not in right,
    ast.Is: lambda left, right: left is right,
    ast.IsNot: lambda left, right: left is not right,
}

_BINARY_OPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.Mod: lambda left, right: left % right,
}


def evaluate_condition(expression: str, context: Mapping[str, Any]) -> bool:
    """Evaluate a deliberately small, call-free expression language."""

    try:
        root = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ConditionEvaluationError(f"invalid condition syntax: {exc.msg}") from exc

    def evaluate(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in context:
                raise ConditionEvaluationError(f"unknown condition name {node.id!r}")
            return context[node.id]
        if isinstance(node, ast.Attribute):
            return _attribute(evaluate(node.value), node.attr)
        if isinstance(node, ast.Subscript):
            return evaluate(node.value)[evaluate(node.slice)]
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            values = [evaluate(item) for item in node.elts]
            if isinstance(node, ast.Tuple):
                return tuple(values)
            if isinstance(node, ast.Set):
                return set(values)
            return values
        if isinstance(node, ast.Dict):
            return {evaluate(key): evaluate(value) for key, value in zip(node.keys, node.values)}
        if isinstance(node, ast.BoolOp):
            values = [bool(evaluate(item)) for item in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
        if isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)
            if isinstance(node.op, ast.Not):
                return not value
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
            return _BINARY_OPS[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.Compare):
            left = evaluate(node.left)
            for operation, comparator in zip(node.ops, node.comparators):
                right = evaluate(comparator)
                function = _COMPARE_OPS.get(type(operation))
                if function is None:
                    raise ConditionEvaluationError(
                        f"unsupported comparison operator {type(operation).__name__}"
                    )
                if not function(left, right):
                    return False
                left = right
            return True
        raise ConditionEvaluationError(f"unsupported condition syntax: {type(node).__name__}")

    try:
        return bool(evaluate(root))
    except ConditionEvaluationError:
        raise
    except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise ConditionEvaluationError(f"condition could not be evaluated: {exc}") from exc


def _protein_view(protein: Protein | None, status: ExecutionStepStatus, iterations: int) -> dict[str, Any]:
    payload = protein.payload if protein is not None else {}
    return {
        "status": status.value,
        "confidence": protein.confidence if protein is not None else 0.0,
        "payload": payload,
        "result": payload.get("result"),
        "protein_id": protein.protein_id if protein is not None else None,
        "iterations": iterations,
    }


def condition_context(
    signal_payload: Mapping[str, Any],
    results: Mapping[str, ExecutionStepResult],
    shared_state: Mapping[str, Any],
    *,
    current_protein: Protein | None = None,
    iteration: int = 0,
) -> dict[str, Any]:
    steps = {
        step_id: _protein_view(result.protein, result.status, result.iterations)
        for step_id, result in results.items()
    }
    context: dict[str, Any] = {
        "signal": {"payload": dict(signal_payload), **dict(signal_payload)},
        "steps": steps,
        "shared": dict(shared_state),
        "result": _protein_view(
            current_protein,
            ExecutionStepStatus.COMPLETED if current_protein is not None else ExecutionStepStatus.PENDING,
            iteration,
        ),
        "iteration": iteration,
        "True": True,
        "False": False,
        "None": None,
    }
    context.update(steps)
    return context


def _resolve_reference(reference: str, context: Mapping[str, Any]) -> Any:
    path = reference[1:]
    if not path:
        raise PlanValidationError("input_map reference cannot be empty")
    tokens = path.split(".")
    if tokens[0] not in context:
        raise PlanValidationError(f"input_map has unknown root {tokens[0]!r}")
    value: Any = context[tokens[0]]
    for token in tokens[1:]:
        value = _attribute(value, token)
    return value


def _resolve_value(value: Any, context: Mapping[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        return _resolve_reference(value, context)
    if isinstance(value, list):
        return [_resolve_value(item, context) for item in value]
    if isinstance(value, tuple):
        return tuple(_resolve_value(item, context) for item in value)
    if isinstance(value, dict):
        return {key: _resolve_value(item, context) for key, item in value.items()}
    return value


def build_step_payload(
    step: ExecutionStep,
    signal_payload: Mapping[str, Any],
    results: Mapping[str, ExecutionStepResult],
    shared_state: Mapping[str, Any],
    *,
    current_protein: Protein | None = None,
    iteration: int = 1,
) -> dict[str, Any]:
    payload = dict(signal_payload)
    context = condition_context(
        signal_payload,
        results,
        shared_state,
        current_protein=current_protein,
        iteration=iteration,
    )
    for target, source in step.input_map.items():
        payload[target] = _resolve_value(source, context)
    return payload


StepExecutor = Callable[[ExecutionStep, GenomeModule, dict[str, Any], int, CellWorkingState], StepAttempt]


class CellExecutionCoordinator:
    """Runs a validated plan in dependency waves inside one selected cell."""

    def __init__(self, modules: Mapping[str, GenomeModule]) -> None:
        self.modules = dict(modules)

    def execute(
        self,
        *,
        plan: CellExecutionPlan,
        organism_id: str,
        cell_id: str,
        signal_id: str,
        signal_payload: Mapping[str, Any],
        executor: StepExecutor,
        run_id: str,
    ) -> CoordinationOutcome:
        validate_plan_modules(plan, self.modules)
        results: dict[str, ExecutionStepResult] = {}
        events: list[Any] = []
        working_state = CellWorkingState()
        working_state.write_sync(
            "execution_context",
            {
                "run_id": run_id,
                "plan_id": plan.plan_id,
                "signal_id": signal_id,
                "inputs": dict(signal_payload),
            },
            metadata={"source": "cell_execution_coordinator"},
        )
        working_state.write_sync("shared_state_buffer", {}, metadata={"source": "cell_execution_coordinator"})
        working_state.write_sync("result_registry", {}, metadata={"source": "cell_execution_coordinator"})

        ordered_steps = {step.step_id: step for step in plan.steps}
        pending = set(ordered_steps)

        while pending:
            terminal = set(results)
            candidates = [
                step
                for step in plan.steps
                if step.step_id in pending and set(step.depends_on).issubset(terminal)
            ]
            if not candidates:
                raise PlanValidationError("execution plan made no progress")

            ready: list[ExecutionStep] = []
            shared = working_state.read_sync("shared_state_buffer")
            for step in candidates:
                failed_dependencies = [
                    dependency
                    for dependency in step.depends_on
                    if results[dependency].status
                    in _FAILED_STEP_STATUSES | {ExecutionStepStatus.SKIPPED}
                ]
                if failed_dependencies:
                    results[step.step_id] = ExecutionStepResult(
                        step_id=step.step_id,
                        module_id=step.module_id,
                        status=ExecutionStepStatus.SKIPPED,
                        error=f"blocked by dependencies: {', '.join(failed_dependencies)}",
                    )
                    pending.remove(step.step_id)
                    continue
                if step.condition is not None:
                    try:
                        allowed = evaluate_condition(
                            step.condition,
                            condition_context(signal_payload, results, shared),
                        )
                    except ConditionEvaluationError as exc:
                        results[step.step_id] = ExecutionStepResult(
                            step_id=step.step_id,
                            module_id=step.module_id,
                            status=ExecutionStepStatus.FAILED,
                            error=str(exc),
                        )
                        pending.remove(step.step_id)
                        continue
                    if not allowed:
                        results[step.step_id] = ExecutionStepResult(
                            step_id=step.step_id,
                            module_id=step.module_id,
                            status=ExecutionStepStatus.SKIPPED,
                            error="condition evaluated false",
                        )
                        pending.remove(step.step_id)
                        continue
                ready.append(step)

            if not ready:
                if plan.fail_fast and any(
                    result.status in _FAILED_STEP_STATUSES
                    for result in results.values()
                ):
                    for step in plan.steps:
                        if step.step_id in pending:
                            results[step.step_id] = ExecutionStepResult(
                                step_id=step.step_id,
                                module_id=step.module_id,
                                status=ExecutionStepStatus.SKIPPED,
                                error="plan stopped after step failure",
                            )
                    pending.clear()
                continue

            results_snapshot = dict(results)
            shared_snapshot = dict(shared)

            def run_step(step: ExecutionStep) -> tuple[ExecutionStepResult, list[Any]]:
                current: Protein | None = None
                attempts = 0
                step_events: list[Any] = []
                latest_payload: dict[str, Any] = {}
                iteration_limit_reached = False
                for iteration in range(1, step.max_iterations + 1):
                    cancellation_checkpoint()
                    attempts = iteration
                    try:
                        latest_payload = build_step_payload(
                            step,
                            signal_payload,
                            results_snapshot,
                            shared_snapshot,
                            current_protein=current,
                            iteration=iteration,
                        )
                    except (PlanValidationError, ConditionEvaluationError) as exc:
                        return (
                            ExecutionStepResult(
                                step_id=step.step_id,
                                module_id=step.module_id,
                                status=ExecutionStepStatus.FAILED,
                                protein=current,
                                iterations=iteration - 1,
                                input_payload=latest_payload,
                                error=str(exc),
                            ),
                            step_events,
                        )
                    try:
                        attempt = executor(
                            step,
                            self.modules[step.module_id],
                            latest_payload,
                            iteration,
                            working_state,
                        )
                    except RuntimeFailure as exc:
                        status = {
                            FailureType.TIMEOUT: ExecutionStepStatus.TIMED_OUT,
                            FailureType.CANCELLED: ExecutionStepStatus.CANCELLED,
                            FailureType.RESOURCE_EXHAUSTION: ExecutionStepStatus.RESOURCE_EXHAUSTED,
                        }.get(exc.failure_type, ExecutionStepStatus.FAILED)
                        return (
                            ExecutionStepResult(
                                step_id=step.step_id,
                                module_id=step.module_id,
                                status=status,
                                protein=current,
                                iterations=iteration,
                                input_payload=latest_payload,
                                error=str(exc),
                                failure_type=exc.failure_type.value,
                            ),
                            step_events,
                        )
                    except Exception as exc:
                        return (
                            ExecutionStepResult(
                                step_id=step.step_id,
                                module_id=step.module_id,
                                status=ExecutionStepStatus.FAILED,
                                protein=current,
                                iterations=iteration,
                                input_payload=latest_payload,
                                error=f"step executor failed: {exc}",
                                failure_type=FailureType.INTERNAL.value,
                            ),
                            step_events,
                        )
                    step_events.extend(attempt.events)
                    current = attempt.protein
                    if attempt.status != ExecutionStepStatus.COMPLETED:
                        return (
                            ExecutionStepResult(
                                step_id=step.step_id,
                                module_id=step.module_id,
                                status=attempt.status,
                                protein=current,
                                iterations=iteration,
                                input_payload=latest_payload,
                                error=attempt.error,
                                failure_type=(
                                    attempt.failure_type.value
                                    if attempt.failure_type is not None
                                    else None
                                ),
                            ),
                            step_events,
                        )
                    if step.iterate_while is None:
                        break
                    iteration_context = condition_context(
                        signal_payload,
                        results_snapshot,
                        shared_snapshot,
                        current_protein=current,
                        iteration=iteration,
                    )
                    try:
                        repeat = evaluate_condition(step.iterate_while, iteration_context)
                    except ConditionEvaluationError as exc:
                        return (
                            ExecutionStepResult(
                                step_id=step.step_id,
                                module_id=step.module_id,
                                status=ExecutionStepStatus.FAILED,
                                protein=current,
                                iterations=iteration,
                                input_payload=latest_payload,
                                error=str(exc),
                            ),
                            step_events,
                        )
                    if not repeat:
                        break
                    if iteration == step.max_iterations:
                        iteration_limit_reached = True

                return (
                    ExecutionStepResult(
                        step_id=step.step_id,
                        module_id=step.module_id,
                        status=ExecutionStepStatus.COMPLETED,
                        protein=current,
                        iterations=attempts,
                        input_payload=latest_payload,
                        iteration_limit_reached=iteration_limit_reached,
                    ),
                    step_events,
                )

            ordered_wave = DEFAULT_EXECUTION_SERVICE.run_wave_sync(
                organism_id,
                [lambda step=step: run_step(step) for step in ready],
                max_parallelism=min(plan.max_parallelism, len(ready)),
            )
            wave_results = {
                step.step_id: result
                for step, result in zip(ready, ordered_wave)
            }

            registry = dict(working_state.read_sync("result_registry"))
            shared_buffer = dict(working_state.read_sync("shared_state_buffer"))
            for step in ready:
                result, step_events = wave_results[step.step_id]
                results[step.step_id] = result
                pending.remove(step.step_id)
                events.extend(step_events)
                if result.protein is not None:
                    registry[step.step_id] = result.protein.model_dump(mode="json")
                    shared_buffer[step.step_id] = result.protein.payload
            working_state.write_sync(
                "result_registry",
                registry,
                metadata={"source": "cell_execution_coordinator"},
            )
            working_state.write_sync(
                "shared_state_buffer",
                shared_buffer,
                metadata={"source": "cell_execution_coordinator"},
            )

            if plan.fail_fast and any(
                results[step.step_id].status
                in _FAILED_STEP_STATUSES
                for step in ready
            ):
                for step in plan.steps:
                    if step.step_id in pending:
                        results[step.step_id] = ExecutionStepResult(
                            step_id=step.step_id,
                            module_id=step.module_id,
                            status=ExecutionStepStatus.SKIPPED,
                            error="plan stopped after step failure",
                        )
                pending.clear()

        final_step_id = plan.final_step_id or plan.steps[-1].step_id
        final_result = results[final_step_id]
        final_protein = final_result.protein
        successful = (
            final_result.status == ExecutionStepStatus.COMPLETED
            and final_protein is not None
            and final_protein.status in {ProteinStatus.APPROVED, ProteinStatus.REPAIRED}
        )
        snapshot = working_state.snapshot_sync()
        shared_state = {
            slot: entry.value
            for slot, entry in snapshot.slots.items()
        }
        if successful:
            run_status = "completed"
        elif final_result.status == ExecutionStepStatus.CANCELLED:
            run_status = "cancelled"
        elif final_result.status == ExecutionStepStatus.TIMED_OUT:
            run_status = "timed_out"
        elif not plan.fail_fast and any(
            result.status == ExecutionStepStatus.COMPLETED
            and result.protein is not None
            and result.protein.status in {ProteinStatus.APPROVED, ProteinStatus.REPAIRED}
            for result in results.values()
        ):
            run_status = "partial"
        else:
            run_status = "failed"
        run = CellExecutionRun(
            run_id=run_id,
            plan_id=plan.plan_id,
            organism_id=organism_id,
            cell_id=cell_id,
            signal_id=signal_id,
            status=run_status,
            step_results=[results[step.step_id] for step in plan.steps],
            final_step_id=final_step_id,
            final_protein_id=final_protein.protein_id if final_protein is not None else None,
            shared_state=shared_state,
            completed_at=utc_now(),
        )
        return CoordinationOutcome(
            run=run,
            final_protein=final_protein,
            events=events,
            working_state=working_state,
        )
