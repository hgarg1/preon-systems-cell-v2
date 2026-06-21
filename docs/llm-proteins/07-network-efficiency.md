# §7 — Network Efficiency & Throughput Optimisation

## Core Principle
> Optimise for **information density**, not raw request volume.

At organism scale, the dominant bottleneck is often not compute — it's **network movement of data**.

## Prompt Size Minimisation

| Technique | How |
|---|---|
| **Context Pruning** | Only include strictly relevant context |
| **Token Compression** | Abbreviate structured data, encode repeated patterns |
| **Semantic Referencing** | Reference cached/computed artifacts instead of resending full context |
| **Layered Context Injection** | Different layers receive different context scopes, not full system state |

## Response Size Optimisation
- Enforce structured output schemas
- Limit verbosity via prompt constraints
- Truncate non-essential content
- Request summaries instead of raw outputs

## Caching Strategy

| Cache Type | What it stores |
|---|---|
| **Result Cache** | Identical inputs → reused outputs |
| **Partial Computation Cache** | Intermediate reasoning steps |
| **Template Cache** | Prompt structures without retransmission |
| **Retrieval Cache** | Previously fetched external data |

## Request Deduplication
Detect duplicate or near-duplicate tasks across proteins → issue one request, share result across all dependents.  
Critical in: large fan-out reasoning, repeated retrieval operations.

## Batching & Multiplexing
- **Batching**: multiple logical tasks → single model invocation
- **Multiplexing**: multiple requests → shared transport channel

Bounded to avoid: oversized prompts, delayed responses, coupling unrelated tasks.

## Streaming Optimisation
Reduces perceived latency and avoids large payload spikes.  
Use for: long reasoning chains, large text outputs.

## Local Execution Preference
> Move computation to data, not data to computation.

- SLLMs for lightweight tasks
- In-memory transformations
- Local aggregation

Reduces: network usage, latency, reliance on external providers.

## Data Locality
Keep related data and computation within the same execution domain:
- Cell-level context stays in the cell
- Aggregation happens within tissues
- Minimise cross-organ data movement

## Payload Reuse
Repeated components (shared instructions, schema definitions, common context) referenced via IDs or shared memory pointers rather than retransmitted.

## Transport Optimisation
- Connection reuse (keep-alive)
- HTTP/2 or multiplexed protocols
- Minimise TLS handshake overhead
- Regional endpoint selection

## Throughput Measurement
Throughput = **completed useful tasks per unit time** (not raw API calls or token volume).

## Adaptive Optimisation
Strategies adjust based on: load conditions, task mix, provider performance, network health.  
Possible adaptations: increase caching aggressiveness · shift to local models · reduce prompt size thresholds · adjust batching.

## Example Flow
1. Multiple proteins request similar data
2. Deduplication merges requests
3. Cached results satisfy some requests
4. Remaining calls batched
5. Prompts minimised before transmission
6. Responses streamed back
7. Results reused across dependent tasks

Result: fewer calls, lower latency, higher effective throughput.

## Goal
Keep the system **compute-bound, not network-bound**.
