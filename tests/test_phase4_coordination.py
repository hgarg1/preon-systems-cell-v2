from __future__ import annotations

from threading import Barrier, Lock, current_thread

import pytest
from pydantic import ValidationError

from preon_systems_cell.coordination import (
    CellExecutionCoordinator,
    ConditionEvaluationError,
    PlanValidationError,
    StepAttempt,
    build_step_payload,
    evaluate_condition,
)
from preon_systems_cell.engine import OrganismRuntime
from preon_systems_cell.models import (
    Actor,
    CellExecutionPlan,
    ExecutionStep,
    ExecutionStepStatus,
    ExecutionStrategy,
    Genome,
    GenomeModule,
    OrganismRecord,
    PolicySet,
    Protein,
    ProteinStatus,
    ProteinType,
    ResourceBudget,
    Signal,
    ValidationReport,
)


def _module(module_id: str) -> GenomeModule:
    return GenomeModule(
        module_id=module_id,
        signal_types=[module_id],
        execution_strategy=ExecutionStrategy.PRECOMPUTED,
    )


def _approved_protein(module_id: str, payload: dict, iteration: int = 1) -> Protein:
    return Protein(
        protein_id=f"protein-{module_id}-{iteration}",
        organism_id="organism-phase4",
        source_signal_id="signal-phase4",
        type=f"{module_id}.result",
        payload={"result": payload.get("value", payload), "input": payload},
        confidence=0.9,
        status=ProteinStatus.APPROVED,
        validation_report=ValidationReport(valid=True),
    )


def _coordinator_executor(step, module, payload, iteration, working_state):
    return StepAttempt(
        protein=_approved_protein(module.module_id, payload, iteration),
        status=ExecutionStepStatus.COMPLETED,
    )


def _execute_coordinator(plan: CellExecutionPlan, modules: list[GenomeModule], executor=_coordinator_executor):
    return CellExecutionCoordinator({module.module_id: module for module in modules}).execute(
        plan=plan,
        organism_id="organism-phase4",
        cell_id="cell-phase4",
        signal_id="signal-phase4",
        signal_payload={"value": "seed"},
        executor=executor,
        run_id="cellrun-phase4",
    )


def test_execution_plan_rejects_duplicate_step_ids():
    with pytest.raises(ValidationError, match="step ids must be unique"):
        CellExecutionPlan(
            plan_id="duplicate",
            steps=[
                ExecutionStep(step_id="same", module_id="a"),
                ExecutionStep(step_id="same", module_id="b"),
            ],
        )


def test_execution_plan_rejects_unknown_dependency():
    with pytest.raises(ValidationError, match="unknown dependencies"):
        CellExecutionPlan(
            plan_id="unknown-dependency",
            steps=[ExecutionStep(step_id="only", module_id="a", depends_on=["missing"])],
        )


def test_execution_plan_rejects_dependency_cycle():
    with pytest.raises(ValidationError, match="acyclic"):
        CellExecutionPlan(
            plan_id="cycle",
            steps=[
                ExecutionStep(step_id="a", module_id="a", depends_on=["b"]),
                ExecutionStep(step_id="b", module_id="b", depends_on=["a"]),
            ],
        )


def test_iterative_step_requires_a_bound_and_condition():
    with pytest.raises(ValidationError, match="requires iterate_while"):
        ExecutionStep(step_id="repeat", module_id="a", max_iterations=2)
    with pytest.raises(ValidationError, match="requires max_iterations"):
        ExecutionStep(step_id="repeat", module_id="a", iterate_while="True")


def test_condition_language_reads_step_state_and_boolean_logic():
    context = {
        "steps": {"lookup": {"confidence": 0.91, "status": "completed"}},
        "lookup": {"confidence": 0.91, "status": "completed"},
    }
    assert evaluate_condition(
        'lookup.confidence >= 0.9 and steps["lookup"].status == "completed"',
        context,
    )


