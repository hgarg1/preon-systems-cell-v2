# §2 — Definitions & Terminology

## Core Biological Abstractions

| Term | Definition | Does NOT |
|---|---|---|
| **LLM Protein** | Smallest unit of intelligence execution; interfaces with LLM/SLLM APIs; executes atomic bounded tasks | Manage workflows, have global awareness, operate independently at scale |
| **Cell** | Localized coordination unit of multiple proteins; short-horizon reasoning + aggregation + scheduling | — |
| **Tissue** | Collection of cells sharing a functional role; aggregates, validates, reconciles, transforms outputs | — |
| **Organ** | Domain-specific intelligent system (e.g. planning, coding); coordinates across tissues; exposes intent-level outputs | — |
| **Organism** | Top-level system; integrates all organ outputs; makes final decisions; maintains global objectives and state | — |

## Execution Concepts

| Term | Definition |
|---|---|
| **Atomic Task** | Bounded unit of work for a single protein (one reasoning step, one web query, one math op) |
| **Composite Task** | Multiple atomic tasks coordinated within a cell or tissue |
| **Execution Graph** | Dependency-aware DAG representing how tasks are scheduled across proteins/cells/tissues |

## Communication Types

| Type | Scope | Character |
|---|---|---|
| **Intra-Cell** | Protein ↔ Protein, same cell | Low latency, shared memory, event-driven |
| **Intra-Tissue** | Cell ↔ Cell, same tissue | Aggregation-focused, partial result sharing |
| **Inter-Tissue** | Tissue ↔ Tissue | Abstracted outputs, structured message passing, versioned exchange |
| **Intra-Organ** | Tissues within same organ | Domain-specific coordination, multi-step pipelines |
| **Inter-Organ** | Organ ↔ Organ | Intent-level messaging, bidirectional, hierarchical control |

## Model Types

| Type | Use for | Characteristics |
|---|---|---|
| **LLM** (Large Language Model) | Deep reasoning, synthesis, ambiguity | High capability, higher latency + cost |
| **SLLM** (Small Language Model) | Routing, lightweight transforms, low-cost summarisation | Faster, cheaper, lower reasoning depth |

## System Properties

| Property | Definition |
|---|---|
| **Concurrency** | Executing multiple tasks simultaneously within resource constraints |
| **Throughput** | Tasks processed per unit time across the system |
| **Latency** | Time to complete a task or produce a result |
| **State** | Structured internal representation at a given time |
| **Memory** | Persisted or semi-persisted data informing future executions |
| **Context** | The subset of state + memory provided to a specific protein invocation |

## Coordination Concepts

| Concept | Definition |
|---|---|
| **Orchestration** | High-level coordination across layers (cells → tissues → organs) |
| **Scheduling** | Allocation and timing of task execution (cell or tissue level) |
| **Consensus** | Resolving multiple outputs into one result (majority vote, confidence-weighted) |
| **Feedback Loop** | Higher-level outputs influencing lower-level execution |

## Scope Summary

| Concept | Scope | Responsibility |
|---|---|---|
| LLM Protein | Atomic | Execute tasks |
| Cell | Local | Coordinate proteins |
| Tissue | Functional | Aggregate and validate |
| Organ | Domain | Solve complex problems |
| Organism | Global | Make decisions |
