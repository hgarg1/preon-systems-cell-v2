# §4 — LLM Protein Architecture

## What a Protein IS / IS NOT

| IS | IS NOT |
|---|---|
| Stateless or semi-stateful at execution time | Long-term planner |
| Highly parallelisable | Global coordinator |
| Governed by strict resource constraints | Multi-stage reasoner beyond bounded scope |

## Internal Structure

```yaml
Protein:
  id: string
  type: enum                        # see Protein Types below
  model_interface:
    provider: string
    model: string
    routing_policy: object
  execution_policy:
    timeout_ms: int
    retry_policy: object
    max_tokens: int
  memory_scope:
    context_window: object
    ephemeral_state: object
  communication_interface:
    input_schema: object
    output_schema: object
  concurrency_controller:
    max_parallel_calls: int
    rate_limits: object
```

## 5 Protein Types

| Type | Function |
|---|---|
| **Reasoning** | Logical steps, intermediate conclusions |
| **Retrieval** | Web/API queries, fetching structured or unstructured data |
| **Transformation** | Reformat, clean, structure data |
| **Aggregation** | Combine outputs from multiple proteins |
| **Evaluation** | Score, validate, rank outputs |

These types compose within cells to achieve higher-order functionality.

## Execution Lifecycle

```
1. Activation       → triggered by cell-level scheduler
2. Context Assembly → relevant state + inputs injected
3. Model Invocation → API call to LLM or SLLM
4. Post-Processing  → output normalisation + validation
5. Emission         → result published to communication layer
6. Termination      → execution ends; state optionally persisted
```

## Context & Memory Model
- Proteins operate with **limited context**: context window + ephemeral state only
- They do **not** maintain long-term memory directly
- Memory managed at higher layers (cells/tissues); proteins are **rehydrated** per execution

## Concurrency Control (Protein-Level)
Each protein enforces local constraints to prevent API throttling, runaway cost, network congestion:
```
max_parallel_calls: 10
tokens_per_minute: 100000
```

## Communication Interface

**Input schema** — defines required inputs, ensures type safety  
**Output schema** — standardised output enabling downstream processing:
```json
{
  "result": "string",
  "confidence": 0.0,
  "metadata": {}
}
```

## Error Handling & Retries
- Retry with exponential backoff
- Switch models if needed
- Return partial results when possible
- Propagate failures upward for higher-level resolution

## Observability Hooks
Each execution emits: latency, token usage, success/failure, model used.

## Design Constraints
- Bounded execution time
- Deterministic interfaces
- Minimal side effects
- Composable across cells

## Key Insight
Proteins are **intentionally simple in isolation** — complexity emerges through structured coordination across the system.
