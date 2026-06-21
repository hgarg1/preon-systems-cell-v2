# §1 — Introduction

## Core Thesis
Traditional AI = pipelines (fragile, stateless, rigid, poor complexity scaling).  
Preon = **Synthetic Digital Biology** — living, persistent, adaptive entities.

| Pipeline world | Preon world |
|---|---|
| Invoked per request | Continuously operating |
| Centralized intelligence | Distributed intelligence |
| Hard-coded control flow | Dynamic coordination |
| Explicitly scripted behavior | Emergent behavior |

## The 5-Layer Hierarchy

```
LLM Protein  →  atomic execution unit
Cell         →  localised coordination of proteins
Tissue       →  specialised functional grouping of cells
Organ        →  domain-specific intelligent system
Organism     →  unified decision-making entity
```

Each upward step adds: more abstraction, more coordination complexity, more capability.  
**Intelligence does not reside in any single layer — it emerges from interactions across layers.**

## Role of LLM Proteins
- Interface with external intelligence (LLMs, SLLMs)
- Execute bounded reasoning/computation
- Produce structured outputs for higher-level coordination

They are NOT agents. They do not own end-to-end logic, have global awareness, or operate independently. Analogy: biological proteins — highly specialised, massively parallel, contextually activated.

## 5 Design Goals

| Goal | What it means |
|---|---|
| **Atomic Modularity** | Each intelligence unit is small, reusable, composable |
| **Controlled Concurrency** | Maximise throughput within API rate limits, bandwidth, cost |
| **Hierarchical Coordination** | Complex behaviour emerges through structured layer interaction |
| **Persistent System Behaviour** | Continuity via shared state, memory layers, execution history |
| **Production-Grade Reliability** | Fault tolerance, observability, auditability |

## Scope of the Document
Defines proteins as the foundational layer: how they interface with models, execute under concurrency, communicate within/across abstractions, and contribute to higher-level intelligence.
