# ADR-002: Genesis Organism Requires No Parents

**Status:** Accepted

---

## Context

The reproduction system was originally designed assuming at least two parent organisms: a mother (providing environment, data, execution context) and a father (providing compressed strategy and variation). The zygote was formed by merging gametes from both parents, inheriting memory from the mother and a strategic blueprint from the father.

This model breaks entirely for the first organism. There are no parents. There is no inherited memory, no gamete merge, no umbilical cord, no mother's oxygen quota. The system needed a distinct creation path for the primordial organism — the digital Adam or Eve — that bootstraps from nothing but intent.

---

## Decision

**The first organism is created directly from declared identity, purpose, and goals. No reproduction mechanics are involved.**

Genesis creation takes three inputs: a name, a purpose statement, and a list of goals. The resulting organism is assigned a default genome and an empty memory store. It has no lineage, no parent organism IDs, no inherited expression profile. It is a blank slate with declared intent.

This path is separate from reproduction. The Growth UI exposes both surfaces distinctly: a Genesis tab (no organisms required) and a Reproduction tab (requires ≥ 2 organisms). The system guards the Reproduction tab against insufficient organisms rather than conflating the two creation modes.

---

## Biological Analog

In origin-of-life biology, the first self-replicating molecule had no parent. Abiogenesis — the emergence of life from non-living chemistry — produced the first organism from environmental conditions alone: heat gradients, chemical concentrations, UV energy, and random molecular collisions in the primordial ocean. There was no template to copy, no gamete to merge. The first cell arose from the environment expressing itself into structure.

The digital analog: the first organism arises from the operator expressing intent into structure. The operator is the primordial environment. The name, purpose, and goals are the first chemical conditions.

---

## Digital Implementation

**Genesis path (`POST /api/organisms`):**
```
input:  { identity_profile: { name, purpose }, goals: [...] }
output: OrganismRecord with empty memory, default genome, no lineage_log
```

**Reproduction path (`POST /api/reproduction/zygote`):**
```
input:  { mother_organism_id, father_organism_id }
output: ZygoteRecord with merged ZygoteGenome, inherited food_log, umbilical cord
```

The genesis path uses `CreateOrganismRequest`, which has no parent fields. `OrganismRecord.lineage_log` is empty. `ZygoteRecord` fields (`mother_organism_id`, `father_organism_id`, `genome: ZygoteGenome`) are absent because genesis organisms are not zygotes.

**UI separation:**
- `GenesisPanel` component: name + purpose + editable goal list → "Spark Genesis"
- `ZygotePanel` component: organism selectors for mother/father → reproduction lifecycle
- `GrowthPage`: defaults to Genesis tab when no organisms exist; defaults to Primordial Soup tab when ≥ 1 organism exists; gates Reproduction tab behind ≥ 2 organism requirement

---

## Consequences

- The system supports a valid zero-organism state that does not require seeding parent organisms before use.
- Genesis organisms are always generation 0 with no parent_cell_id on their initial cells.
- The Primordial Soup (ADR-003) must be used to provide initial food and oxygen, since there is no mother organism to donate them.
- Lineage visualization tools must handle null lineage gracefully — not all organisms have ancestors.

---

## Rejected Alternatives

**Self-reproduction from a single parent:** One organism acts as both mother and father (asexual reproduction). Rejected because the reproduction system is architecturally coupled to two distinct gamete roles (environment donor vs. strategy donor). A single-parent path would require special-casing throughout the reproduction mechanics. Genesis is cleaner.

**Seeding a default "system" organism as parent:** Create a hidden system organism automatically and use it as the mother for all genesis organisms. Rejected because it introduces invisible state, makes lineage graphs misleading, and forces reproduction mechanics onto a creation act that isn't reproduction.
