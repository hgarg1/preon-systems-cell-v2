# ADR-013: Use Typed Failures and Bounded Resilience Semantics

**Status:** Accepted

---

## Context

Retries, fallbacks, circuit breakers, cancellation, and partial results interact across provider, protein, step, and cell boundaries. Independent exception handling in each component can retry permanent failures, exceed the caller's deadline, repeat non-idempotent work, or report cancellation as an ordinary error.

The runtime needs one failure model before tissue fan-out increases the number of concurrent failure paths.

---

## Proposed Decision

Define canonical typed failures and one bounded resilience policy shared across runtime layers.

- Failures identify layer, category, retryability, idempotency requirement, cause, and trace identity.
- Categories distinguish validation/permanent failure, transient provider failure, timeout, cancellation, saturation, policy rejection, resource exhaustion, and internal defect.
- Retry only transient, idempotent work within a shared attempt and absolute-deadline budget.
- A fallback call consumes the same logical step budget; fallback does not reset time or attempt limits.
- Provider circuit breakers use static safe thresholds initially, expose their state to operators, and never bypass data/provider policy.
- Cancellation is terminal for the cancelled scope and is not retried.
- Cell-plan outcomes distinguish `failed`, `partial`, `degraded`, `cancelled`, and `timed_out`.
- Fail-fast and independent-branch behavior use the same outcome definitions in execution, persistence, APIs, and telemetry.
- Hierarchical checkpoints and autonomous recovery modes remain Phase 11 work.

---

## Biological Analog

Biological homeostasis responds differently to a temporary shortage, a toxin, tissue damage, and organism death. Repeating the same response indefinitely can cause more harm than the original failure. Bounded retries and circuit breakers model controlled stress response rather than uncontrolled positive feedback.

---

## Digital Implementation

The execution service from ADR-009 owns the overall deadline and cancellation scope. Provider adapters translate vendor failures into canonical categories. The coordinator applies plan policy, and ADR-011 persists the same terminal status exposed by APIs.

Fault-injection tests cover transient recovery, permanent failure, exhausted budgets, open and half-open circuits, fallback policy, cancellation, and mixed-success branches.

---

## Consequences

- Callers and operators receive consistent failure meanings across layers.
- Retry storms and deadline overruns are bounded.
- Adapter authors must map provider-specific errors carefully.
- Some work will fail earlier instead of being retried optimistically; this is intentional when safety or budgets require it.
- Circuit state in an in-process implementation is replica-local until a later deployment decision introduces shared state.

---

## Alternatives Considered

**Retry every exception a fixed number of times:** Rejected because permanent, policy, validation, and cancellation failures should not retry.

**Let each component define its own statuses:** Rejected because persisted runs, APIs, and telemetry would disagree.

**Use fallback without a shared budget:** Rejected because a fallback chain could multiply latency and cost beyond the caller's limit.

**Implement autonomous hierarchical recovery now:** Deferred to Phase 11 because tissues, organs, and their checkpoint boundaries do not yet exist.
