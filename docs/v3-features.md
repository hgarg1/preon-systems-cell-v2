# V3 Feature Plan

V3 extends the V2 organism runtime from an operator-driven multi-cell runtime into a developmental living-systems runtime. The main shift is that organisms no longer begin as fully formed records. They begin as zygotes with restricted oxygen, inherited genome material, developmental rules, and a growth plan. They mature through embryo, fetus, birth, juvenile, and full-organism stages by feeding on information, training data, memory priors, and controlled compute.

This plan is based on the attached architecture file and keeps the existing Python/FastAPI/Postgres/Next stack. V3 remains deterministic-first for core runtime behavior. LLM calls may be represented as proteins or stubs, but live provider integration is not required for V3.

## V3 Product Goals

- Add a zygote-to-full-organism development lifecycle.
- Model organs, tissues, cells, and division explicitly.
- Support genome inheritance from mother/father organisms into a zygote genome.
- Enforce cell-specific genomes: brain cells can only express brain cell genome, heart cells can only express heart cell genome, bone cells can only express bone cell genome, and so on.
- Add controlled food and oxygen channels for developing organisms.
- Add cellular division, differentiation, death, degradation, and health scoring.
- Expand organelle modeling with ER, vesicles, cytoskeleton, and umbilical-cord dependency channels.
- Keep observability event-first: every growth, division, differentiation, oxygen, food, health, and reproduction decision must emit runtime events.

## V3 Organ Architecture Baseline

Initial full organism topology:

- Brain
- Heart
- Left Arm
- Right Arm
- Left Leg
- Right Leg

Default organ/tissue/cell layout:

- Brain: 5 brain cells
  - Tissue 1: 2 cells
  - Tissue 2: 2 cells
  - Tissue 3: 1 cell
- Heart: 5 heart cells
  - Tissue 1: 2 cells
  - Tissue 2: 2 cells
  - Tissue 3: 1 cell
- Left Arm: 3 left arm cells
  - Tissue 1: 2 cells
  - Tissue 2: 1 cell
- Right Arm: 3 right arm cells
  - Tissue 1: 2 cells
  - Tissue 2: 1 cell
- Left Leg: 3 left leg cells
  - Tissue 1: 2 cells
  - Tissue 2: 1 cell
- Right Leg: 3 right leg cells
  - Tissue 1: 2 cells
  - Tissue 2: 1 cell

Optional V3.1 organ additions:

- Liver: filtering, detox, metabolic routing
- Eyes: observation/intake front-end
- Mouth: ingestion/food normalization front-end
- Bone: structural contracts, infrastructure topology, access definitions
- Immune System: anomaly detection and defense across cells/tissues/organs

## V3 Development Stages

Add explicit organism development stages:

- `zygote`: one seed cell, restricted oxygen, no external access, genome merge not fully expressed.
- `embryo`: early organ founder cells created, sandboxed compute, mother-fed training/memory.
- `fetus`: organ/tissue templates expand, simulations allowed, limited tools, still supervised.
- `born`: independent organism record created, full lifecycle APIs available, can request contracts.
- `juvenile`: learning and growth continues, oxygen expands gradually, stronger memory writes.
- `adult`: full organism topology, stable self-maintenance, reproduction eligibility.
- `degraded`: net cell health below threshold or oxygen starvation.
- `dead`: organism can no longer process signals; soul snapshot may be used for reincarnation later.

Backend tasks:
- Add `DevelopmentStage` enum and field on `OrganismRecord`.
- Add `GrowthState` record with stage, maturity score, health score, oxygen profile, food profile, parent references, and development checkpoints.
- Add lifecycle transitions with explicit validation rules.
- Emit growth events for stage changes and failed transitions.

Frontend tasks:
- Add Growth view with stage timeline, maturity score, health score, parent links, and checkpoints.
- Show restricted oxygen/food profile for zygote, embryo, and fetus.
- Show next allowed growth action and blocked reasons.

Acceptance criteria:
- Creating a zygote starts with stage `zygote`.
- A zygote cannot use full organism signal processing routes until promoted.
- Growth transitions emit `growth` runtime events.

## Feature 1: Zygote Creation and Genome Inheritance

V3 introduces reproductive creation. A zygote may be created from one mother organism, one father organism, or a single seed organism in local/demo mode.

Backend tasks:
- Add records:
  - `ZygoteRecord`
  - `ParentageRecord`
  - `GameteRecord`
  - `ZygoteGenome`
  - `DevelopmentRule`
