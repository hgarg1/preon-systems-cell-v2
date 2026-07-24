# ADR-015: Use Governed Structural Resources and Scoped Access Grants

**Status:** Accepted

---

## Context

An organism must be able to grow relational schemas, tables, object-storage namespaces, queues, topics, service contracts, and adapters. It must also let ordinary cells use those resources without turning the skeletal subsystem into a proxy for every database or blob operation.

External provisioning is side-effecting and may be partial. Raw provider credentials cannot safely live in cell state, proposals, events, or API responses.

---

## Decision

Represent persistent structure as a desired-state resource with provider identity, opaque provider reference, observed state, generation, health, organism ownership, and creating skeletal cell.

All structural changes follow one lifecycle:

1. A skeletal cell creates a side-effect-free plan.
2. The runtime hashes and persists the exact plan.
3. Policy or an operator approves that plan digest.
4. A provider adapter applies it idempotently.
5. An osteocyte records observed state and health.

Ordinary cells receive scoped `ResourceGrant` records containing resource identity, allowed operations, namespace, provider, ownership, and lifecycle status. Credentials are referenced opaquely and are never returned as grant data.

Destructive remodeling and retirement always require an osteoclast proposal and explicit approval. The initial provider is deterministic and in-memory; PostgreSQL persists the control-plane records. Real PostgreSQL, S3, Azure Blob, and other provisioning adapters must implement the same plan/apply/inspect boundary before they may mutate external infrastructure.

---

## Biological Analog

Bone provides a stable matrix and protected access paths. Other tissue uses the resulting structure; it does not ask an osteoblast to mediate every movement through it.

---

## Consequences

- Database and object-storage growth share one provider-neutral contract.
- Resource use is organism- and cell-scoped without centralizing data-plane traffic.
- Approval, plan hashing, idempotency, and reconciliation are testable before cloud credentials exist.
- Phase 5B memory can request its storage through this control plane.
- Live external provisioning remains a production-hardening gate, not an implied effect of setting `provider="s3"` or `provider="postgres"`.

---

## Alternatives Considered

**Give cells provider credentials directly:** Rejected because credential scope, revocation, ownership, and audit would be inconsistent.

**Route all reads and writes through skeletal cells:** Rejected because it creates a bottleneck and confuses structural governance with application data access.

**Provision immediately when a need is detected:** Rejected because plans may be destructive, costly, insecure, duplicated, or only partially applied.

## Phase 5.5 Provider Boundary

PostgreSQL and S3-compatible adapters now implement this contract. PostgreSQL
accepts only structured schema/table/index definitions with allowlisted types;
proposal-supplied SQL is never executed. S3 uses organism namespaces and marker
objects. Credentials come from environment configuration and never enter
proposals, grants, events, or provider references.
