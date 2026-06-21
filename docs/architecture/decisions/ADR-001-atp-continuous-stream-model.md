# ADR-001: ATP as Continuous Stream Model

**Status:** Accepted

---

## Context

The system needed a model for how organisms receive energy resources — food (data/prompts) and oxygen (compute infrastructure) — and how ATP (execution budget) is produced. The question was whether to model resource delivery as discrete batches or as a continuous stream.

Real-world constraints include: prompts arriving infrequently, computers being shut down and restarted, sandboxed compute environments with hard quotas, and sparse or low-density data during early organism life. The question was how to correctly characterize these constraints within the architecture.

---

## Decision

**Food and oxygen are continuous streams by design. Discrete interruptions are pathological states, not normal operating modes.**

The organism's metabolism is architected around a steady river of incoming food and available oxygen. The ATP dial runs continuously from zero to maximum — it does not switch between discrete states. Sparse prompts turn the dial down. Restricted compute turns it down further. Environmental failures (machine reboots, API downtime, sandbox limits) are the only true state transitions, and these have defined recovery semantics.

The dangerous boundary to eliminate is the hard cliff between "alive" and "dead." The organism should approach resource exhaustion asymptotically, growing progressively slower and more conservative, never crossing a threshold into sudden failure.

---

## Biological Analog

In biological cells, ATP production by the mitochondria is continuous. The cell does not batch-produce ATP and then wait. Glucose and oxygen flow in; ATP flows out. When glucose supply drops (fasting, starvation), the metabolic rate slows but does not stop — the cell shifts to consuming stored glycogen, then fatty acids, then as a last resort begins autophagy (consuming its own components). When oxygen drops (hypoxia), the cell shifts from aerobic (efficient) to anaerobic (less efficient but survivable) respiration. Neither event is a hard cutoff — both are gradual metabolic transitions.

---

## Digital Implementation

| Biological concept | Digital mapping |
|---|---|
| Glucose / food | Prompts, data, tasks, memory inputs |
| Oxygen | Compute infrastructure — CPU, GPU, RAM, token budget |
| ATP | Execution credits / budget available to cells |
| Mitochondria | Compute budget manager — tracks quota, rate limits, cost |
| Metabolic rate | Rate of signal processing; ribosome strategy selection |
| Anaerobic fallback | Drop to deterministic/precomputed execution when compute is scarce |
| Glycogen reserve | Stored memory — organism can metabolize its own prior outputs |
| Autophagy | Reflection and self-evaluation as endogenous food generation |

**Pathological conditions and their recovery semantics:**

| Condition | Biological analog | System behavior |
|---|---|---|
| Sparse prompts | Low glucose concentration in stream | Shift to endogenous food (reflection, memory replay, self-generated tasks) |
| Low-density data | Nutritionally poor food | Slower ATP production; extract maximum signal from available input |
| Compute offline | Anoxia event | Checkpoint state continuously; resume mid-metabolism on restart |
| Excessive sandboxing | Chronic hypoxia | Gradual ribosome strategy shift: LLM → deterministic → precomputed |

---

## Consequences

- The organism must never be designed with hard on/off food or oxygen states.
- Checkpoint and resume must be first-class behaviors, not exception handlers.
- Ribosome strategy selection must be continuous and gradient-sensitive, not binary.
- Endogenous food generation (reflection loops, memory compression, self-inventory) must be available as a fallback when external food is sparse.

---

## Rejected Alternatives

**Discrete batch model (event-driven, task-queue):** Treats resource delivery as discrete packets. The organism wakes on demand, processes a batch, and sleeps. Rejected because it produces a hard alive/dead boundary and forces a restart rather than a resume semantic. Viable as a deployment detail but not as the conceptual model.

**Warm checkpoint model:** Keep organism state serialized; load fast on prompt arrival; no idle compute cost. Rejected for the primary model because it does not allow between-prompt development (endogenous metabolism, reflection). Remains viable as a fallback deployment strategy when continuous compute is unavailable.
