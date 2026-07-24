# ADR-016: Separate Working State from Admitted Durable Memory

**Status:** Accepted

---

## Context

The runtime previously persisted every approved final protein as organism memory. Approval means that a protein is valid output; it does not mean that the output is important, novel, safe to retain, or useful across later activations. Treating execution history, cell working state, and long-term organism memory as the same thing produces unbounded low-value retention.

---

## Decision

`CellWorkingState` and execution-run state remain execution-scoped. A protein becomes durable organism memory only through an explicit admission decision.

Automatic admission requires:

- an explicit memory-candidate marker;
- an approved or repaired source protein;
- minimum confidence and importance;
- novelty against active admitted memory;
- valid source provenance;
- review before promoting a redacted or invalidated source.

Operator-created memory is explicit manual admission. Every admitted record carries type, confidence, importance, content hash, provenance, classification, admission status, promotion reason, lifecycle metadata, and the Phase 5A structural resource holding it.

Tissue and organ memory remain deferred until their owning runtimes exist.

---

## Consequences

- Routine valid output no longer silently becomes long-term memory.
- Execution history remains available in its durable ledger without polluting memory.
- Callers that want automatic retention must declare candidacy and importance.
- Existing manual memory APIs remain an intentional operator admission path.

---

## Alternatives Considered

**Persist every approved protein:** Rejected because validation and long-term value are different decisions.

**Treat execution logs as memory:** Rejected because logs have different access, retention, and retrieval semantics.
