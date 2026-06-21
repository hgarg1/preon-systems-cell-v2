# §17 — Observability & Telemetry

## Core Principle
> Every meaningful decision, transition, and execution event should be **traceable at the appropriate level of abstraction**.

Not logging every token indiscriminately — capturing enough structured telemetry to reconstruct behaviour, explain outcomes, and improve performance without overwhelming the system.

## 5 Observability Objectives

| Question | Answered by |
|---|---|
| **What happened?** | Execution traces, state transitions, emitted outputs |
| **Why did it happen?** | Routing logic, conflict resolution paths, policy decisions |
| **How well did it happen?** | Latency, throughput, cost, success rate, confidence quality |
| **What failed or degraded?** | Retries, fallbacks, contention, error propagation |
| **How can it improve?** | Bottleneck analysis, drift detection, execution optimisation |

## 5 Telemetry Categories

| Category | What it captures |
|---|---|
| **Execution** | Task start/end times, state transitions, model invocations, retry/fallback events |
| **Communication** | Intra-cell events, inter-tissue requests/responses, organ coordination flows |
| **Resource** | Token usage, bandwidth, queue depth, in-flight requests, memory hit/miss rates |
| **Quality** | Confidence scores, validation pass/fail, contradiction detections, consensus convergence |
| **Governance** | Policy checks, redactions, routing restrictions, blocked outputs |

## Hierarchical Tracing Model
```
Trace:
  organism_request_id: req_123
  organ_spans:
    - brain_01
    - simulation_02
  tissue_spans:
    - planning_tissue_04
    - validation_tissue_09
  cell_runs:
    - cell_abc
  protein_calls:
    - protein_xyz
```

Creates a trace tree: high-level objective → decomposition path → execution graph → final output.

## Event Model
Structured events for all meaningful activity:
- task queued / activated
- model selected
- output normalised
- consensus failed
- fallback triggered
- checkpoint restored
- policy violation blocked

Each event: timestamped, typed, linked to trace identifiers.

## Metrics by Layer

| Layer | Key Metrics |
|---|---|
| **Protein** | Invocation latency, token usage, success/failure rate, schema compliance |
| **Cell** | Aggregation latency, local concurrency saturation, duplicate suppression rate |
| **Tissue** | Consensus convergence rate, iteration count, aggregation overhead |
| **Organ** | End-to-end reasoning latency, domain output confidence, cross-tissue coordination efficiency |
| **Organism** | Global objective completion rate, final output latency, cost per objective, degraded-mode frequency |

## Logs vs Traces vs Metrics

| Type | Purpose |
|---|---|
| **Logs** | Detailed records of discrete events or anomalies |
| **Traces** | Causal execution paths across multiple components |
| **Metrics** | Aggregated quantitative signals over time |

All three required: logs explain detail · traces explain flow · metrics explain system health.

## Replayability
System can reconstruct/replay portions of execution using: trace metadata · checkpointed state · prompt packages · routing decisions · normalised outputs.

Replay modes:
- Full-flow replays
- Subgraph replays
- Simulation-only replays (no external side effects)

## Explainability by Layer

| Audience | Layer | Purpose |
|---|---|---|
| Platform engineers | Protein/Cell | Low-level debugging and optimisation |
| Systems engineers, model architects | Tissue/Organ | Reasoning analysis |
| Operators, product owners, governance reviewers | Organism | Final decision explainability |

## Bottleneck Analysis
Common bottlenecks identified: provider latency spikes · network saturation · slow aggregation · repeated retries · oversized contexts · conflict loops with poor convergence.

Attribution by: layer · organ/tissue · provider · task class · execution mode.

## Drift & Anomaly Detection
Triggered by: unexpected token cost increases · slower consensus convergence · declining confidence calibration · repeated fallback activation in one domain · unusual tissue disagreement patterns.

Responses: alerts · degraded-mode activation · routing adjustments · targeted evaluation runs.

## Decision Provenance
Every organism-level decision has provenance:
- Contributing organs and tissues
- Major intermediate outputs
- Evidence sources used
- Consensus and adjudication paths
- Policy checks applied
- Final confidence and uncertainty signals

## Privacy & Security
- Sensitive payloads may be hashed, summarised, or redacted
- Raw prompts/outputs restricted to approved environments
- Access to traces may differ by role
- Observability increases visibility without compromising governance

## Retention & Sampling
- Retention tiers by event class
- Selective sampling for high-volume traces
- Full-fidelity capture for high-risk paths
- Summarised rollups for older operational data

## Operational Dashboards
- Organism health
- Organ and tissue performance
- Provider utilisation
- Failure and fallback
- Cost and token efficiency
- Governance and policy events