def test_condition_language_rejects_calls_and_unknown_names():
    with pytest.raises(ConditionEvaluationError, match="unsupported condition syntax"):
        evaluate_condition("__import__('os')", {})
    with pytest.raises(ConditionEvaluationError, match="unknown condition name"):
        evaluate_condition("missing.value", {})


def test_input_map_resolves_signal_step_and_nested_literal_values():
    first = _approved_protein("first", {"value": "resolved"})
    from preon_systems_cell.models import ExecutionStepResult

    step_results = {
        "first": ExecutionStepResult(
            step_id="first",
            module_id="first",
            status=ExecutionStepStatus.COMPLETED,
            protein=first,
            iterations=1,
        )
    }
    step = ExecutionStep(
        step_id="second",
        module_id="second",
        depends_on=["first"],
        input_map={
            "original": "$signal.value",
            "prior": "$steps.first.result",
            "nested": {"confidence": "$steps.first.confidence"},
        },
    )
    assert build_step_payload(step, {"value": "seed"}, step_results, {}) == {
        "value": "seed",
        "original": "seed",
        "prior": "resolved",
        "nested": {"confidence": 0.9},
    }


def test_coordinator_runs_sequential_steps_and_feeds_prior_result():
    modules = [_module("first"), _module("second")]
    plan = CellExecutionPlan(
        plan_id="sequential",
        steps=[
            ExecutionStep(step_id="first", module_id="first"),
            ExecutionStep(
                step_id="second",
                module_id="second",
                depends_on=["first"],
                input_map={"value": "$steps.first.result"},
            ),
        ],
    )

    outcome = _execute_coordinator(plan, modules)

    assert outcome.run.status == "completed"
    assert outcome.run.step_results[1].input_payload["value"] == "seed"
    assert outcome.final_protein is not None
    assert outcome.final_protein.payload["result"] == "seed"
    assert set(outcome.run.shared_state) == {
        "execution_context",
        "shared_state_buffer",
        "result_registry",
    }


def test_coordinator_executes_independent_steps_in_parallel():
    modules = [_module("left"), _module("right")]
    plan = CellExecutionPlan(
        plan_id="parallel",
        steps=[
            ExecutionStep(step_id="left", module_id="left"),
            ExecutionStep(step_id="right", module_id="right"),
        ],
        max_parallelism=2,
    )
    rendezvous = Barrier(2)
    names: list[str] = []
    names_lock = Lock()

    def executor(step, module, payload, iteration, working_state):
        with names_lock:
            names.append(current_thread().name)
        rendezvous.wait(timeout=2)
        return _coordinator_executor(step, module, payload, iteration, working_state)

    outcome = _execute_coordinator(plan, modules, executor)

    assert outcome.run.status == "completed"
    assert len(set(names)) == 2


def test_false_condition_skips_step_without_blocking_independent_final_step():
    modules = [_module("first"), _module("optional"), _module("final")]
    plan = CellExecutionPlan(
        plan_id="conditional",
        steps=[
            ExecutionStep(step_id="first", module_id="first"),
            ExecutionStep(
                step_id="optional",
                module_id="optional",
                depends_on=["first"],
                condition="first.confidence > 0.99",
            ),
            ExecutionStep(step_id="final", module_id="final", depends_on=["first"]),
        ],
        final_step_id="final",
    )

    outcome = _execute_coordinator(plan, modules)

    statuses = {result.step_id: result.status for result in outcome.run.step_results}
    assert statuses == {
        "first": ExecutionStepStatus.COMPLETED,
        "optional": ExecutionStepStatus.SKIPPED,
        "final": ExecutionStepStatus.COMPLETED,
    }
    assert outcome.run.status == "completed"


