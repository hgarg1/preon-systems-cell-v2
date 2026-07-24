# ADR-020: Use a Transactional Outbox for Structural Effects

**Status:** Accepted

## Context

External mutation can succeed after an HTTP request fails, or fail after
approval is durable.

## Decision

Approval records the reviewed digest and a structural-effect outbox entry, then
returns `202 Accepted`. A bounded worker claims effects with leases, applies
them at least once through idempotent adapters, and records resources, grants,
observed state, attempts, and terminal status.

Expired leases are reclaimable. Retries are capped. Osteocyte reconciliation
observes drift but never authorizes an unreviewed destructive plan.

## Consequences

Approval and application are distinct states. Exactly-once external mutation is
not claimed; idempotent convergence is required.

## Alternatives Considered

Inline application was rejected due to ambiguous timeouts. Manual dispatch was
rejected because approved routine growth should progress automatically.