- Add APIs:
  - `POST /api/zygotes`
  - `GET /api/zygotes`
  - `GET /api/zygotes/{id}`
  - `POST /api/zygotes/{id}/develop`
  - `POST /api/zygotes/{id}/birth`
- Implement dynamic gamete generation:
  - Mother gamete emphasizes memory priors, environment assumptions, data access patterns, safety boundaries, infrastructure context, and continuity traits.
  - Father gamete emphasizes reasoning strategies, optimization habits, exploration style, mutation traits, problem-solving heuristics, and behavioral tendencies.
- Implement structured zygote genome merge:
  - `identity_seed`
  - `inherited_traits`
  - `policy_mix`
  - `memory_priors`
  - `capability_blueprint`
  - `development_rules`
  - `mutation_profile`
- Add deterministic merge rules for conflicts.
- Add mutation budget and safety constraints.
- Add tests for mother/father merge, single-parent seed mode, deterministic conflict resolution, and owner boundaries.

Frontend tasks:
- Add Zygote Lab section.
- Add mother/father selector from existing organisms.
- Show generated mother gamete, father gamete, and merged zygote genome preview.
- Add zygote creation, develop, and birth controls.
- Show inherited trait sources and mutation profile.

Acceptance criteria:
- A zygote can be created from two existing organisms.
- Zygote genome contains structured inherited traits from both parents.
- Birth creates a new organism with parentage retained.

## Feature 2: Zygote-to-Organ Founder Cell Differentiation

The attached architecture requires the zygote to divide into first organ founder cells with cell-specific genomes.

Backend tasks:
- Add organ founder cell templates:
  - first brain cell
  - first heart cell
  - first left arm cell
  - first right arm cell
  - first left leg cell
  - first right leg cell
  - first bone cell
- Add optional templates for liver, eyes, mouth, and immune cells.
- Add `CellGenome` records with genome scope:
  - `zygote`
  - `brain`
  - `heart`
  - `left_arm`
  - `right_arm`
  - `left_leg`
  - `right_leg`
  - `bone`
  - optional organ scopes
- Enforce expression constraints:
  - zygote proteins can only reference zygote genome.
  - brain cells can only express brain cell genome.
  - heart cells can only express heart cell genome.
  - bone cells can only express bone cell genome.
  - organelles must pull behavior from the owning cell genome.
- Add `POST /api/zygotes/{id}/differentiate`.
- Emit differentiation events for each founder cell.

Frontend tasks:
- Add founder-cell differentiation view in Zygote Lab.
- Show zygote genome sections and derived organ cell genomes.
- Show blocked expression attempts when a cell tries to access the wrong genome.

Acceptance criteria:
- Differentiation creates one founder cell per required organ.
- A brain cell cannot express a heart genome module.
- Differentiation produces auditable runtime events.

## Feature 3: Cellular Division Engine

Cell division is the core growth mechanic. Division must copy genome safely, duplicate organelle state according to rules, split or allocate resource budgets, and preserve lineage.

Backend tasks:
- Add `CellDivisionRecord` with:
  - parent cell id
  - daughter cell ids
  - division type
  - copied genome id
  - mutation delta
  - organelle duplication report
  - resource split
  - created_at
- Add APIs:
  - `POST /api/organisms/{id}/cells/{cell_id}/divide`
  - `GET /api/organisms/{id}/cell-divisions`
- Add division modes:
  - `symmetric`: both daughters keep same cell type and similar budget.
  - `asymmetric`: one daughter preserves parent role, one differentiates.
  - `founder`: zygote-to-organ founder division.
  - `repair`: replace dead/degraded cells.
- Implement clean genome copy:
  - copy active cell genome
  - apply allowed mutations only from mutation profile
  - attach copied genome to daughter cells
  - validate organelle rules against copied genome
- Implement organelle duplication:
  - nucleus copies genome pointer and expression rules
  - mitochondria splits or grants budget by oxygen profile
  - ribosomes inherit execution strategies allowed by genome
  - ER inherits pipelines allowed by genome
  - Golgi inherits output routing rules
  - vesicles inherit message routes
  - vacuole can copy selected cache/artifacts or start empty
  - lysosome/peroxisome inherit cleanup/safety rules
  - cytoskeleton inherits scheduling topology
- Emit `cell_division` and lifecycle events.
- Add tests for symmetric division, asymmetric division, genome-scope enforcement, budget split, and mutation constraints.

