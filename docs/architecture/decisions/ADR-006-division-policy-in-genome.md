# ADR-006: Division Policy Belongs in the Genome

**Status:** Accepted

---

## Context

Once the three-gate division model was established (ADR-005), the system needed to decide where the gate thresholds, allowed division modes, cooldown periods, and the master `can_divide` flag should live. Candidates were: the cell itself, the organism, or the genome.

---

## Decision

**The division policy lives in the genome. Cells do not decide to divide. They reach the state the genome was always waiting for.**

The genome encodes the conditions under which any cell of this organism is permitted to divide, which modes it may use, how often, and up to what generation. A cell that satisfies these conditions becomes eligible — it does not initiate division. The genome specifies the developmental trajectory; the cell's lived experience provides the measurements that determine when that trajectory's division point has been reached.

This is expressed as a `DivisionPolicy` block embedded in the `Genome` model. A genome with `division_policy: null` permits division unconditionally (backward-compatible default). A genome with a policy enforces all three gates at division time.

**Division policy schema:**
```
DivisionPolicy {
  can_divide: bool                       # Master kill switch
  gates: {
    load:       DivisionLoadGate         # Throughput threshold
    capability: DivisionCapabilityGate   # Quality + breadth threshold
    lifecycle:  DivisionLifecycleGate    # Generation + state + cooldown
  }
  allowed_modes: DivisionMode[]          # Which modes this genome permits
  preferred_mode: DivisionMode           # Default mode when eligible
  cooldown_ms: int                       # Minimum time between divisions of same parent
  max_daughters_per_division: int        # 2–4 daughters per split
}
```

---

## Biological Analog

In biology, the conditions governing whether and how a cell divides are encoded in the cell's DNA — specifically in genes for cyclins, cyclin-dependent kinases (CDKs), checkpoint proteins (p53, Rb, BRCA), and growth factor receptors. A neuron does not divide in adult tissue not because of its current state but because specific genes (CDK inhibitors) are expressed that permanently suppress the cell cycle. A cancer cell divides uncontrollably because tumor suppressor genes in its genome have been mutated or silenced.

The genome does not describe what is happening in the cell right now — it describes what the cell is allowed to do. The cell's environment and internal state determine whether the genomic conditions have been met. This is the core distinction:

- **Genome** = the rules for when division is permitted
- **Cell state** = the measurements that determine if those rules are currently satisfied

The digital division policy encodes the same principle. The genome declares the developmental rules. The cell's protein output, signal diversity, generation number, and lifecycle state are the measurements evaluated against those rules.

**Contact inhibition analog:** The `max_generation` field in the lifecycle gate is analogous to contact inhibition in biology — the mechanism by which normal cells stop dividing when surrounded by other cells. In the digital system, generation depth serves as a proxy for population density: beyond a certain generation, no further division is permitted regardless of load or capability.

---

## Digital Implementation

**`Genome` model (`models.py`):**
```python
class Genome(BaseConfigModel):
    genome_id: str
    version: int
    core_instruction_set: list[str]
    modules: list[GenomeModule]
    regulatory_rules: list[dict]
    capability_registry: dict
    constraints: dict
    division_policy: DivisionPolicy | None = None   # ← added
```

**Policy update endpoint:**
```
PATCH /api/genomes/{genome_id}/division-policy
body: { policy: DivisionPolicy }
response: { genome: Genome }
```

The policy is applied in-place on the genome store. It does not create a genome version — it modifies the active genome directly. This is intentional: the policy is an operational parameter of the genome, not a structural change to the instruction set or module configuration.

**Gate enforcement in `divide_cell` (engine):**
```python
if genome and genome.division_policy:
    policy = genome.division_policy
    if not policy.can_divide:
        raise ValueError("genome division policy prohibits cell division")
    if mode not in policy.allowed_modes:
        raise ValueError(f"mode '{mode}' not in allowed modes: {policy.allowed_modes}")
    readiness = self.check_division_readiness(organism_id, cell_id)
    if not readiness.eligible:
        raise ValueError(f"division gates not satisfied: {readiness.blocked_by}")
```

**Frontend:** The genome page's `Division Policy` tab exposes the full policy editor. The readiness check panel lets the operator evaluate any specific cell against the current policy before attempting division.

---

## Consequences

- Gate thresholds are versioned with the genome. Changing threshold values means updating the genome's division policy.
- A genome with `can_divide: False` produces a terminally non-dividing cell type — analogous to post-mitotic neurons or fully differentiated red blood cells.
- Changing `division_policy` takes effect immediately on the active genome. Existing cells already past the generation ceiling will not divide; no retroactive enforcement is needed.
- Organisms created before this policy was introduced have `division_policy: None` and retain unrestricted division behavior (backward compatible).
- Future genome versioning should track `division_policy` changes alongside structural changes.

---

## Rejected Alternatives

**Policy on the organism:** The organism holds the division policy and applies it across all cells. Rejected because organisms may eventually run multiple cell types (differentiated tissues) with different division behaviors. A single organism-level policy cannot express type-specific rules. The genome is the right level because each cell type can be assigned a distinct genome expressing a distinct policy.

**Policy on the cell:** Each cell carries its own division policy. Rejected because policy would need to be copied to every daughter cell and kept synchronized. Cells are ephemeral; the genome is persistent. Policy belongs in the persistent layer.

**No policy — always operator-controlled:** Division is always an explicit operator command with no system-level constraints. Partially retained: division is still operator-triggered (the system does not auto-divide). But without genome-level gates, the operator has no systematic way to define what "division-ready" means for a given organism type. The policy makes the developmental trajectory explicit and enforceable.
