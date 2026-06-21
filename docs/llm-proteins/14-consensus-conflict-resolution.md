# §14 — Consensus & Conflict Resolution

## Core Principle
> **Disagreement is not a defect — it is a signal.**

The objective is not to eliminate divergence at the source. It is to: detect it · interpret its meaning · resolve it at the appropriate layer · preserve the highest-quality outcome possible.

## 6 Sources of Conflict

| Type | Description |
|---|---|
| **Output Conflict** | Two or more components produce incompatible results |
| **Confidence Conflict** | Components agree on direction but disagree on certainty |
| **Scope Conflict** | Different layers interpret the task at different abstraction levels |
| **Priority Conflict** | Components optimise for different objectives (speed vs cost vs accuracy) |
| **State Conflict** | Different components act on inconsistent or stale state |
| **Policy Conflict** | Outputs violate governance, safety, or domain constraints |

## Resolution by Layer
Resolve at the **lowest layer capable** of resolving it correctly:

| Layer | Handles |
|---|---|
| **Protein** | Schema mismatch, malformed output, low-level retries |
| **Cell** | Local disagreements among protein outputs |
| **Tissue** | Competing cell-level conclusions within a shared domain |
| **Organ** | Cross-tissue disagreements in domain-specific reasoning |
| **Organism** | Cross-organ conflicts affecting final decisions or global objectives |

## 5 Consensus Modes

| Mode | Best for |
|---|---|
| **Majority Consensus** | Classification, binary decisions, structured comparison |
| **Confidence-Weighted** | Probabilistic reasoning, ranking tasks, uncertain environments |
| **Evidence-Weighted** | Retrieval-backed reasoning, factual tasks, simulation-driven decisions |
| **Hierarchical** | Strategic decisions, global tradeoff optimisation, cross-domain coordination |
| **Deliberative** | Ambiguous reasoning, high-stakes outputs, where first-pass aggregation is insufficient |

## Conflict Classification by Severity

| Severity | Typical Response |
|---|---|
| **Low** (formatting / low-impact) | Normalise locally, continue execution |
| **Medium** (meaningful divergence) | Run evaluation pass, require additional evidence, trigger local refinement loop |
| **High** (affects correctness / safety) | Escalate to higher layer, invoke adjudication tissue, suspend output until resolved |

## Adjudication Mechanisms
Invoked when direct consensus is insufficient. Performed by: evaluator proteins · validation cells · adjudication tissues · governing organs.

Strategies:
- Score competing outputs against objective criteria
- Compare against source evidence
- Simulate downstream consequences
- Apply governance/policy rules

## Multi-Pass Resolution Loop
1. Initial outputs conflict
2. Discrepancy detected
3. Evidence inspected
4. Targeted subcomponents re-invoked
5. Revised synthesis produced
6. If needed, escalation occurs

## Contradiction Detection
Active (not passive) detection:
- Schema validation
- Semantic similarity and contradiction checks
- Rule-based consistency tests
- Evidence cross-checking
- Temporal consistency checks against current state

## Confidence Calibration
Prevents overconfident but weak outputs from dominating. Calibrated using:
- Historical output quality
- Provider/model performance profiles
- Task-specific evaluation accuracy
- Agreement with external evidence

## Tradeoff Resolution
Many conflicts are tradeoff conflicts (speed vs accuracy, cost vs fidelity, caution vs decisiveness).  
Resolved using: policy-aware weighting · hierarchical objective alignment.

Example: tissue prefers detail → organ prefers speed → organism prioritises deadline → system aligns to active objective function.

## State Reconciliation
Conflicts from inconsistent state snapshots resolved via:
- Version checks
- Freshness validation
- Conflict-aware merging
- Invalidation of stale intermediate artifacts

## Human-Analog Model
> Proteins disagree at micro-level · cells reconcile local signals · tissues stabilise collective function · organs enforce domain coherence · organism acts as one body.

Disagreement is progressively reconciled as outputs move upward through the hierarchy.

## 4 Failure Modes of Consensus Systems

| Failure Mode | Description | Mitigation |
|---|---|---|
| **False Convergence** | Agreement reached too quickly on a poor answer | Diversity-aware evaluation |
| **Endless Deliberation** | Loops without resolving disagreement | Bounded iteration counts |
| **Confidence Capture** | Strong but incorrect component dominates | Calibrated confidence weighting |
| **Escalation Overuse** | Too many conflicts pushed to higher layers | Layer-specific resolution thresholds |

## Example Flow
1. Three tissues provide competing product strategy recommendations
2. Organ-level coordinator detects semantic conflict
3. Evaluation tissue scores each against market data, financial constraints, confidence history
4. Two recommendations partially merged; one rejected (weak evidence)
5. Revised output returned to organ
6. Organism synthesises with other organ inputs → final decision
