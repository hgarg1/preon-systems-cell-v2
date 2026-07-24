# ADR-018: Use a Modular Runtime with Ports and Adapters

**Status:** Accepted

## Context

`engine.py` accumulated execution, lifecycle, memory, skeletal growth, policy,
reproduction, persistence coordination, and telemetry.

## Decision

Keep one deployable modular monolith, but place domain behavior behind focused
services and typed ports. Provider and persistence implementations are adapters
selected by one composition root. `OrganismRuntime` remains a compatible facade,
while `preon_systems_cell.engine` contains only stable re-exports.

## Consequences

- Existing callers retain their imports.
- Domain behavior can be tested without FastAPI or PostgreSQL.
- Infrastructure dependencies point inward.
- No distributed-service boundary is introduced.

## Alternatives Considered

Continuing one engine class was rejected due to coupling. Microservices were
rejected because their operational cost has no present benefit.
