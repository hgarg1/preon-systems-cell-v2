# ADR-005: Cell Division Requires Three Co-Passing Gates

**Status:** Accepted

---

## Context

The system needed a mechanism to trigger cell division. Division is the primary growth mechanism: a single cell splits into two daughter cells, enabling load distribution, specialization, and organ formation. The question was what should trigger division — and what combination of signals constitutes sufficient readiness.

Proposed trigger models considered:
1. Biomass/size threshold alone
2. Intelligence/volitional threshold alone ("the cell wants to split")
3. A combination of measurable, objective conditions
4. External command only (operator-triggered)

---

## Decision

**Cell division requires three independent gates to pass simultaneously. All three must be green. Any single failing gate blocks division regardless of the state of the others.**

The three gates are:

**Gate 1 — Load Gate (environmental trigger)**
Is the organism producing enough output to make division productive? Measured as total proteins produced by the organism. If below the minimum throughput threshold, dividing would produce two idle cells. Division is not warranted.

**Gate 2 — Capability Gate (quality and breadth checkpoint)**
Has the organism demonstrated sufficient capability in terms of both output quality and signal diversity? Measured as: count of successful high-confidence proteins AND count of distinct signal types processed at that confidence level. Both must meet thresholds. A cell that has processed many signals of one type fails this gate — domain depth is not the same as generative sufficiency. A cell with broad but low-confidence outputs also fails.

**Gate 3 — Lifecycle Gate (structural safety check)**
Is the cell in a valid state to divide? Measured as: generation ≤ maximum (prevents runaway proliferation), lifecycle state matches required state (prevents division of hibernating or degraded cells), and cooldown elapsed since the parent cell's last division (prevents rapid re-division).

---

## Biological Analog

Cell division (mitosis) in biology is gated by the cell cycle — a series of checkpoints that must all pass before division proceeds:

| Biological checkpoint | What it checks | Digital gate |
|---|---|---|
| G1 checkpoint (restriction point) | Is the cell large enough? Enough nutrients? Growth factors present? | Load gate — is the organism processing enough work to warrant division? |
| S phase / G2 checkpoint | Is DNA fully replicated and undamaged? | Capability gate — has the genome been expressed sufficiently to seed two functional daughters? |
| M checkpoint (spindle assembly) | Are chromosomes properly attached to the spindle? | Lifecycle gate — is the cell in the correct structural state (active, right generation, past cooldown)? |

The critical biological principle: any checkpoint failure halts the entire cell cycle. A cell does not partially divide. If the DNA is damaged at the G2 checkpoint, the cell does not proceed to mitosis regardless of how large it has grown or how many growth factors are present. The gates are independent and all required.

---

## Digital Implementation

**`DivisionGates` model (`models.py`):**
```python
class DivisionLoadGate(BaseConfigModel):
    min_protein_throughput: int  # Total proteins organism must have produced

class DivisionCapabilityGate(BaseConfigModel):
    min_successful_proteins: int       # Successful proteins above confidence threshold
    min_distinct_signal_types: int     # Breadth: number of different signal types handled
    min_avg_confidence: float          # Quality: minimum average confidence across successes

class DivisionLifecycleGate(BaseConfigModel):
    max_generation: int                # Ceiling on how many times a cell lineage can divide
    required_lifecycle_state: str      # "active" — hibernating/degraded cells cannot divide
```

**Gate evaluation in `engine.py` (`check_division_readiness`):**
- Load gate: `len(proteins) >= min_protein_throughput`
- Capability gate: filter proteins by `valid and confidence >= threshold`, count distinct types, compute average confidence
- Lifecycle gate: generation check, state check, cooldown check against prior `CellDivisionRecord` timestamps

**Enforcement in `divide_cell`:** Gates are evaluated before any division logic executes. If any gate fails, a `ValueError` is raised with the specific failing gate names. The division does not proceed.

**Readiness API:** `GET /api/organisms/{id}/cells/{cell_id}/division-readiness` returns the full evaluation for each gate including measured values, pass/fail reason, and recommended division mode.

---

## Consequences

- Division is never triggered automatically. The system evaluates readiness on demand (operator check or future background evaluation) but does not self-divide.
- Gate thresholds are defined in the genome's `division_policy`, not hardcoded. Different genome configurations can produce different division behaviors.
- The load gate uses organism-level protein throughput as a proxy for cell load, because the current data model does not track per-cell signal queue depth.
- Very early organisms (few proteins produced) will never pass the load or capability gates. This is correct — premature division of an immature organism would produce two equally immature organisms with half the resource budget each.

---

## Rejected Alternatives

**Pure biomass/size threshold:** Division triggers when the cell accumulates enough "mass" — modeled as memory records, protein count, or stored state volume. Rejected because bulk without quality is not readiness. A cell that has accumulated many misfolded proteins, garbage signals, or low-confidence outputs should not divide — it would just produce two cells equally degraded. Mass without quality is not maturity.

**Pure volitional model ("the cell wants to split"):** Division triggers based on an internal signal of the cell's own readiness assessment. Rejected because "wanting" is not operationalizable or debuggable. What does it mean for a cell to want to divide? Under what conditions does wanting occur? This question has no clear answer without reducing it to measurable conditions — at which point it becomes the three-gate model anyway.

**External command only:** Division only occurs when the operator explicitly triggers it. Retained as the current implementation — division is always operator-triggered. The gates are enforced at the time of the trigger. Future work may add background evaluation that surfaces division eligibility to the UI automatically.

**Single composite score:** Combine all signals into one readiness score and divide when it exceeds a threshold. Rejected because independent gate failures have different meanings and different remedies. A failing load gate means "wait for more use." A failing capability gate means "diversify signal types." A failing lifecycle gate means "wait for cooldown or fix the cell's health." Collapsing these into one number loses the diagnostic signal.