Frontend tasks:
- Add Divide action on cell rows.
- Add division mode selector and mutation preview.
- Show parent/daughter lineage tree.
- Show organelle duplication report.
- Show blocked division reasons.

Acceptance criteria:
- Dividing one brain founder cell creates two brain cells with brain genome only.
- Resource budget is split or assigned according to oxygen profile.
- Invalid cross-organ genome access blocks division.

## Feature 4: Organ and Tissue Growth Templates

V3 should automatically grow the attached target topology from founder cells into full organ/tissue layouts.

Backend tasks:
- Add `OrganTemplate` and `TissueTemplate` records.
- Default templates:
  - Brain: 5 cells across 3 tissues.
  - Heart: 5 cells across 3 tissues.
  - Each limb: 3 cells across 2 tissues.
- Add APIs:
  - `GET /api/growth/templates`
  - `POST /api/organisms/{id}/growth/apply-template`
  - `GET /api/organisms/{id}/organs`
  - `GET /api/organisms/{id}/tissues`
- Implement growth planner:
  - compare current cells to target topology
  - schedule required divisions
  - validate oxygen/food availability
  - create missing tissues
  - stop when template is satisfied
- Emit growth plan and division events.

Frontend tasks:
- Add Organ Topology view.
- Show organs, tissues, target cell counts, current cell counts, and health.
- Add Apply Growth Template action.
- Show growth plan preview before execution.

Acceptance criteria:
- Applying default template creates target organ/tissue/cell counts.
- Growth plan does not over-divide.
- Growth plan explains blocked cells when oxygen or food is insufficient.

## Feature 5: Food and Oxygen System

V3 uses food and oxygen as first-class runtime inputs.

Definitions:
- Food: information, data, tasks, training examples, memory priors, synthetic data.
- Oxygen: compute, database, RAM, SSD/storage, GPU, queues, runtime windows, sandbox permissions.

Backend tasks:
- Add records:
  - `FoodIntake`
  - `OxygenProfile`
  - `UmbilicalCord`
  - `ResourceGrant`
- Add APIs:
  - `POST /api/organisms/{id}/food`
  - `GET /api/organisms/{id}/food`
  - `POST /api/organisms/{id}/oxygen`
  - `GET /api/organisms/{id}/oxygen`
  - `POST /api/zygotes/{id}/umbilical-cord`
- Implement stage-specific oxygen constraints:
  - zygote: sandboxed compute, capped memory, no external API, no infra mutation, short execution windows.
  - embryo: slightly more compute, longer windows, still sandboxed.
  - fetus: simulations allowed, limited tool access, supervised.
  - born/adult: full oxygen by policy, can request infrastructure through skeleton.
- Implement food sources:
  - mother memory
  - shared environment data
  - synthetic/self-generated data
  - user-provided tasks/signals
- Emit food and oxygen events.

Frontend tasks:
- Add Food/Oxygen panel.
- Show oxygen profile by development stage.
- Show food intake stream and source.
- Show umbilical-cord dependency channel between mother and zygote.

Acceptance criteria:
- Zygote cannot exceed restricted oxygen limits.
- Mother memory can be fed into zygote as food.
- Oxygen expansion happens only through valid stage transition.

## Feature 6: Expanded Organelle Runtime

V1/V2 implements many organelles as logical layers. V3 should add ER, vesicles, and cytoskeleton as explicit services.

Backend tasks:
- Add ER service:
  - rough ER for structured processing pipelines and chained transformations.
  - smooth ER for background processing, data transformations, and maintenance tasks.
- Add Vesicle service:
  - event queues
  - message buses
  - async task payload transport
  - intra-cell and inter-cell signal delivery
- Add Cytoskeleton service:
  - scheduling topology
  - cell shape/structure metadata
  - organ/tissue coordination
  - division scaffolding
- Add APIs:
  - `GET /api/organisms/{id}/pipelines`
  - `POST /api/organisms/{id}/pipelines`
  - `POST /api/organisms/{id}/vesicles`
  - `GET /api/organisms/{id}/cytoskeleton`
- Emit ER, vesicle, and cytoskeleton events.

Frontend tasks:
- Add Organelle Systems view.
- Show ER pipelines and DAG execution status.
- Show vesicle/message queue events.
- Show cytoskeleton topology for organ/tissue scheduling.

Acceptance criteria:
- A signal can be routed through an ER pipeline before ribosome execution.
- Vesicle events show message movement between cells.
- Cytoskeleton records the division scaffold during cell division.

