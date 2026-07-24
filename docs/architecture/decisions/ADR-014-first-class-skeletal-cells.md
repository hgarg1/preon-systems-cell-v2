# ADR-014: Model Skeletal Roles as First-Class Cells

**Status:** Accepted

---

## Context

The runtime has two incomplete meanings for bone. `BoneContract` describes a deterministic capability, while `BoneStructureRecord` describes infrastructure. Osteocyte and osteoclast behavior also exists as helper objects owned by the process rather than as cells owned by an organism.

The biological model comes first: structure grows with an organism because specialized cells create, monitor, and remodel it. A process-global helper cannot have an organism identity, genome, lifecycle, health, resource budget, or traceable lineage.

---

## Decision

Each organism is born with a skeletal tissue containing three specialized `CellRecord` instances:

- An **osteoblast** proposes and applies approved structural growth.
- An **osteoclast** proposes and applies approved remodeling or retirement.
- An **osteocyte** observes structural health and records reconciliation outcomes.

Growth proposals must identify the organism and osteoblast cell that produced them. Remodeling and retirement proposals must identify an osteoclast. These cells participate in ordinary wake, hibernate, health, persistence, ownership, event, and trace behavior.

`BoneContract` remains a capability contract satisfied by an enzyme. Persistent infrastructure is a structural bone resource. Enzymes are implementations, not cells or structural resources.

---

## Biological Analog

Osteoblasts form bone matrix, osteoclasts resorb and remodel it, and osteocytes live in established bone and sense its condition. The matrix is the structure they produce; it is not the cell itself.

---

## Consequences

- Structural changes have a concrete organism-owned actor.
- New organisms have three additional core cells.
- Existing capability-bone helpers remain compatible, but infrastructure growth no longer treats them as the actor.
- Rich skeletal genomes and autonomous repair remain future work; Phase 5A starts with deterministic behavior and explicit approval.

---

## Alternatives Considered

**Keep skeletal roles as process-global helpers:** Rejected because structure could not grow with, belong to, or die with a specific organism.

**Represent infrastructure records themselves as cells:** Rejected because cells create and maintain structural material; the material is not a cell.