def test_iteration_reuses_current_result_and_stops_on_condition():
    module = _module("refine")
    seen_payloads: list[dict] = []
    plan = CellExecutionPlan(
        plan_id="iteration",
        steps=[
            ExecutionStep(
                step_id="refine",
                module_id="refine",
                input_map={"previous": "$result.result"},
                max_iterations=4,
                iterate_while="iteration < 3",
            )
        ],
    )

    def executor(step, module, payload, iteration, working_state):
        seen_payloads.append(payload)
        return StepAttempt(
            protein=Protein(
                protein_id=f"protein-{iteration}",
                organism_id="organism-phase4",
                source_signal_id="signal-phase4",
                type="refine.result",
                payload={"result": iteration},
                confidence=0.9,
                status=ProteinStatus.APPROVED,
                validation_report=ValidationReport(valid=True),
            ),
            status=ExecutionStepStatus.COMPLETED,
        )

    outcome = _execute_coordinator(plan, [module], executor)

    assert outcome.run.step_results[0].iterations == 3
    assert [payload["previous"] for payload in seen_payloads] == [None, 1, 2]
    assert not outcome.run.step_results[0].iteration_limit_reached


def test_iteration_hard_limit_is_reported():
    module = _module("bounded")
    plan = CellExecutionPlan(
        plan_id="bounded-iteration",
        steps=[
            ExecutionStep(
                step_id="bounded",
                module_id="bounded",
                max_iterations=2,
                iterate_while="True",
            )
        ],
    )

    outcome = _execute_coordinator(plan, [module])

    result = outcome.run.step_results[0]
    assert result.iterations == 2
    assert result.iteration_limit_reached
    assert outcome.run.status == "completed"


def test_fail_fast_skips_remaining_plan_after_failure():
    modules = [_module("bad"), _module("later")]
    plan = CellExecutionPlan(
        plan_id="fail-fast",
        steps=[
            ExecutionStep(step_id="bad", module_id="bad"),
            ExecutionStep(step_id="later", module_id="later", depends_on=["bad"]),
        ],
    )

    def executor(step, module, payload, iteration, working_state):
        return StepAttempt(
            protein=None,
            status=ExecutionStepStatus.FAILED,
            error="deliberate failure",
        )

    outcome = _execute_coordinator(plan, modules, executor)

    assert [result.status for result in outcome.run.step_results] == [
        ExecutionStepStatus.FAILED,
        ExecutionStepStatus.SKIPPED,
    ]
    assert outcome.run.status == "failed"


def test_executor_exception_becomes_failed_step_instead_of_crashing_runtime():
    module = _module("explode")
    plan = CellExecutionPlan(
        plan_id="executor-error",
        steps=[ExecutionStep(step_id="explode", module_id="explode")],
    )

    def executor(step, module, payload, iteration, working_state):
        raise RuntimeError("provider exploded")

    outcome = _execute_coordinator(plan, [module], executor)

    assert outcome.run.status == "failed"
    assert outcome.run.step_results[0].status == ExecutionStepStatus.FAILED
    assert outcome.run.step_results[0].error == "step executor failed: provider exploded"


def test_non_fail_fast_plan_continues_independent_branch_after_failure():
    modules = [_module("bad"), _module("independent"), _module("blocked")]
    plan = CellExecutionPlan(
        plan_id="continue-independent",
        steps=[
            ExecutionStep(step_id="bad", module_id="bad"),
            ExecutionStep(step_id="independent", module_id="independent"),
            ExecutionStep(step_id="blocked", module_id="blocked", depends_on=["bad"]),
        ],
        final_step_id="independent",
        fail_fast=False,
    )

    def executor(step, module, payload, iteration, working_state):
        if step.step_id == "bad":
            return StepAttempt(
                protein=None,
                status=ExecutionStepStatus.FAILED,
                error="deliberate failure",
            )
        return _coordinator_executor(step, module, payload, iteration, working_state)

    outcome = _execute_coordinator(plan, modules, executor)

    statuses = {result.step_id: result.status for result in outcome.run.step_results}
    assert statuses == {
        "bad": ExecutionStepStatus.FAILED,
        "independent": ExecutionStepStatus.COMPLETED,
        "blocked": ExecutionStepStatus.SKIPPED,
    }
    assert outcome.run.status == "completed"


