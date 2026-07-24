import asyncio
from datetime import UTC, datetime
from threading import Event
import time

import pytest

from preon_systems_cell.api import (
    RUNTIME,
    get_cell_execution_run,
    list_cell_execution_runs,
)
from preon_systems_cell.engine import OrganismRuntime, RuntimeStores
from preon_systems_cell.execution_service import SharedExecutionService, cancellation_checkpoint
from preon_systems_cell.model_routing.telemetry import clear_log, get_log
from preon_systems_cell.models import (
    CellExecutionRun,
    DataClass,
    ExecutionStrategy,
    Genome,
    GenomeModule,
    LlmProvider,
    ModelClass,
    OrganismRecord,
    ProteinType,
    Signal,
    TraceContext,
    highest_data_class,
)
from preon_systems_cell.protein_output import ProteinOutputNormalizer
from preon_systems_cell.resilience import (
    CircuitBreaker,
    FailureType,
    RuntimeFailure,
    RetryBudget,
    retry_bounded,
)
from preon_systems_cell.security import bounded_redact
from preon_systems_cell.storage.postgres import PostgresRuntimeStore


class _Adapter:
    def __init__(self, output: str) -> None:
        self.output = output
        self.kwargs = {}

    def complete(self, *_args, **kwargs) -> str:
        self.kwargs = kwargs
        return self.output


def test_data_class_is_ordered_and_restricted_payloads_are_redacted():
    assert highest_data_class(DataClass.PUBLIC, DataClass.CONFIDENTIAL) == DataClass.CONFIDENTIAL
    assert bounded_redact(
        {"result": "private", "count": 2},
        DataClass.RESTRICTED,
    ) == {"result": "[REDACTED]", "count": 2}


def test_live_reasoning_output_is_normalized_and_traced(monkeypatch):
    clear_log()
    adapter = _Adapter('{"final_answer":"42","reasoning_summary":"checked"}')
    monkeypatch.setattr(
        "preon_systems_cell.llm_providers.get_adapter",
        lambda *_args: adapter,
    )
    runtime = OrganismRuntime()
    module = GenomeModule(
        module_id="reasoning",
        signal_types=["query"],
        execution_strategy=ExecutionStrategy.LLM,
        llm_provider=LlmProvider.OPENAI,
        llm_model_class=ModelClass.REASONING,
        model_routing_policy="explicit_override",
        protein_type=ProteinType.REASONING,
        data_class_allowed=[DataClass.RESTRICTED],
    )
    trace = TraceContext(organism_id="org-1")
    protein = runtime.ribosome.execute(
        module,
        Signal(
            signal_id="signal-1",
            organism_id="org-1",
            type="query",
            payload={"prompt": "six times seven"},
            data_class=DataClass.RESTRICTED,
            trace_context=trace,
        ),
    )

    assert protein.payload["result"] == "42"
    assert protein.data_class == DataClass.RESTRICTED
    telemetry = get_log()[-1]
    assert telemetry["request_id"] == trace.request_id
    assert telemetry["provider_call_id"].startswith("providercall-")
    assert telemetry["schema_valid"] is True
    assert adapter.kwargs["response_schema"]["required"] == ["final_answer"]


def test_restricted_data_fails_closed_without_an_approved_provider(monkeypatch):
    monkeypatch.setattr("preon_systems_cell.llm_providers.get_adapter", lambda *_args: None)
    runtime = OrganismRuntime()
    module = GenomeModule(
        module_id="reasoning",
        signal_types=["query"],
        execution_strategy=ExecutionStrategy.LLM,
        llm_provider=LlmProvider.GROK,
        model_routing_policy="explicit_override",
        protein_type=ProteinType.REASONING,
        data_class_allowed=[DataClass.RESTRICTED],
    )
    protein = runtime.ribosome.execute(
        module,
        Signal(
            signal_id="signal-1",
            organism_id="org-1",
            type="query",
            data_class=DataClass.RESTRICTED,
        ),
    )
    assert "restricted data requires" in protein.payload["error"]


@pytest.mark.parametrize(
    ("protein_type", "raw", "kwargs", "key"),
    [
        (ProteinType.REASONING, "plain answer", {}, "final_answer"),
        (
            ProteinType.RETRIEVAL,
            '{"result":"fact","sources":[{"uri":"urn:test"}]}',
            {},
            "sources",
        ),
        (
            ProteinType.TRANSFORMATION,
            '{"name":"Ada"}',
            {"output_schema": {"name": "string"}},
            "result",
        ),
        (
            ProteinType.AGGREGATION,
            '{"result":"combined","disagreements":[]}',
            {"inputs": ["a", "b"]},
            "inputs",
        ),
        (
            ProteinType.EVALUATION,
            '{"score":0.8,"criteria":["accuracy"],"rationale":"good"}',
            {},
            "score",
        ),
    ],
)
def test_all_five_protein_contracts_normalize(protein_type, raw, kwargs, key):
    normalized = ProteinOutputNormalizer().normalize(raw, protein_type, **kwargs)
    assert key in normalized.payload


