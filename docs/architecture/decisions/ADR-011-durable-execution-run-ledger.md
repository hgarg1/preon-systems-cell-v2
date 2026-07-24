# ADR-011: Persist Cell Runs as a Durable Execution Ledger

**Status:** Accepted

---

## Context

Phase 4 execution-run state is process-memory only. It disappears on restart and cannot support run retrieval, operational investigation, reliable replay inputs, or future memory provenance. Persisting one opaque response blob would be simple, but it would make ordered step queries, schema evolution, and bounded retention difficult.

---

## Proposed Decision

Persist cell execution as an append-oriented run ledger with separate run and ordered step records.

- `CellExecutionRun` stores run identity, ownership, plan/version identity, status, timing, trace linkage, classification, and final outcome metadata.
- `ExecutionStepResult` stores stable step order, attempts/iterations, dependency outcome, timing, status, protein reference, and bounded result metadata.
- PostgreSQL is the durable production store; the in-memory store implements the same behavioral contract for tests and local operation.
- Large or sensitive inputs and outputs are stored once as bounded snapshots or protected references, not duplicated into every event and step.
- State transitions are explicit and validated. Terminal records are append-mostly; corrections use additional metadata or a superseding record rather than silent history rewriting.
- Retrieval APIs are owner-scoped, paginated, and return redacted views appropriate to the caller.
- Retention and deletion policy are configurable and respect the record's `DataClass`.

This ledger is execution history, not Phase 5 semantic memory. Promotion into organism memory requires a separate admission decision.

---

## Biological Analog

Episodic traces are not the same as learned memory. Biological systems first leave a record of activity; only selected experiences consolidate into durable memory. The execution ledger preserves what occurred, while Phase 5 decides what deserves reuse.

---

## Digital Implementation

Schema migrations create run and step tables with stable identifiers, ownership keys, trace keys, timestamps, status fields, and bounded payload references. The store contract supports create, transition, append-step-result, list, and get operations.

Round-trip, restart, ordering, redaction, ownership, and in-memory/PostgreSQL parity tests are required.

---

## Consequences

- Runs survive restart and become inspectable through stable APIs.
- Execution history can support provenance without polluting organism memory.
- Database schema and retention become part of the compatibility surface.
- Full deterministic replay is not guaranteed unless all external inputs, model identities, and nondeterministic parameters are separately captured.
- Strict tenant isolation requires stronger database controls than owner-scoped application queries alone.

---

## Alternatives Considered

**Keep process-memory history:** Rejected because it cannot survive restart or support trustworthy operations.

**Store one JSON blob per run:** Rejected as the sole representation because step ordering, status queries, retention, and migrations become opaque.

**Persist every prompt and completion inline:** Rejected because of duplication, sensitive-data exposure, and unbounded storage.

**Write execution results directly into organism memory:** Rejected because operational history and admitted reusable knowledge have different lifecycle and quality rules.
