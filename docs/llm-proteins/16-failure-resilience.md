# §16 — Failure Handling & Resilience

## Core Principle
> **Failures should be isolated when possible, absorbed when practical, and escalated only when necessary.**

At organism scale, failure is not an exceptional event — it is an **expected operating condition**.

## 6 Failure Classes

| Class | Examples |
|---|---|
| **Execution** | Timeout, malformed response, schema violation, token budget exhaustion |
| **Dependency** | Upstream dependency failed or never completed |
| **Coordination** | Cells/tissues/organs fail to synchronise, aggregate, or converge |
| **State & Memory** | Context missing, stale, inconsistent, or corrupted |
| **Network & Transport** | Latency spikes, packet loss, provider connection issues, bandwidth saturation |
| **Policy & Governance** | Output violates policy/security/correctness constraints → must be blocked or remediated |

## Failure Scope (Containment Units)

| Scope | What's affected |
|---|---|
| **Protein-Scoped** | Single invocation fails; containing cell remains healthy |
| **Cell-Scoped** | Local coordination fails within a cell |
| **Tissue-Scoped** | Aggregation/consensus/role coordination breaks across cells |
| **Organ-Scoped** | Domain-level reasoning becomes degraded or inconsistent |
| **Organism-Scoped** | Global objectives, coordination, or output formation compromised |

Scoping failure correctly is critical for containment.

## Detection Mechanisms
- Timeout thresholds
- Schema and contract validation
- Contradiction/inconsistency checks
- Health probes for providers and internal services
- Staleness/freshness validation for state
- Abnormal latency or retry-rate detection

Failures detected as **close to their source** as possible.

## Local Recovery (First Resort)
- Protein retries with stricter schema guidance
- Cell substitutes alternative protein pathway
- Tissue reruns only the failed aggregation phase

Reduces cost and prevents unnecessary escalation.

## Retry Policy Parameters
- Retryable error classes
- Maximum retries
- Retry interval and backoff schedule
- Model fallback eligibility
- Deadline constraints

| Error Type | Strategy |
|---|---|
| Transient network timeout | Exponential backoff retry |
| Malformed structured output | Retry with stronger schema constraints |
| Repeated provider failure | Provider failover or deferment |

Retries are useful **only when the failure condition is likely to change**.

## 4 Fallback Paths

| Path | Description |
|---|---|
| **Horizontal** | Switch to another provider or equivalent tissue/component |
| **Vertical** | Switch to lower-fidelity or lower-cost execution path |
| **Structural** | Replace failing subgraph with alternative decomposition |
| **Partial** | Return bounded, incomplete, or lower-confidence result rather than failing |

## Graceful Degradation Examples
- Fewer validation passes under time pressure
- Local SLLMs replacing external LLMs for simple tasks
- Reduced context breadth when bandwidth constrained
- Simplified aggregation when full consensus unreachable

> The organism should **weaken intelligently before it breaks**.

## Escalation Logic
Occurs when: local retries exhausted · failure affects correctness/safety · lower layer cannot resolve ambiguity · policy intervention required.  

Path: `protein → cell → tissue → organ → organism`

Each escalation includes: failure metadata · attempted recoveries · affected dependencies · recommended next actions.

## Checkpointing & Replay
For long/complex execution paths:
- Preserve intermediate progress
- Replay only the failed segment
- Avoid re-running successful upstream work

Checkpoints at: cell aggregation boundaries · tissue synthesis boundaries · organ-level decision milestones.

## Isolation & Containment
- Scoped execution sandboxes
- Queue isolation by domain
- Concurrency domains
- Memory partitioning
- Timeout boundaries between layers

Prevents local failure from infecting the broader organism.

## 4 Resilience Modes

| Mode | When |
|---|---|
| **Normal** | All components operating under standard policies |
| **Degraded** | Some providers/tissues/organs impaired; fallback paths active |
| **Recovery** | Clearing backlogs, replaying checkpoints, rebuilding state |
| **Containment** | Fault isolated; surrounding layers reduce interaction until stable |

## Failure Budgets
Per-layer acceptable thresholds:
- Tolerated retry rate
- Acceptable partial-output rate
- Maximum latency inflation under degradation
- Allowable degraded execution window

## Example Flow
1. Reasoning tissue triggers 500 protein calls
2. Provider begins timing out; malformed responses increase
3. Protein-level retries attempted with bounded backoff
4. Cell reroutes simple tasks to local SLLMs
5. Tissue activates fallback aggregation; marks confidence as reduced
6. Organ requests narrower follow-up instead of full rerun
7. Organism produces partial but actionable output; failed provider isolated

Result: **reduced fidelity, not systemic failure**.
