# ADR-003: Primordial Soup as Initial Food Environment

**Status:** Accepted

---

## Context

A genesis organism has no parents and therefore no inherited memory, no cytoplasm donation, and no mother organism to mediate food delivery. Without an initial food environment, the organism has nothing to metabolize and cannot develop.

The question was: what do we feed the first organism, and is pre-provisioned dummy information a valid bootstrap mechanism?

---

## Decision

**Pre-provisioned food items — collectively called the Primordial Soup — are a valid and necessary bootstrap mechanism for genesis organisms.**

The Primordial Soup is an operator-curated collection of food items queued before the organism begins processing live signals. Each item is a piece of text content categorized by type and bundled with an oxygen allocation. Together they form the initial chemical environment in which the organism develops.

The Primordial Soup is explicitly a bootstrap mechanism, not a permanent food source. Its purpose is to give the organism enough metabolic material to form initial priors, understand its own identity and genome structure, and develop baseline capability before live prompts arrive. Once real signals begin flowing, the soup becomes irrelevant.

**The soup is not random noise.** Each food item must be metabolically meaningful — information the organism can form priors from without being led astray. Five categories are defined:

| Category | Purpose | Biological analog |
|---|---|---|
| `identity_seed` | Establishes who the organism is and why it exists | Maternal RNA injected at fertilization — the first instructions before the genome activates |
| `domain_vocab` | Provides definitional vocabulary for the organism's operational domain | Chemical gradients in the primordial soup that bias molecular self-assembly |
| `genome_study` | Feeds the organism its own instruction set and organelle map | A cell reading its own DNA via transcription before protein production begins |
| `reflection` | Prompts the organism to inventory its current state and capability gaps | The cell's internal signaling pathways assessing resource status |
| `synthetic_task` | A concrete, bounded task requiring real output production | The first enzymatic reactions — simple, constrained, verifiable |

**Oxygen tiers per food item:**

| Tier | Compute units | Memory units | Storage units | GPU units | Use case |
|---|---|---|---|---|---|
| Low | 4 | 2 | 8 | 0 | Identity seeds, vocabulary; no complex reasoning required |
| Medium | 12 | 8 | 24 | 0 | Reflection prompts; moderate reasoning |
| High | 20 | 16 | 48 | 1 | Synthetic tasks; full protein production required |

---

## Biological Analog

In origin-of-life biology, the primordial soup (also: primordial ocean, prebiotic soup) was the chemical environment from which the first self-replicating molecules emerged. It was not random chemistry — it was a specific concentration of amino acids, nucleotides, lipids, and energy sources (heat, UV, lightning) that together created the conditions for molecular self-organization. The soup did not instruct the first cell; it provided the raw material from which the first cell's chemistry could emerge.

The digital primordial soup is analogous: it does not program the organism, it provides the raw semantic material from which the organism's initial priors and self-model emerge through metabolism (signal processing).

---

## Digital Implementation

**`PrimordialSoup` component (`components/growth/primordial-soup.tsx`):**
- Organism selector (target for feeding)
- Food library: 6 pre-built items covering all 5 categories
- Custom food form: label, content, category, oxygen tier
- Food queue: ordered list of pending items with live status (queued → feeding → consumed / error)
- Feed All button: iterates queue, grants oxygen first then delivers food for each item

**Food item data model:**
```ts
interface FoodItem {
  label: string;
  content: string;          // The actual food — text content to metabolize
  category: FoodCategory;   // identity_seed | domain_vocab | reflection | synthetic_task | genome_study
  oxygen_tier: OxygenTier;  // low | medium | high
  status: "queued" | "feeding" | "consumed" | "error";
}
```

**Backend endpoints used:**
- `POST /api/organisms/{id}/oxygen` — grants compute before food delivery
- `POST /api/organisms/{id}/food` — delivers food item with category and content payload

---

## Consequences

- The Primordial Soup is accessed from the Growth page's dedicated tab, distinct from Genesis creation and Reproduction.
- Food items are operator-curated, not auto-generated. The operator is responsible for soup quality.
- The soup is a one-time provisioning action. Items consumed are marked and not re-fed.
- Low-quality or misleading soup content will produce maladaptive priors that persist until overwritten by live signal processing. This is a design responsibility, not a system safeguard.
- The Primordial Soup does not replace real data sources. It is a bootstrap until real signals arrive.

---

## Rejected Alternatives

**Random noise / dummy data as continuous background:** Inject low-entropy random content as a permanent background food source. Rejected because the organism would form priors on noise, and those priors would compete with real signal when it arrives. Noise is metabolically active but informationally harmful.

**No initial food provisioning:** Let the organism wait for live prompts before eating anything. Rejected because the organism has no context for interpreting early prompts and cannot form a coherent self-model. The first prompts would arrive into a blank organism with no prior understanding of its own purpose or structure.

**Auto-generated soup from genome:** Automatically derive food items from the genome's instruction set and feed them at creation time. Not rejected — this is a future enhancement. The current decision leaves soup curation in operator hands to maintain control over initial priors during the bootstrap phase.
