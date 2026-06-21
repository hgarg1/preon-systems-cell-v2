# LLM Proteins Architecture — Section Index

Source: `docs/cell architecure v1/LLM Protiens Documentation.pdf` (145 pages, v1.0)

| # | File | Topic |
|---|---|---|
| 1 | [01-introduction.md](01-introduction.md) | Why biological model, the 5-layer hierarchy, 5 design goals |
| 2 | [02-definitions.md](02-definitions.md) | Canonical vocabulary: protein, cell, tissue, organ, organism, LLM vs SLLM |
| 3 | [03-system-overview.md](03-system-overview.md) | 8-step execution cycle, continuous operation, OrganismOS runtime |
| 4 | [04-protein-architecture.md](04-protein-architecture.md) | Internal protein struct, 5 protein types, lifecycle, concurrency limits |
| 5 | [05-model-interface-layer.md](05-model-interface-layer.md) | Provider abstraction, routing policy, token budgeting, fallback strategy |
| 6 | [06-concurrency-execution.md](06-concurrency-execution.md) | Useful vs raw parallelism, DAG scheduling, backpressure, queue types |
| 7 | [07-network-efficiency.md](07-network-efficiency.md) | Prompt minimization, caching, deduplication, batching, locality |
| 8 | [08-intra-cell-communication.md](08-intra-cell-communication.md) | Shared memory + events + message passing hybrid inside a cell |
| 9 | [09-intra-tissue-communication.md](09-intra-tissue-communication.md) | Aggregation strategies, consensus, iterative refinement across cells |
| 10 | [10-inter-tissue-communication.md](10-inter-tissue-communication.md) | Structured intent interfaces between tissues, data contracts |
| 11 | [11-organ-coordination.md](11-organ-coordination.md) | Organ = coordination layer over tissues, task decomp, feedback loops |
| 12 | [12-collective-intelligence.md](12-collective-intelligence.md) | Bottom-up emergence + top-down control, voice unification |
| 13 | [13-task-decomposition-orchestration.md](13-task-decomposition-orchestration.md) | Decomp vs orchestration, task graph, routing, adaptive replanning |
| 14 | [14-consensus-conflict-resolution.md](14-consensus-conflict-resolution.md) | 6 conflict types, 5 consensus modes, adjudication, failure modes |
| 15 | [15-memory-state-management.md](15-memory-state-management.md) | 5-layer memory, 5 memory types, context construction, lifecycle |
| 16 | [16-failure-resilience.md](16-failure-resilience.md) | 6 failure classes, retry policy, fallback paths, resilience modes |
| 17 | [17-observability-telemetry.md](17-observability-telemetry.md) | 5 telemetry categories, hierarchical tracing, provenance, replayability |
| 18 | [18-security-governance.md](18-security-governance.md) | Layered governance, access control, data classification, audit |
| 19 | [19-example-flows.md](19-example-flows.md) | 8 concrete flows from atomic math to multi-organ strategy |
| 20 | [20-design-principles.md](20-design-principles.md) | 15 named principles — the "why" behind every architectural choice |
| 21 | [21-future-extensions.md](21-future-extensions.md) | Self-optimization, multimodal, simulation organs, autonomous goals |