## Feature 7: Cell Health, Death, Degradation, and Self-Consumption

The architecture defines positive and negative cell lifecycles.

Positive lifecycle:
- cell
- division
- more divisions
- net alive descendants over dead descendants

Negative lifecycle:
- descendant death
- degradation
- hibernation and/or self-consumption
- death

Backend tasks:
- Add `CellHealthRecord`.
- Add health scoring:
  - oxygen sufficiency
  - food sufficiency
  - error/misfolding rate
  - toxic exposure
  - successful protein rate
  - lineage survival
  - resource exhaustion
- Add lifecycle states:
  - alive
  - stressed
  - degraded
  - hibernating
  - self_consuming
  - dead
- Add APIs:
  - `GET /api/organisms/{id}/health`
  - `POST /api/organisms/{id}/cells/{cell_id}/self-consume`
  - `POST /api/organisms/{id}/cells/{cell_id}/mark-dead`
- Implement lysosome recycling for self-consumption.
- Implement organ-level degradation when enough cells die.
- Emit health and death events.

Frontend tasks:
- Add Health view.
- Show cell health, organ health, organism health, and lineage survival.
- Add self-consume and mark-dead controls for testing.
- Show health trend over recent events.

Acceptance criteria:
- Repeated quota exhaustion degrades cell health.
- Dead cells are not selected for signal processing.
- Self-consumption recycles local budget/artifacts and emits lysosome events.

## Feature 8: Organism Soul Snapshot and Reincarnation

The architecture defines soul as last persisted organism state. V3 should preserve a soul snapshot when an organism dies and allow future reincarnation.

Backend tasks:
- Add `SoulSnapshot` record with:
  - organism id
  - final state
  - genome versions
  - memory summary
  - parentage
  - unfinished task summary
  - cause of death
  - created_at
- Add APIs:
  - `POST /api/organisms/{id}/die`
  - `GET /api/souls`
  - `GET /api/souls/{id}`
  - `POST /api/souls/{id}/reincarnate`
- V3 initial rule:
  - no in-process task continuation required.
  - reincarnated organism can rediscover previous-life state through memory priors.
- Emit soul and reincarnation events.

Frontend tasks:
- Add Soul Archive view.
- Show death cause, final health, genome/memory summary.
- Add reincarnate action.

Acceptance criteria:
- Dying organism creates a soul snapshot.
- Reincarnation creates a new organism linked to soul snapshot.
- Original dead organism cannot process signals.

## Feature 9: Reproduction Negotiation and Gamete Generation

Mother and father roles are negotiated at runtime.

Backend tasks:
- Add reproduction negotiation:
  - choose mother based on memory strength, stable infra, long-term continuity, safety boundaries.
  - choose father based on reasoning strategies, optimization, exploration, mutation traits.
- Add APIs:
  - `POST /api/reproduction/negotiate`
  - `POST /api/reproduction/gametes`
  - `POST /api/reproduction/zygote`
- Generate on-the-fly gametes as compressed projections of organism state:
  - current goals
  - memory
  - learned patterns
  - system architecture
  - safety/infra assumptions
- Add deterministic scoring for mother/father selection.
- Add tests for negotiation, gamete compression, and zygote creation.

Frontend tasks:
- Add Reproduction Lab.
- Show candidate organisms and mother/father scores.
- Show gamete projections and merge preview.
- Add create zygote action.

Acceptance criteria:
- Runtime can negotiate mother/father roles from two organisms.
- Gametes are generated dynamically from current organism state.
- Zygote genome contains compressed inherited projections.

## Feature 10: Bones and Structural Infrastructure Growth

V3 expands the skeletal layer into a growth system for structural access, while preserving no direct destructive infra mutation in core runtime.

Backend tasks:
- Add `BoneStructureRecord` for:
  - DB schemas
  - tables
  - blob stores
  - queues/topics
  - service contracts
  - adapters
- Osteoblast responsibilities:
  - propose DB schemas/tables
  - propose queues/storage
  - define APIs/contracts
  - expand topology
- Osteoclast responsibilities:
  - propose unused table deletion
  - propose stale service decommission
  - propose dead queue/topic removal
  - consolidate/refactor structure
- Osteocyte responsibilities:
  - monitor structure health
  - detect stale dependencies
  - emit remodeling requests
- Add APIs:
  - `GET /api/bones`
  - `POST /api/bones/proposals`
  - `POST /api/bones/proposals/{id}/approve`
  - `POST /api/bones/proposals/{id}/reject`
