# Living Skeleton and Structural Resource Growth

Phase 5A makes infrastructure growth organism-owned and cellular. It is the substrate for Phase 5B durable memory and later database, object-storage, queue, topic, contract, and adapter needs.

## Two meanings of bone

The runtime retains two intentionally separate concepts:

1. A **capability bone** is a `BoneContract`: the stable statement of what the organism can do. An enzyme supplies its current deterministic implementation.
2. A **structural bone** is a `BoneStructureRecord`: persistent infrastructure created and maintained for an organism.

An enzyme is not structural bone. Data stored in a structural resource is not bone either; for example, the `memory_records` table is structural bone while each `MemoryRecord` row is organism memory.

## Skeletal cells

Every new organism has a `skeletal` tissue with:

| Cell type | Responsibility |
|---|---|
| `osteoblast` | Plan growth and apply an approved growth plan |
| `osteoclast` | Plan remodeling or retirement and apply it only after approval |
| `osteocyte` | Observe health and record reconciliation outcomes |

They are ordinary `CellRecord` objects and participate in persistence, ownership, health, wake/hibernate, resource budgeting, and runtime events.

## Control plane and data plane

The skeletal control plane plans, approves, applies, observes, and grants access to structure. It does not proxy ordinary reads and writes.

```text
Structural need
  -> skeletal cell proposal
  -> deterministic plan + digest
  -> approval
  -> provider apply
  -> observed structural resource
  -> scoped ResourceGrant

Ordinary cell
  -> validates its ResourceGrant
  -> uses the provider data-plane adapter directly
```

`ResourceGrant` records contain no secret. `credential_ref` is an opaque reference for a future secret broker; it must never contain credential material.

## HTTP surface

- `GET /api/organisms/{organism_id}/skeleton`
- `POST /api/organisms/{organism_id}/skeleton/proposals`
- `POST /api/bones/proposals/{proposal_id}/approve`
- `POST /api/bones/proposals/{proposal_id}/reject`
- `POST /api/organisms/{organism_id}/skeleton/grants/{grant_id}/revoke`

The existing unscoped `/api/bones` and `/api/bones/proposals` APIs remain for backward compatibility.

An organism-scoped growth request can name the intended substrate without causing an unreviewed external effect:

```json
{
  "name": "organism-memory",
  "structure_type": "database_schema",
  "operation": "grow",
  "provider": "postgres",
  "definition": {
    "schema": "organism_memory",
    "namespace": "organism-123"
  },
  "target_cell_id": "cell-123",
  "requested_permissions": ["read", "write"],
  "idempotency_key": "organism-123:memory-schema:v1"
}
```

The approval request may include the returned `plan_digest`. If it does, a changed or stale plan is rejected.

## Provider boundary

Providers implement:

- `plan`: pure and side-effect-free
- `apply`: idempotent application of an approved plan
- `inspect`: current observed state

The Phase 5A `InMemoryStructuralProvider` proves lifecycle behavior without interpreting `provider="postgres"` or `provider="s3"` as permission to mutate live infrastructure. Live providers require contract tests, credentials supplied outside model state, reconciliation after partial failure, and deployment-specific approval policy.

## Phase 5.5 execution and effects

Planning and provider application now leave skeletal-cell run/protein
provenance. Approval queues an outbox effect. A bounded worker applies effects
idempotently, records attempts, and supports osteocyte reconciliation.

Live providers use `PREON_STRUCTURAL_DATABASE_URL` or the
`PREON_S3_ENDPOINT_URL`, `PREON_S3_REGION`, `PREON_S3_BUCKET`,
`PREON_S3_ACCESS_KEY_ID`, and `PREON_S3_SECRET_ACCESS_KEY` settings.
`pytest -m integration` runs opt-in real-provider tests when test endpoints are
configured.

## Phase 5B memory integration

Durable memory must request a database schema/table/index resource and access grant through this subsystem. Memory rows remain governed organism state and are never inserted into `bone_structures`.
