# ADR-008: Normalize Provider Output at a Canonical Protein Boundary

**Status:** Accepted

---

## Context

Provider adapters currently return completion text under a generic `result` field, while the five protein types require different structured contracts. Allowing each caller to parse provider text independently would duplicate repair logic, produce inconsistent telemetry, and permit malformed evidence to pass into the runtime.

Phase 4.5 needs one boundary between model-provider output and `ProteinPipeline` validation.

---

## Proposed Decision

Introduce a `ProteinOutputNormalizer` as the only supported path from provider completion to a typed protein result.

- Prefer provider-native structured output or JSON Schema when the selected provider supports it.
- Maintain a canonical output schema for each protein type: reasoning, retrieval, transformation, aggregation, and evaluation.
- Preserve the original provider response only as a protected diagnostic reference; downstream runtime code receives the normalized representation.
- Permit bounded repair only for recoverable syntax or schema-shape failures.
- Never invent missing citations, evidence, scores, or source records during repair.
- Record parse, repair, schema-validation, and final pipeline outcomes after the real decision has occurred.
- Treat failure to produce a valid required contract within the repair budget as a typed protein failure.

Provider capability negotiation belongs in the model interface layer. Protein semantics remain provider-independent.

---

## Biological Analog

A ribosome does not define a protein's success merely because translation produced a chain. Chaperones, the endoplasmic reticulum, and Golgi quality controls fold, inspect, and route the product before it becomes usable. The normalizer is the digital folding boundary: provider output is raw translated material, not yet a valid protein.

---

## Digital Implementation

The boundary is:

```text
ProviderAdapter
  -> ProviderCompletion
  -> ProteinOutputNormalizer
  -> typed candidate
  -> ProteinPipeline
  -> accepted protein or typed failure
```

Normalizer behavior is selected by protein type and provider capability, not by API route. Contract tests cover every protein type across native-structured, JSON-text, repairable, and irrecoverable responses.

---

## Consequences

- Provider-specific response formats do not leak into protein or coordination code.
- Validation telemetry becomes trustworthy because it describes the actual normalized candidate.
- Adding a provider requires capability mapping and adapter contract tests.
- Repair adds latency and cost, so it must have explicit attempt and deadline budgets.
- Schema evolution requires compatibility rules for persisted runs and replay.

---

## Alternatives Considered

**Parse output in each protein executor:** Rejected because parsing, repair, and telemetry would diverge across protein types and call sites.

**Require native structured output from every provider:** Rejected because provider capabilities differ and this would unnecessarily eliminate otherwise usable providers.

**Accept free-form text and rely on downstream prompts:** Rejected because malformed data would cross the validation boundary and failures would surface far from their cause.

**Use unbounded LLM repair until validation succeeds:** Rejected because it creates unpredictable cost, latency, and evidence fabrication risk.
