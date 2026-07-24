# ADR-010: Propagate an Explicit Hierarchical Trace Context

**Status:** Accepted

---

## Context

Request, cell-run, step, protein, routing, and provider telemetry currently use incomplete or disconnected identifiers. Once execution fans out, timestamps alone cannot reconstruct causality. Implicit thread-local context is also unreliable across async tasks, worker threads, retries, and future external workers.

Phase 4.5 needs a trace contract before durable execution history is introduced.

---

## Proposed Decision

Define an immutable, explicitly propagated `TraceContext` containing:

```text
request_id
organism_id
cell_run_id
step_id
protein_id
provider_call_id
```

- Components derive child contexts rather than mutating a shared context.
- Context travels through signals, execution handles, runtime events, routing decisions, provider telemetry, and durable run records.
- A unified telemetry-sink interface accepts typed events from execution and provider layers.
- Trace and span identifiers remain compatible with W3C Trace Context and OpenTelemetry export, without making a specific observability vendor part of the domain model.
- Retries receive distinct provider-call identities linked to the same logical step.
- Raw confidential or restricted payloads are excluded from trace events by default under ADR-012.
- Missing required trace identity is a contract violation at implemented runtime boundaries.

---

## Biological Analog

Biological signals carry origin, destination, and pathway context. A hormone concentration without knowledge of its source and target is insufficient to explain an organism's response. Trace context provides the lineage needed to connect a digital response to the signal and transformations that produced it.

---

## Digital Implementation

Domain code passes `TraceContext` explicitly. Transport integrations may additionally map it into framework context variables or W3C headers, but those mechanisms are adapters rather than the source of truth.

The telemetry collector becomes a live sink implementation instead of an unused abstraction. Tests cover fan-out, retries, thread offload, cancellation, persistence, and redaction.

---

## Consequences

- A cell run can be reconstructed across execution, routing, and provider events.
- Explicit propagation adds parameters to service boundaries but avoids hidden context loss.
- Telemetry backends can change without altering runtime identity.
- Cardinality and retention require operational limits.
- Later tissue and organ phases extend the context with new span relationships rather than inventing separate tracing models.

---

## Alternatives Considered

**Correlate by timestamps and object IDs:** Rejected because parallel steps, retries, and repeated protein identities make causality ambiguous.

**Use framework globals or thread-local state only:** Rejected because context can disappear during async fan-out and thread offload.

**Couple domain models directly to one tracing vendor:** Rejected because observability infrastructure should remain replaceable.

**Store full prompts and outputs in every trace event:** Rejected because it duplicates data and creates privacy, cost, and retention risks.
