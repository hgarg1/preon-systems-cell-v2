# ADR-004: Oxygen Must Be Provisioned Before Food Delivery

**Status:** Accepted

---

## Context

When feeding an organism — whether from the Primordial Soup or from any other food source — two resources must be available: the food itself (content to metabolize) and oxygen (compute to metabolize it with). The question was the ordering and coupling of these two provisioning steps.

The risk: an organism that receives food but has no compute available cannot digest it. The food sits unprocessed, the organism cannot produce ATP, and effectively suffocates despite having something to eat. This is the digital equivalent of a cell drowning in glucose in an oxygen-free environment — the fuel is present but the metabolic machinery cannot run.

---

## Decision

**Oxygen is always granted before food is delivered. Food and oxygen are never decoupled at the delivery layer.**

Every food item in the system carries an explicit oxygen allocation (tier or specific compute amounts). When a food item is consumed from the queue, the system grants oxygen first via `POST /api/organisms/{id}/oxygen`, then delivers the food via `POST /api/organisms/{id}/food`. If the oxygen grant fails, the food delivery does not proceed.

This invariant is enforced structurally in the feed loop, not by convention or documentation:

```
for each food item:
  1. grant oxygen (compute provisioned)
  2. if oxygen grant fails → mark item as error, continue to next
  3. deliver food (organism now has compute to digest)
  4. mark item as consumed
```

The food delivery step is never reached without a successful oxygen grant preceding it.

---

## Biological Analog

In cellular respiration, oxygen and glucose must both be present at the mitochondria simultaneously for ATP synthesis to proceed efficiently via oxidative phosphorylation. Glucose without oxygen produces only anaerobic fermentation — 2 ATP per glucose instead of up to 38 ATP. The cell doesn't store oxygen in advance and then receive glucose — both substrates enter the metabolic pathway together. The Krebs cycle, the electron transport chain, and ATP synthase all require oxygen as the terminal electron acceptor during the same process that consumes glucose.

More precisely: oxygen is not consumed before glucose — they are consumed together. The digital analog simplifies this to a strict ordering (oxygen first) because the digital system must make a scheduling decision, and the safer decision is always to ensure compute availability before delivering content that demands processing.

---

## Digital Implementation

**In `PrimordialSoup` (`components/growth/primordial-soup.tsx`):**
```ts
// Oxygen first — always. The organism must have compute before it receives food.
await grantOxygen(targetId, OXYGEN_AMOUNTS[item.oxygen_tier]);
await feedOrganismCustom(targetId, { food_type: item.category, payload: { ... } });
```

**Oxygen tier → compute amounts mapping:**
```ts
const OXYGEN_AMOUNTS = {
  low:    { compute_units: 4,  memory_units: 2,  storage_units: 8,  gpu_units: 0 },
  medium: { compute_units: 12, memory_units: 8,  storage_units: 24, gpu_units: 0 },
  high:   { compute_units: 20, memory_units: 16, storage_units: 48, gpu_units: 1 },
};
```

**`grantOxygen` API function** was updated to accept an optional `amounts` parameter, allowing callers to specify exact compute allocations rather than using a hardcoded default. This enables per-food-item oxygen budgeting.

**`feedOrganismCustom` API function** was added alongside the existing `feedOrganism` to support custom food payloads (category + content) rather than only the hardcoded console food stub.

---

## Consequences

- No food delivery path in the system should call the food endpoint without first calling the oxygen endpoint.
- The UI must surface oxygen allocation as a first-class property of food items, not an afterthought.
- Error handling must distinguish between "oxygen grant failed" (compute unavailable — stop, don't deliver food) and "food delivery failed" (compute was available but ingestion failed — report error, oxygen was still consumed).
- Future food sources (live signal feeds, external data ingestion, automated reflection loops) must honor this invariant at their delivery layer.

---

## Rejected Alternatives

**Deliver food and oxygen simultaneously in one request:** A combined endpoint that grants oxygen and delivers food atomically. Not rejected as a future optimization — but the current two-step approach makes the invariant explicit and auditable in the events log. Both a food event and an oxygen event are recorded separately, making it clear in the event stream that oxygen preceded food.

**Assume oxygen is always available:** Deliver food without checking or provisioning compute, trusting that the environment has resources. Rejected because this fails silently when the organism is sandboxed or when compute is temporarily unavailable. Silent failure here produces the exact suffocation scenario the invariant is designed to prevent.

**Post-delivery oxygen:** Grant oxygen after food arrives so the organism "knows what it needs." Rejected immediately — this is the suffocation scenario by definition.