def _phase4_runtime(
    plan: CellExecutionPlan,
    step_modules: list[GenomeModule],
    *,
    budget: ResourceBudget | None = None,
) -> tuple[OrganismRuntime, OrganismRecord]:
    runtime = OrganismRuntime()
    genome_id = f"genome-{plan.plan_id}"
    trigger = GenomeModule(
        module_id="workflow_trigger",
        signal_types=["workflow"],
        execution_strategy=ExecutionStrategy.LLM_STUB,
        execution_plan=plan,
    )
    runtime.stores.genomes[genome_id] = Genome(
        genome_id=genome_id,
        modules=[trigger, *step_modules],
    )
    organism = runtime.create_organism(
        OrganismRecord(
            organism_id=f"organism-{plan.plan_id}",
            genome_id=genome_id,
            policies=PolicySet(allowed_signal_types=["workflow"]),
        )
    )
    if budget is not None:
        runtime.stores.cells[organism.organism_id][0] = runtime.stores.cells[organism.organism_id][0].model_copy(
            update={"resource_budget": budget}
        )
    return runtime, organism


def _workflow_signal(organism_id: str, **payload) -> Signal:
    return Signal(
        signal_id=f"signal-{organism_id}",
        organism_id=organism_id,
        actor=Actor(actor_id="operator", roles=["operator"]),
        type="workflow",
        payload=payload or {"term": "ATP"},
    )


def test_runtime_executes_retrieval_then_real_aggregation_with_organelle_events():
    plan = CellExecutionPlan(
        plan_id="retrieval-aggregation",
        steps=[
            ExecutionStep(
                step_id="lookup",
                module_id="lookup",
                input_map={"query": "$signal.term"},
            ),
            ExecutionStep(
                step_id="combine",
                module_id="combine",
                depends_on=["lookup"],
                input_map={
                    "inputs": ["$steps.lookup.result"],
                    "prompt": "Summarize the retrieved definitions",
                },
            ),
        ],
    )
    runtime, organism = _phase4_runtime(
        plan,
        [
            GenomeModule(
                module_id="lookup",
                signal_types=["search"],
                execution_strategy=ExecutionStrategy.DETERMINISTIC_TOOL,
                deterministic_tool="knowledge.reference.lookup",
                protein_type=ProteinType.RETRIEVAL,
            ),
            GenomeModule(
                module_id="combine",
                signal_types=["aggregate"],
                execution_strategy=ExecutionStrategy.LLM_STUB,
                protein_type=ProteinType.AGGREGATION,
            ),
        ],
    )

    decision, cell, protein, events, structure = runtime.submit_signal(
        _workflow_signal(organism.organism_id, term="ATP")
    )

    assert decision.action == "accept"
    assert structure is None
    assert cell is not None
    assert protein is not None and protein.status == ProteinStatus.APPROVED
    assert len(protein.payload["inputs"]) == 1
    run = runtime.stores.cell_execution_runs[organism.organism_id][0]
    assert run.status == "completed"
    assert [result.status for result in run.step_results] == [
        ExecutionStepStatus.COMPLETED,
        ExecutionStepStatus.COMPLETED,
    ]
    assert set(run.shared_state["result_registry"]) == {"lookup", "combine"}
    assert any(event.type == "cell_execution" for event in events)
    assert any(event.type == "golgi" and event.values["decision"] == "pass" for event in events)
    assert any(event.type == "cytoskeleton" and event.values["route"] == "membrane" for event in events)
    assert len(runtime.stores.proteins[organism.organism_id]) == 2
    assert runtime.stores.memory_records.get(organism.organism_id, []) == []
    assert any(
        event.type == "memory"
        and event.message == "Protein output not admitted to durable memory"
        for event in runtime.stores.events[organism.organism_id]
    )
    assert cell.resource_budget.compute_units == 8
    assert cell.resource_budget.tool_calls == 3


