# ADR-009: Use a Shared Bounded Execution Service

**Status:** Accepted

---

## Context

The organism engine and provider adapters contain synchronous work. Calling the full execution path directly from an async FastAPI route can block the event loop. Creating an independent worker pool for each request or DAG wave would avoid some blocking but would not enforce system-wide limits, propagate cancellation reliably, or provide meaningful backpressure.

Phase 4.5 must define the runtime execution boundary before tissue fan-out multiplies concurrency.

---

## Proposed Decision

Run organism work through one shared, bounded execution-service abstraction.

- FastAPI submits work to the service rather than executing the synchronous organism path on its event loop.
- The service owns global, per-organism, and per-provider concurrency controls.
- One absolute deadline and cancellation signal propagate from request to cell run, step, and provider call.
- Admission failure, queue saturation, timeout, cancellation, and partial completion have distinct typed outcomes.
- Provider limits wrap the actual provider invocation, not only request admission.
- Executors are application-lifecycle resources; request handlers do not create private pools.
- The first implementation may be in-process. Its interface must allow an external worker system later without changing cell-plan semantics or public APIs.

Limits are process-wide in the in-process implementation. A multi-replica deployment needs a distributed limiter or infrastructure-level quota before claiming deployment-wide enforcement.

---

## Biological Analog

The cytoskeleton and circulatory system coordinate shared transport capacity across a cell and organism. Each incoming signal does not grow a private transport network. Capacity is bounded, prioritized, and shared so local activity cannot starve the whole organism.

---

## Digital Implementation

The execution service exposes bounded submission and returns an execution handle containing identity, deadline, cancellation, and completion state. The same handle is connected to `TraceContext` from ADR-010 and failure semantics from ADR-013.

Tests must demonstrate event-loop responsiveness, bounded concurrency, deterministic saturation, deadline propagation, cancellation, and cleanup after failure.

---

## Consequences

- Request concurrency cannot create unbounded threads or provider calls.
- Runtime behavior becomes testable independently of HTTP.
- In-process execution remains operationally simple for the current deployment stage.
- Process-local limits are not global across replicas and must be described honestly.
- Moving to an external queue remains a future deployment decision and may require a follow-up ADR.

---

## Alternatives Considered

**Execute synchronously in FastAPI:** Rejected because one slow run can block unrelated async request handling.

**Create a pool per request or plan wave:** Rejected because aggregate concurrency remains unbounded and lifecycle cleanup becomes unreliable.

**Adopt an external queue immediately:** Deferred because current durability and scale do not yet justify its operational cost. The execution-service contract preserves that migration path.

**Allow every provider adapter to manage its own concurrency:** Rejected because the organism could still exceed global or per-organism budgets.