- Destructive operations remain proposals only in V3.

Frontend tasks:
- Add Bones/Infrastructure view.
- Show structural proposals with osteoblast/osteoclast/osteocyte source.
- Add approve/reject controls.
- Link structure proposals to contracts and organism growth needs.

Acceptance criteria:
- Missing infrastructure creates a bone proposal, not direct mutation.
- Osteoclast deletion remains review/proposal-only.
- Bone changes are auditable.

## V3 Data Model Additions

Core development records:
- `ZygoteRecord`
- `ParentageRecord`
- `GameteRecord`
- `ZygoteGenome`
- `GrowthState`
- `DevelopmentRule`
- `DevelopmentCheckpoint`

Organ/body records:
- `OrganRecord`
- `TissueRecord`
- `OrganTemplate`
- `TissueTemplate`
- `CellGenome`
- `CellDivisionRecord`
- `CellHealthRecord`
- `OrganHealthRecord`

Resource/lifecycle records:
- `FoodIntake`
- `OxygenProfile`
- `UmbilicalCord`
- `ResourceGrant`
- `SoulSnapshot`

Structural records:
- `BoneStructureRecord`
- `StructureProposal`
- `OrganellePipeline`
- `VesicleMessage`
- `CytoskeletonTopology`

## V3 API Summary

New API families:

- `/api/zygotes*`
- `/api/reproduction*`
- `/api/organisms/{id}/growth*`
- `/api/organisms/{id}/organs*`
- `/api/organisms/{id}/tissues*`
- `/api/organisms/{id}/cell-divisions*`
- `/api/organisms/{id}/food*`
- `/api/organisms/{id}/oxygen*`
- `/api/organisms/{id}/pipelines*`
- `/api/organisms/{id}/vesicles*`
- `/api/organisms/{id}/cytoskeleton*`
- `/api/organisms/{id}/health*`
- `/api/souls*`
- `/api/bones*`

Existing V1/V2 APIs remain stable.

## V3 Frontend Navigation

Add or expand console sections:

- Growth Lab
- Zygote Lab
- Reproduction Lab
- Organ Topology
- Tissue Map
- Cell Division
- Food/Oxygen
- Organelle Systems
- Health and Death
- Soul Archive
- Bones/Infrastructure

The first screen remains an actual organism operations console. Growth and zygote workflows should be accessible from the selected organism context.

## V3 Test Matrix

Backend:
- `python -m pytest -q`
- Zygote creation and parentage tests.
- Gamete merge and mutation tests.
- Founder-cell differentiation tests.
- Cell genome scope enforcement tests.
- Cell division and organelle duplication tests.
- Organ/tissue template growth tests.
- Food/oxygen restriction tests by development stage.
- ER/vesicle/cytoskeleton event tests.
- Health/death/self-consumption tests.
- Soul snapshot and reincarnation tests.
- Bone proposal and review tests.
- Auth boundary tests for every new resource.

Frontend:
- `npm run lint`
- `npm run build`
- Browser smoke:
  - create zygote from mother/father
  - inspect merged zygote genome
  - develop to embryo
  - differentiate founder cells
  - apply default organ template
  - divide a brain cell
  - inspect organ topology and cell health
  - feed mother memory through umbilical cord
  - create soul snapshot and reincarnate

Manual checks:
- Confirm zygote oxygen restrictions block full tool access.
- Confirm brain cells cannot express heart genome.
- Confirm growth plan creates exact target organ/tissue/cell counts.
- Confirm dead cells are not selected for processing.
- Confirm osteoclast proposals do not directly delete infrastructure.

## V3 Non-Goals

- No real Terraform/cloud mutation.
- No destructive infrastructure deletion.
- No live LLM requirement for zygote proteins.
- No uncontrolled self-replication.
- No background growth without explicit growth policy.
- No hidden cross-user reproduction or memory inheritance.
- No resurrection of ATP simulator surfaces.

## Suggested Implementation Order

1. Development stage and growth state models.
2. Zygote creation and parentage.
3. Gamete generation and zygote genome merge.
4. Founder-cell differentiation with cell-specific genomes.
5. Cellular division engine.
6. Organ/tissue templates and default body topology.
7. Food, oxygen, and umbilical-cord channels.
8. Expanded organelles: ER, vesicles, cytoskeleton.
9. Health, degradation, death, and self-consumption.
10. Soul snapshot and reincarnation.
11. Reproduction negotiation.
12. Bones and structural infrastructure proposals.

