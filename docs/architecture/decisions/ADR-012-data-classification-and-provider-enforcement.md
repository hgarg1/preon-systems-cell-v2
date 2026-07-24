# ADR-012: Enforce Canonical Data Classification at Provider Invocation

**Status:** Accepted

---

## Context

Free-form classification strings cannot support reliable policy checks. Checking only at the HTTP membrane is insufficient because data may be transformed, combined, loaded from memory, or routed to a different provider later in the execution path. Logs and durable run snapshots also create secondary disclosure paths.

Phase 4.5 requires a minimum security boundary before broader fan-out and durable memory.

---

## Proposed Decision

Adopt one canonical `DataClass` enum:

```text
public < internal < confidential < restricted
```

- Every signal, step payload, protein, runtime event, execution record, and later memory record carries a classification.
- Combining inputs produces at least the highest input classification unless an explicit, audited declassification policy applies.
- Provider and model policies declare the maximum permitted class and any residency or local-runtime requirements.
- Compatibility is enforced immediately before every provider invocation, after all input mapping and context construction.
- Policy failure is fail-closed. A fallback provider is allowed only when it independently satisfies the same policy.
- Restricted payloads require a configured, policy-approved execution target; the runtime does not silently relabel or downgrade them.
- Events, debug bundles, telemetry, and API views are redacted by default according to classification.
- Current authorization is described as owner scoping, not strict multi-tenant isolation.

---

## Biological Analog

A cell membrane does not grant permanent access merely because a substance crossed an outer boundary once. Transport and compartment membranes continue to regulate where material may travel. Data classification likewise follows the payload and is checked at each consequential boundary.

---

## Digital Implementation

`DataClass` is a shared domain type rather than separate enums or strings in individual modules. Policy evaluation returns a typed allow, reject, or permitted-fallback result and emits a redacted audit event linked through ADR-010.

Tests cover propagation, aggregation, fallback, logging, durable snapshots, API redaction, and rejection immediately before invocation.

---

## Consequences

- Provider policy remains enforceable after transformations and routing changes.
- Classification becomes a required compatibility field across persistent schemas and APIs.
- Conservative propagation may over-classify derived data until audited declassification exists.
- Owner scoping reduces accidental cross-owner access but does not replace database-level tenant isolation.
- Local execution is a policy option only when an approved local runtime is actually configured.

---

## Alternatives Considered

**Use free-form labels:** Rejected because spelling and semantic drift make enforcement unreliable.

**Check classification only at request admission:** Rejected because later memory reads, aggregation, and rerouting can change the data crossing a provider boundary.

**Trust provider adapters to decide independently:** Rejected because policy would diverge and domain classification would leak into vendor-specific code.

**Automatically downgrade data when no permitted provider exists:** Rejected because availability must not override confidentiality.
