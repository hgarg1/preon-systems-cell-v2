# §5 — Model Interface Layer

## Purpose
The abstraction boundary between proteins and external/local model providers. Ensures model access is standardised, observable, policy-governed, and resilient.

Without this layer: proteins couple directly to providers → brittle, non-reusable, inconsistent.

## Responsibilities
request normalisation · provider abstraction · model routing · prompt packaging · token budgeting · retry + fallback logic · response normalisation · telemetry

## Provider Abstraction
Proteins never talk to providers directly. All calls pass through a unified abstraction hiding:
- Request formats, auth methods, rate limit semantics
- Latency behaviour, streaming protocols, response schemas

```yaml
ModelRequest:
  task_type: reasoning
  capability_profile: medium_high
  latency_target_ms: 1500
  cost_tier: balanced
  context_payload: ...
```

## Model Classes

| Class | Used for | Trade-off |
|---|---|---|
| **Frontier LLMs** | Deep reasoning, synthesis, ambiguity, long-horizon inference | Highest capability, highest cost + latency |
| **SLLMs** | Simple transforms, routing support, lightweight reasoning | Lower cost + latency, lower reasoning depth |
| **Domain-Specialised** | Code gen, retrieval ranking, classification, simulation | Optimised for narrow tasks, high efficiency in scope |

## Routing Policy
Policy-driven, not hard-coded. Considers:
- Task complexity, latency target, cost constraints, token budget
- Concurrency pressure, provider health, historical performance

```python
if task_complexity == low and latency_target_ms < 500:
    use: local_sllm
elif task_complexity == medium and cost_tier == balanced:
    use: mid_tier_llm
else:
    use: frontier_llm
```

## Prompt Packaging
Standardised structure for every request:
```json
{
  "instruction": "Perform a bounded reasoning step on the provided subproblem.",
  "context": {
    "inputs": ["..."],
    "previous_outputs": ["..."]
  },
  "constraints": {
    "max_tokens": 400,
    "style": "structured_json",
    "temperature": 0.2
  }
}
```
Improves interoperability, auditing, replayability.

## Token Budgeting
Explicitly assigned per request based on: protein type, task priority, system-wide load, organ-level policy.  
Enforced for: input context size, output size, retry attempts.  
Prevents uncontrolled cost expansion.

## Fallback & Failover Strategy

| Strategy | Trigger |
|---|---|
| **Horizontal Fallback** | Switch to another provider with similar capability |
| **Vertical Fallback** | Downgrade to smaller model when constraints tighten |
| **Escalation** | Retry with *more* capable model if output insufficient |
| **Deferred Execution** | Delay if conditions are poor and task is non-urgent |

## Streaming vs Buffered Responses

| Mode | Use when |
|---|---|
| **Buffered** | Small outputs, downstream needs complete result, determinism preferred |
| **Streaming** | Large responses, latency-to-first-token matters, downstream can process partial results |

## Response Normalisation
All provider outputs normalised to common internal form:
```json
{
  "content": "...",
  "structured_output": {},
  "confidence": 0.81,
  "token_usage": { "input": 240, "output": 120 },
  "latency_ms": 1320,
  "provider": "...",
  "model": "..."
}
```

## Backpressure Awareness
Reacts to: too many in-flight requests, rising provider latency, network saturation, token budget exhaustion.  
Responses: reduce parallel volume · reroute to SLLMs · shorten prompts · batch requests · defer low-priority calls.

## Security & Governance Controls
- Provider allowlists, data classification rules, redaction policies
- Output validation requirements, audit logging
- Sensitive workloads → private endpoints, local models, isolated environments

## Example Invocation Flow
1. Protein receives atomic task
2. MIL evaluates routing policy
3. Prompt package assembled
4. Token budget assigned
5. Provider/model invoked
6. Output normalised
7. Telemetry emitted
8. Result returned to cell
