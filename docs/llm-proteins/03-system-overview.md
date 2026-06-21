# §3 — System Overview

## The 8-Step Execution Cycle

```
1. Problem Ingestion      (Organism)  — receives high-level task/objective
2. Task Decomposition     (Organ)     — breaks into domain-specific subproblems
3. Functional Distribution (Tissue)   — assigns subtasks to specialised tissues
4. Task Breakdown         (Cell)      — decomposes into atomic operations
5. Execution              (Protein)   — fires LLM/SLLM calls
6. Aggregation            (Tissue)    — merges, validates, refines results
7. Synthesis              (Organ)     — combines into domain-level conclusions
8. Decision Formation     (Organism)  — produces final structured output
```

This process is **iterative** — multiple feedback loops may occur between steps.

## Continuous Operation Model
Unlike request-response systems, Preon runs as a **persistent execution environment**:
- Systems remain continuously active (not invoked per call)
- State evolves over time
- Tasks triggered by external inputs, internal signals, or feedback loops
- Enables long-running reasoning, adaptive behaviour, incremental improvement

## Distributed Intelligence
- **Distributed**: no single component has full context
- **Collaborative**: outputs produced through coordination
- **Hierarchical**: higher layers guide lower layers

> No individual Protein or Cell is "intelligent" in isolation — the system becomes intelligent through interaction.

## OrganismOS (Execution Runtime)
The implicit runtime that wraps all components. Responsible for:
- Task scheduling and orchestration
- Concurrency management
- Communication routing
- State and memory coordination
- Fault tolerance and retries

Ensures proteins execute efficiently, system-wide constraints are enforced, and coordination across layers is consistent.

## Concurrency as a First-Class Primitive
- Execute thousands of protein tasks in parallel
- Dynamically adjust execution rates
- Balance latency / cost / throughput
- Prevent API saturation, network bottlenecks, resource contention

## Communication Topology
Not a pipeline — a **mesh**:
- **Horizontal** (within layers): protein ↔ protein, cell ↔ cell
- **Vertical** (across layers): protein → cell → tissue → organ → organism
- **Bidirectional**: higher layers provide guidance; lower layers return results and feedback

## Emergent Behaviour
The system is explicitly designed for emergence:
- Multiple proteins executing in parallel
- Intermediate results aggregated + refined
- Higher-level coordination shaping execution

Allows the system to solve problems beyond the capability of individual models, adapt dynamically, and improve over time.
