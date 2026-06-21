# §6 — Concurrency & Execution Model

## Core Principle
> **Maximise *useful* parallelism, not raw parallelism.**

Useful parallelism = tasks execute concurrently only when dependencies allow, requests paced to provider + network limits, work routed to lowest-cost capable model, no more parallel work than downstream can absorb.

## Execution Hierarchy (Concurrency is managed at ALL layers)

| Layer | Scope of control |
|---|---|
| **Protein** | Local invocation count, retries, token budgets, response handling |
| **Cell** | Scheduling proteins, deduplication, local queues |
| **Tissue** | Cross-cell dependency resolution, aggregation timing |
| **Organ** | Domain workload prioritisation, redistribution across tissues |
| **Organism** | Global execution policy, fairness constraints, system-wide backpressure |

## Task States
`queued → ready → running → waiting_on_dependency → retry_pending → completed / failed / deferred`

## Dependency-Aware Scheduling (DAG)
- Tasks with no unmet dependencies execute immediately
- Blocked tasks remain dormant
- Independent tasks execute in parallel
- Aggregation tasks activate only when quorum/dependency threshold met

## Concurrency Domains
Execution partitioned by: protein type, cell, tissue, provider, organ, tenant/workload.  
Each domain defines: max concurrent tasks, max req/sec, token throughput limits, priority rules.

## Provider-Aware Throttling
Runtime continuously tracks: request rate, token rate, error rate, latency inflation, quota windows.  
Responses: slow dispatch · reroute to alternate providers · shift simple tasks to SLLMs · batch calls · defer low-priority.

## Network Preservation Strategy
1. **Prompt Size Minimisation** — only minimum required context transmitted
2. **Request Coalescing** — compatible tasks merged into fewer calls
3. **Batched Dispatch Windows** — grouped into short scheduling windows to smooth bursts
4. **Streaming for Long Responses** — avoids large buffered payload spikes
5. **Local Model Offloading** — low-complexity tasks to local/nearby SLLMs
6. **Payload Reuse & Caching** — repeated context fragments reused, not retransmitted

## Adaptive Concurrency Control
Limits adjust dynamically based on live signals:
- provider latency p95 increases → reduce max_parallel_calls
- local queue depth exceeds threshold → increase local_sllm_usage
- downstream aggregators lag → slow upstream fan-out

## Backpressure Propagation
Backpressure is **first-class**. Overloaded layer signals pressure upward and sideways.  
May trigger: upstream throttling · task deferral · lower-fidelity model routing · reduced prompt sizes · stricter batching.

## Queue Types

| Queue | Purpose |
|---|---|
| **Priority** | Urgent tasks dispatched ahead of lower-value work |
| **Domain** | Separated by tissue / organ / provider / tenant |
| **Retry** | Failed tasks under controlled backoff |
| **Deferred** | Non-urgent work held until capacity available |

## Batching & Coalescing
Combine: similar retrieval requests, repeated classification, shared context across subtasks.  
**But**: batching is *selective* not universal — over-batching creates oversized prompts, reduced traceability, slower urgent responses.

## Locality of Execution
Keep computation close to where context already exists:
- Lightweight transforms → in-cell
- Shared aggregation → tissue layer
- Simple inference → local SLLMs

## Retry Policy

| Error | Response |
|---|---|
| Transient provider error | Retry with backoff |
| Repeated timeout | Reroute or defer |
| Malformed output | Retry with stricter schema guidance |
| Persistent failure | Escalate to higher layer |

Retry budgets are explicitly bounded — poorly governed retries amplify congestion.

## Execution Modes

| Mode | When |
|---|---|
| **Burst** | Short-lived, high-priority execution spikes |
| **Steady-State** | Sustained organism operation under predictable load |
| **Degraded** | Provider / network / compute conditions constrained |
| **Recovery** | After failure events or backlog accumulation |

## Key Observability Metrics
in-flight requests · queue depth by domain · p50/p95/p99 latency · retry frequency · provider saturation rate · network egress volume · token throughput per layer · completion rate by task class · backpressure events

## Example Flow
1. Organ decomposes task → 300 cell-level subtasks → 2,000 protein operations
2. Scheduler identifies 1,100 dependency-free tasks
3. Provider-aware throttling limits safe external dispatch
4. Low-complexity tasks rerouted to local SLLMs
5. Similar retrieval requests coalesced
6. Tissue-level backpressure slows upstream fan-out
7. Completed outputs promoted upward for synthesis

Result: high concurrency without network/provider collapse.
