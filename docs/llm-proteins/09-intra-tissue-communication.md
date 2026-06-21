# §9 — Intra-Tissue Communication

## Core Principle
> Many cells contribute, but the tissue speaks with a single, unified voice.

A tissue is where collective intelligence first becomes **structurally meaningful**. It transforms parallel cell execution into coherent, domain-level intelligence consumable by organs.

## Communication Topologies

| Topology | How | Best for |
|---|---|---|
| **Hub-and-Spoke** | Central aggregator collects cell outputs | Simple aggregation tasks |
| **Distributed Mesh** | Cells share intermediate results with peers | Iterative refinement |
| **Hierarchical Aggregation** | Sub-groups aggregate locally, then up | Large cell counts, hierarchical tasks |

The system may dynamically switch between topologies based on workload.

## Data Exchange Format
Structured representations, never raw text:
```json
{
  "result": "...",
  "confidence": 0.0,
  "reasoning_trace": [],
  "metadata": {}
}
```
Enables: comparability, aggregation/ranking, validation, auditing.

## 5 Aggregation Strategies

| Strategy | How |
|---|---|
| **Simple** | Concatenate or merge outputs |
| **Weighted** | Combine based on confidence scores |
| **Majority Voting** | Select most common/agreed result |
| **Ranking & Selection** | Rank outputs, pick best candidate |
| **Synthesis** | Combine multiple outputs into a new refined result |

## Consensus Formation
When cells produce divergent outputs:
- Confidence-weighted voting
- Cross-validation between cells
- Evaluation proteins score outputs
- Iterative refinement loops

Consensus may be **strict** (single answer) or **probabilistic** (multiple candidates retained).

## Iterative Refinement Loop
1. Cells generate initial outputs
2. Results aggregated
3. Discrepancies identified
4. Cells re-invoked with updated context
5. Refined outputs produced

Continues until: convergence, confidence threshold met, or resource limits reached.

## Coordination Roles (Logical, Not Fixed)

| Role | Function |
|---|---|
| **Producer Cells** | Generate primary outputs |
| **Evaluator Cells** | Assess quality and correctness |
| **Aggregator Cells** | Merge and reconcile outputs |
| **Coordinator Cells** | Manage execution flow and iteration |

Cells may dynamically assume roles based on context.

## Tissue-Level State
- Aggregated outputs
- Intermediate consensus states
- Execution history
- Validation metrics

May be partially persisted, versioned for traceability.

## Latency vs Throughput Tradeoffs
- Higher accuracy → higher latency
- Deeper validation → increased cost

The system dynamically balances speed / quality / resource constraints.

## Failure Handling
- Inconsistent outputs → re-execute specific cells
- Insufficient consensus → fallback aggregation methods
- Degraded cell performance → escalate to organ-level reasoning

## Example Flow
1. Tissue receives domain-specific task
2. Task distributed across multiple cells
3. Cells independently generate outputs
4. Outputs collected by aggregators
5. Conflicts identified
6. Evaluation cells score candidates
7. Unified result synthesised
8. Tissue emits structured output