def test_invalid_retrieval_does_not_invent_sources():
    with pytest.raises(RuntimeFailure) as exc_info:
        ProteinOutputNormalizer().normalize('{"result":"uncited"}', ProteinType.RETRIEVAL)
    assert exc_info.value.failure_type == FailureType.VALIDATION


def test_execution_service_enforces_deadline_without_blocking_event_loop():
    service = SharedExecutionService(max_workers=1, global_limit=1)

    async def run() -> None:
        with pytest.raises(RuntimeFailure) as exc_info:
            await service.run("org-1", time.sleep, 0.05, timeout_seconds=0.005)
        assert exc_info.value.failure_type == FailureType.TIMEOUT

    try:
        asyncio.run(run())
    finally:
        service.close()


def test_execution_service_propagates_cooperative_cancellation():
    service = SharedExecutionService(max_workers=1)
    observed = Event()

    def operation() -> None:
        try:
            while True:
                cancellation_checkpoint()
                time.sleep(0.001)
        except RuntimeFailure as exc:
            if exc.failure_type == FailureType.CANCELLED:
                observed.set()
            raise

    async def run() -> None:
        task = asyncio.create_task(service.run("org-1", operation))
        await asyncio.sleep(0.005)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.to_thread(observed.wait, 0.2)

    try:
        asyncio.run(run())
        assert observed.is_set()
    finally:
        service.close()


def test_provider_concurrency_saturation_is_typed():
    service = SharedExecutionService(per_provider_limit=1)
    try:
        with service.provider_slot("openai", 0.01):
            with pytest.raises(RuntimeFailure) as exc_info:
                with service.provider_slot("openai", 0.001):
                    pass
        assert exc_info.value.failure_type == FailureType.SATURATION
    finally:
        service.close()


def test_retry_budget_retries_only_retryable_work():
    attempts = 0

    def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("temporary")
        return "ok"

    assert retry_bounded(
        operation,
        budget=RetryBudget(max_attempts=2, base_delay_seconds=0),
        is_retryable=lambda exc: isinstance(exc, OSError),
    ) == "ok"
    assert attempts == 2


def test_circuit_breaker_opens_and_recovers():
    circuit = CircuitBreaker(failure_threshold=2, recovery_seconds=0)
    circuit.failure()
    assert circuit.state == "closed"
    circuit.failure()
    assert circuit.state == "half_open"
    circuit.success()
    assert circuit.state == "closed"


def test_cell_run_retrieval_is_owner_scoped():
    stores = RuntimeStores()
    stores.genomes["genome-default"] = Genome(genome_id="genome-default")
    stores.organisms["org-1"] = OrganismRecord(organism_id="org-1", owner_user_id="owner-1")
    stores.cell_execution_runs["org-1"] = [
        CellExecutionRun(
            run_id="run-1",
            plan_id="plan-1",
            organism_id="org-1",
            cell_id="cell-1",
            signal_id="signal-1",
            owner_user_id="owner-1",
            status="completed",
            final_step_id="step-1",
        )
    ]
    original = RUNTIME.stores
    RUNTIME.stores = stores
    try:
        assert list_cell_execution_runs("org-1", "owner-1")[0].run_id == "run-1"
        assert get_cell_execution_run("org-1", "run-1", "owner-1") is not None
        assert list_cell_execution_runs("org-1", "other") is None
    finally:
        RUNTIME.stores = original


def test_postgres_reload_reconstructs_durable_cell_run():
    now = datetime.now(UTC)
    run_row = {
        "run_id": "run-1",
        "plan_id": "plan-1",
        "organism_id": "org-1",
        "cell_id": "cell-1",
        "signal_id": "signal-1",
        "owner_user_id": "owner-1",
        "status": "completed",
        "final_step_id": "step-1",
        "final_protein_id": None,
        "shared_state": {},
        "data_class": "confidential",
        "trace_context": {
            "request_id": "request-1",
            "organism_id": "org-1",
            "cell_run_id": "run-1",
        },
        "created_at": now,
        "completed_at": now,
    }
    step_row = {
        "result": {
            "step_id": "step-1",
            "module_id": "module-1",
            "status": "completed",
        }
    }

    class Connection:
        async def fetch(self, query, *args):
            if "FROM cell_execution_runs" in query:
                return [run_row]
            if "FROM cell_execution_step_results" in query:
                assert args == ("run-1",)
                return [step_row]
            return []

    class Acquire:
        async def __aenter__(self):
            return Connection()

        async def __aexit__(self, *_args):
            return None

    class Pool:
        def acquire(self):
            return Acquire()

    stores = asyncio.run(PostgresRuntimeStore(Pool()).load_stores())
    run = stores.cell_execution_runs["org-1"][0]
    assert run.run_id == "run-1"
    assert run.data_class == DataClass.CONFIDENTIAL
    assert run.trace_context.cell_run_id == "run-1"
    assert run.step_results[0].step_id == "step-1"
