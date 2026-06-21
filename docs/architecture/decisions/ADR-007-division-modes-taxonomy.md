# ADR-007: Four Division Modes with Distinct Biological Purposes

**Status:** Accepted

---

## Context

Not all cell division serves the same purpose. A cell splitting to handle load has a different intent from a cell splitting to produce a specialist daughter, which is different again from a cell splitting to repair a dead neighbor. The system needed a taxonomy of division modes that correctly maps biological division types to digital purposes, with each mode producing meaningfully different outcomes.

---

## Decision

**Four division modes are defined. Each has a distinct biological analog, a distinct digital purpose, and a distinct set of conditions under which it is appropriate.**

| Mode | Biological analog | Digital purpose |
|---|---|---|
| `symmetric` | Mitosis producing two identical daughter cells | Load distribution — two identical workers share the queue |
| `asymmetric` | Stem cell division producing one stem cell + one committed progenitor | Capability inheritance + specialization — one daughter continues, one differentiates |
| `founder` | Organ-founding division — one daughter stays, one migrates to seed a new tissue | New cell type progenitor — seeds a new organ or tissue type |
| `repair` | Wound healing / tissue homeostasis — replacing a dead or damaged cell | Dead or degraded cell replacement, driven by health monitoring not load |

---

## Mode Definitions

### `symmetric` — Load Distribution

Both daughters are structurally identical copies of the parent. They inherit the same `expression_profile`, `cell_type`, `organ_id`, and `tissue_id`. The parent's `resource_budget` is split evenly between them. Generation increments by 1.

**Trigger context:** Load gate is the primary driver. The organism is processing more signals than one cell can handle efficiently. The goal is throughput, not differentiation.

**Biological analog:** Most somatic cell division — skin cells, intestinal epithelium, liver cells replacing worn tissue. Both daughters are functionally identical to the parent.

**Constraint:** Symmetric division produces two generalists. It does not increase the organism's capability range. Repeated symmetric division of a single cell type without differentiation produces a clonal mass with no new function — analogous to benign hyperplasia.

---

### `asymmetric` — Capability Inheritance + Specialization

One daughter (the "stem daughter") inherits the parent's expression profile and continues its role. The second daughter (the "committed daughter") begins differentiation — it carries a modified expression profile that upregulates expression of one module type and downregulates others. Generation increments by 1 for both. The committed daughter's `cell_type` may be updated to reflect its specialization trajectory.

**Trigger context:** Capability gate drives this. The parent has demonstrated breadth across multiple signal types and is now mature enough to produce a specialist. The genome's preferred mode is typically `asymmetric` because it produces functional diversity, not just capacity.

**Biological analog:** Stem cell division. A hematopoietic stem cell divides asymmetrically to produce one daughter that remains a stem cell and one that commits to becoming a red blood cell, a T cell, or a platelet. The stem cell property is not divided — it is retained in one daughter while the other begins a specialization program.

**Constraint:** The committed daughter's specialization trajectory must be specified by the genome's `capability_registry` or `differentiation_rules`. Without this, asymmetric division produces two cells with slightly different expression profiles but no defined developmental destination.

---

### `founder` — New Cell Type Progenitor

One daughter stays in the parent's organ and tissue, continuing the parent's role. The second daughter is a founder cell — it migrates out of the parent's tissue context and becomes the progenitor of a new organ or tissue type. The founder daughter receives a distinct `organ_id` and `tissue_id`, and its `cell_type` reflects the new organ it will seed.

**Trigger context:** Rare. Requires explicit genomic permission. Represents the organism deciding to build new structural capacity — a new organ, a new tissue layer. The founder daughter does not yet have peers; it is generation 0 of its new lineage.

**Biological analog:** During embryonic development, founder cells migrate from one tissue to seed new organs. Neural crest cells, for example, migrate from the neural tube to form peripheral nervous system ganglia, facial bones, and pigment cells. Each migration event is a founder division — one cell stays, one migrates and founds a new population.

**Constraint:** Founder division has organism-wide architectural consequences. A new `OrganRecord` and `TissueRecord` must be created to house the founder daughter. This mode should be gated behind both genomic permission and operator review. It is not appropriate for routine load scaling.

---

### `repair` — Dead or Degraded Cell Replacement

The division produces one daughter that is a functional replacement for a dead or degraded cell in the same organ and tissue. The parent cell is not the damaged cell — it is a healthy neighbor that divides to fill the gap. The daughter is assigned to the damaged cell's slot (same `organ_id`, `tissue_id`, `cell_type`). The dead cell is removed from the cell store.

**Trigger context:** Health monitoring, not load or capability. Triggered when a cell's `health_state` transitions to `DEAD` or `CellHealthState.DEGRADED` and the organ's target cell count is unmet. The repair division is initiated by a healthy adjacent cell, not by the damaged one.

**Biological analog:** Contact inhibition release in wound healing. When a cell dies, its neighbors detect the gap (loss of contact inhibition signals) and re-enter the cell cycle to replace it. The daughter of the dividing neighbor moves into the vacated space. This is distinct from growth — repair division stops when the gap is filled.

**Constraint:** Repair mode bypasses the load and capability gates. A healthy cell should always be permitted to repair a dead neighbor regardless of protein throughput or signal diversity. Only the lifecycle gate (generation ceiling, state check) applies to the parent cell in repair mode.

---

## Implementation Notes

**`DivisionMode` enum (`models.py`):**
```python
class DivisionMode(StrEnum):
    SYMMETRIC  = "symmetric"
    ASYMMETRIC = "asymmetric"
    FOUNDER    = "founder"
    REPAIR     = "repair"
```

**Genome policy controls which modes a given cell type may use:**
```python
division_policy.allowed_modes = [DivisionMode.SYMMETRIC, DivisionMode.ASYMMETRIC]
division_policy.preferred_mode = DivisionMode.ASYMMETRIC
```

**Current engine behavior:** `divide_cell` in `engine.py` currently implements the symmetric daughter structure for all modes (two copies with split resource budgets). Mode-specific daughter differentiation (expression profile mutation for asymmetric, organ assignment for founder, dead-cell slot replacement for repair) is architecture-ready but not yet fully implemented at the engine layer. The modes are enforced at the policy level; the downstream differentiation behavior is the next implementation milestone.

---

## Consequences

- The genome's `division_policy.preferred_mode` defaults to `asymmetric` because most productive divisions should produce functional diversity, not just capacity. Symmetric is the fallback.
- `repair` mode bypasses load and capability gates. This must be explicitly implemented in gate evaluation — repair divisions are health-driven, not capability-driven.
- `founder` mode requires additional infrastructure creation (organ + tissue records). Until that infrastructure step is automated, founder divisions should remain gated behind operator confirmation.
- A genome that lists only `["repair"]` in `allowed_modes` produces a terminally non-proliferating but self-repairing cell type — analogous to a post-mitotic neuron that can regenerate damaged synaptic machinery but cannot reproduce.
