# §13 — Task Decomposition & Orchestration

## Core Principle
> Problems are not solved all at once — they are **systematically decomposed** into the smallest useful units and **recomposed** into coherent results.

## Decomposition vs Orchestration (they are different)

| | Task Decomposition | Orchestration |
|---|---|---|
| **Answers** | What work needs to be done? | When, where, and how should that work happen? |
| **Concern** | Breaking a high-level objective into smaller units | Sequencing, routing, coordinating, supervising execution |

Without both: monolithic reasoning, uncontrolled parallelism, redundant work, or incoherent paths.

## 4 Decomposition Levels

| Level | Breaks down |
|---|---|
| **Organism** | Global objective → organ-specific domains |
| **Organ** | Domain objectives → tissue-specific functional tasks |
| **Tissue** | Functional tasks → cell-level reasoning problems |
| **Cell** | Reasoning problems → atomic protein executions |

## 4 Decomposition Strategies

| Strategy | Split by | Example |
|---|---|---|
| **Functional** | Capability or domain | research · reasoning · simulation · execution |
| **Temporal** | Sequential phases | gather data → analyse → validate → act |
| **Structural** | Problem structure | system components · modules · stakeholders |
| **Granularity-Based** | Until units are protein-executable | smallest useful atomic unit |

Multiple strategies may be applied simultaneously.

## Task Graph Structure
```yaml
Task:
  id: string
  parent_task: string
  owner_layer: organism|organ|tissue|cell|protein
  dependencies: []
  priority: high|medium|low
  constraints:
    latency_ms: 2000
    cost_tier: balanced
```

## Routing Logic
After decomposition, tasks routed based on: required capability · current load · latency requirements · cost constraints · model availability · specialisation.  
Routing is **dynamic** — may change mid-execution based on system conditions.

## 4 Orchestration Modes

| Mode | Description |
|---|---|
| **Directive** | Higher layer explicitly instructs lower layers |
| **Delegated** | Layer assigns subproblem, downstream self-coordinates |
| **Iterative** | Execution proceeds in loops with repeated refinement |
| **Opportunistic** | Work executed wherever capacity + capability immediately available |

These modes may **coexist** within the same execution path.

## Dependency Management
Types: data dependencies · control dependencies · validation dependencies · resource dependencies.  
Rules: independent work executes in parallel · blocked tasks wait without consuming resources · downstream tasks activate when prerequisites complete.

## Recomposition Path
```
Protein outputs → cell reasoning
Cell outputs    → tissue result
Tissue outputs  → organ intelligence
Organ outputs   → organism decision
```

Must preserve: semantic consistency · traceability to source work · alignment with original objective.

## Adaptive Replanning
The system supports replanning when: new information emerges · dependencies fail · intermediate outputs change scope · constraints tighten.  
May: alter the task graph · reroute tasks · inject new validation steps · terminate low-value subpaths.

## Granularity Control
- **Too coarse**: low parallelism, poor reuse, large expensive calls
- **Too fine**: overhead explosion, communication burden, coordination inefficiency

Target: **smallest useful executable unit**, not smallest possible unit.

## Priority & Urgency
High-value paths receive resources first. Signals: user-facing deadlines · organism-critical decisions · validation requirements · background optimisation work.

## Failure-Aware Orchestration
- Reroute around degraded tissues/organs
- Replay failed subgraphs
- Substitute lower-fidelity execution paths
- Generate partial outputs when full completion unavailable

## Memory & State Dependency
Decomposition relies on: prior execution history · cached intermediate artifacts · persistent memory · active organism objectives.  
Allows: avoiding redundant work · reusing prior reasoning · maintaining continuity.

## Example Flow
**Objective**: "Design and validate a new product pricing strategy"
1. Organism decomposes → market analysis, financial modeling, simulation, recommendation
2. Each organ routes to appropriate tissues and cells
3. Cells decompose to atomic protein operations
4. Outputs recomposed upward through tissues and organs
5. Organism synthesises final recommendation
6. Inconsistencies detected → orchestration layer replans selected subgraphs
