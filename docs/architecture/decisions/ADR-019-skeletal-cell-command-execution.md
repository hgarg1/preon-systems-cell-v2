# ADR-019: Execute Structural Commands Through Skeletal Cells

**Status:** Accepted

## Context

Skeletal cells had durable identities, but runtime methods performed structural
behavior directly.

## Decision

Growth planning and application execute through osteoblasts, remodeling and
retirement through osteoclasts, and observation/reconciliation through
osteocytes. Internal commands use bounded execution and produce traced signals,
proteins, and durable skeletal runs. They do not pass through the external
membrane, and skeletal cells remain excluded from ordinary workload selection.

## Consequences

Structural provenance now identifies real executions. The skeleton remains a
control plane and does not proxy ordinary resource data.

## Alternatives Considered

Metadata-only cell attribution and routing all data through skeletal cells were
rejected.