def test_runtime_reports_resource_exhaustion_and_skips_dependants():
    plan = CellExecutionPlan(
        plan_id="resource-bound",
        steps=[
            ExecutionStep(step_id="first", module_id="first"),
            ExecutionStep(step_id="second", module_id="second", depends_on=["first"]),
        ],
    )
    runtime, organism = _phase4_runtime(
        plan,
        [_module("first"), _module("second")],
        budget=ResourceBudget(compute_units=1, memory_units=10, tool_calls=4),
    )

    _, _, protein, events, _ = runtime.submit_signal(_workflow_signal(organism.organism_id))

    run = runtime.stores.cell_execution_runs[organism.organism_id][0]
    assert protein is not None and protein.status == ProteinStatus.DROPPED
    assert run.status == "failed"
    assert run.step_results[1].status == ExecutionStepStatus.RESOURCE_EXHAUSTED
    assert any(
        event.type == "mitochondria"
        and event.values.get("step_id") == "second"
        and event.values["reserved"] is False
        for event in events
    )


def test_runtime_lysosome_rolls_back_failed_llm_step_state():
    plan = CellExecutionPlan(
        plan_id="misfolded",
        steps=[ExecutionStep(step_id="combine", module_id="combine")],
    )
    runtime, organism = _phase4_runtime(
        plan,
        [
            GenomeModule(
                module_id="combine",
                signal_types=["aggregate"],
                execution_strategy=ExecutionStrategy.LLM_STUB,
                protein_type=ProteinType.AGGREGATION,
            )
        ],
    )

    _, _, protein, events, _ = runtime.submit_signal(_workflow_signal(organism.organism_id))

    run = runtime.stores.cell_execution_runs[organism.organism_id][0]
    assert protein is not None and protein.status == ProteinStatus.DROPPED
    assert run.status == "failed"
    assert "raw_combine" not in run.shared_state
    assert any(event.type == "lysosome" for event in events)


def test_runtime_enforces_iteration_budget_and_records_each_protein():
    plan = CellExecutionPlan(
        plan_id="runtime-iteration",
        steps=[
            ExecutionStep(
                step_id="repeat",
                module_id="repeat",
                max_iterations=3,
                iterate_while="True",
            )
        ],
    )
    runtime, organism = _phase4_runtime(plan, [_module("repeat")])

    _, cell, protein, _, _ = runtime.submit_signal(_workflow_signal(organism.organism_id))

    run = runtime.stores.cell_execution_runs[organism.organism_id][0]
    assert run.step_results[0].iterations == 3
    assert run.step_results[0].iteration_limit_reached
    assert len(runtime.stores.proteins[organism.organism_id]) == 3
    assert protein is not None and protein.protein_id == run.final_protein_id
    assert cell is not None and cell.resource_budget.compute_units == 7


def test_genome_validation_rejects_plan_module_missing_from_genome():
    runtime = OrganismRuntime()
    plan = CellExecutionPlan(
        plan_id="unknown-module",
        steps=[ExecutionStep(step_id="missing", module_id="not_in_genome")],
    )
    genome = Genome(
        genome_id="genome-invalid-plan",
        modules=[
            GenomeModule(
                module_id="trigger",
                signal_types=["workflow"],
                execution_plan=plan,
            )
        ],
    )

    report = runtime.validate_genome(genome)

    assert not report.valid
    assert report.errors == [
        "trigger execution plan: execution plan references unknown modules: not_in_genome"
    ]


def test_coordinator_rejects_unknown_module_even_without_genome_prevalidation():
    plan = CellExecutionPlan(
        plan_id="runtime-unknown-module",
        steps=[ExecutionStep(step_id="missing", module_id="not_registered")],
    )
    with pytest.raises(PlanValidationError, match="unknown modules"):
        _execute_coordinator(plan, [])
