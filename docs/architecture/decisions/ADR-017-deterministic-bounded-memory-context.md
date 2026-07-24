# ADR-017: Build Memory Context Deterministically Within a Fixed Budget

**Status:** Accepted

---

## Context

Admitted memory is useful only when later execution can retrieve it safely and predictably. Unbounded or model-selected recall can leak higher-class data, cross ownership boundaries, produce nondeterministic prompts, and consume the provider’s entire context window.

---

## Decision

Build context before protein invocation using deterministic keyword relevance.

The builder:

1. includes bounded cell shared state;
2. filters memory by organism owner, admission and lifecycle status, TTL, and data classification;
3. scores keyword overlap, explicit references, kind, recency, importance, and confidence;
4. deduplicates by content hash;
5. applies a stable ordering;
6. admits records only while a provider-aware token budget remains.

Access count and last-access time change only for records actually injected into context. Memory is never evicted solely because it has not yet been accessed. TTL expiration, explicit supersession, duplicate consolidation, and conservative low-value aging remain auditable status changes rather than physical deletion.

The first implementation does not use embeddings or semantic similarity. Those require a separate quality, cost, privacy, and provider decision.

---

## Consequences

- Identical state and inputs produce the same selected memory set.
- Higher-class memory cannot flow into a lower-class invocation.
- Prompt growth is bounded and observable in runtime events.
- Retrieval quality can be measured with a small labeled keyword-relevance corpus.
- Approximate token counting is conservative but not identical to every provider tokenizer.

---

## Alternatives Considered

**Let the LLM choose memories:** Rejected because it adds cost and nondeterminism before the governed invocation boundary.

**Start with vector retrieval:** Rejected because keyword retrieval is inspectable and sufficient to establish the contracts.

**Return the newest records only:** Rejected because recency alone ignores relevance, importance, and explicit references.

## Phase 5.5 Invocation Boundary

Provider input is a typed envelope. System instructions, user input, working
state, and recalled memory remain separate until mapped to provider-native
roles. Memory is serialized as untrusted supporting data and cannot select a
provider, modify policy, authorize tools, or change execution destinations.
