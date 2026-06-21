# §10 — Inter-Tissue Communication

## Core Principle
> Communication occurs through **structured intent**, not raw execution detail.

Inter-tissue communication enables cross-domain coordination while maintaining **abstraction boundaries** — tissues remain modular, complexity is contained, interfaces remain stable.

## What Tissues Expose (NOT raw internals)
- Structured outputs
- Summarised reasoning
- Confidence metrics
- Domain-specific representations

```json
{
  "intent": "analyze_market_trends",
  "result": {...},
  "confidence": 0.87,
  "summary": "..."
}
```

Other tissues consume this without needing to understand internal execution.

## 4 Interaction Patterns

| Pattern | Description |
|---|---|
| **Request–Response** | One tissue requests analysis/data from another |
| **Publish–Subscribe** | Tissues emit outputs that others subscribe to |
| **Feedback Loop** | Downstream tissues refine upstream tissue outputs |
| **Collaborative Iteration** | Multiple tissues iteratively refine a shared result |

## Bidirectional Communication
Example: research tissue provides data to reasoning tissue → reasoning tissue requests clarification → loop continues until convergence.

## Coordination Semantics
Each inter-tissue message carries:
- **intent** — what is being requested
- **scope** — which portion of the problem is addressed
- **constraints** — latency, cost, fidelity
- **expected output format**

## Data Contracts
Each tissue exposes:
- Input schema
- Output schema
- Expected behaviour

Enables: modular composition, independent evolution of tissues, easier debugging.

## Latency Considerations
Inter-tissue communication is slower than intra-tissue. Mitigations:
- Minimise cross-tissue requests
- Use parallelism where possible
- Leverage caching for repeated interactions

## State Sharing
Tissues may share: summarised state, references to shared data, pointers to cached results.  
They **do not** share full internal state — abstraction boundaries are preserved.

## Failure Handling

| Failure | Recovery |
|---|---|
| Incompatible outputs | Request retry |
| Missing data | Fallback to alternative tissue |
| Degraded upstream | Degraded execution path |
| Unresolvable | Escalate to organ-level coordination |

## Example Flow
1. Reasoning tissue needs external data
2. Sends structured request to retrieval tissue
3. Retrieval tissue processes and returns results
4. Reasoning tissue incorporates data
5. Additional clarification requests may follow
6. Final output produced after convergence

## Key Insight
This layer is the critical step from **isolated reasoning units** → **fully integrated intelligent system**. Controlled complexity, composable domains, scalable coordination.
