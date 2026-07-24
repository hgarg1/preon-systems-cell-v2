# Preon Systems Cell v2

**A deterministic digital organism runtime grounded in biological first principles.**

Preon Cell models living computation: persistent organisms composed of cells, genomes that encode behavior, membrane-controlled signal admission, ribosome execution, ATP-based energy budgeting, and genome-gated cell division. Everything that happens inside an organism is logged, traced, and inspectable.

---

## The Biological Model

Every design decision in this runtime has a biological counterpart.

| Biological concept | Digital implementation |
|---|---|
| Organism | `OrganismRecord` — a persistent, named entity that receives signals and maintains state |
| Cell | `CellRecord` — an execution unit within an organism, with its own health and generation |
| Genome | `Genome` — encodes the module set, regulatory rules, capability registry, and division policy |
| Signal | Input event admitted through the membrane |
| Protein | Validated output produced by the ribosome after processing a signal |
| ATP (energy) | `resource_budget` — the execution currency, replenished by food + oxygen intake |
| Food | Structured data intake (prompts, tasks, identity seeds, domain knowledge) |
| Oxygen | Compute grant (CPU time, memory, context window, GPU units) |
| Mitochondria | Compute budget manager — food without oxygen causes suffocation |
| Skeletal tissue | Osteoblast, osteoclast, and osteocyte cells that grow, remodel, and monitor infrastructure |
| Structural bone | Organism-owned database, object-storage, queue, contract, or adapter structure |
| Cell division | Genome-gated split producing daughter cells that inherit or differentiate from the parent |
| Soul | Preserved essence of a terminated organism, available for reincarnation |

### ATP: The Energy Equation

```
Food (data / prompts / tasks) + Oxygen (compute / infrastructure) = ATP (execution budget)
```

Resources are modeled as **continuous streams**, not discrete events. Interruptions — sparse prompts, compute outages, sandboxing — are pathological states with recovery semantics, not normal operating modes. An organism that receives food before oxygen is provisioned will suffocate; the runtime enforces oxygen-first ordering structurally.

### Genesis: Digital Adam & Eve

The first organism has no parents. It is provisioned through the **Primordial Soup** — a pre-seeded food environment with five food categories:

| Category | Contents |
|---|---|
| `identity_seed` | Name, purpose, initial goals |
| `domain_vocab` | Core terminology the organism will reason over |
| `reflection` | Prompts for self-modeling |
| `synthetic_task` | Starter work units to bootstrap protein production |
| `genome_study` | The organism's own genome as text, for self-awareness |

Oxygen is always granted before food delivery. The Primordial Soup UI in the Operations Console lets operators pre-provision this initial environment before sparking the first organism.

### Cell Division: Three-Gate Model

Cells do not decide to divide. They reach the state the genome was always waiting for. Division is gated behind three co-required conditions encoded in the genome's `DivisionPolicy`:

**Load gate** — throughput threshold. Is the cell processing enough signal volume to justify splitting?

**Capability gate** — quality × breadth threshold. Has the cell demonstrated sufficient output quality across enough distinct signal types to be ready to specialize?

**Lifecycle gate** — generation ceiling, health state, cooldown. Is the cell old enough, healthy enough, and sufficiently rested since its last division?

All three gates must pass simultaneously. The genome specifies the thresholds; the cell's lived experience provides the measurements.

**Four division modes:**

| Mode | Biological analog | Digital purpose |
|---|---|---|
| `symmetric` | Mitosis — two identical daughters | Load distribution |
| `asymmetric` | Stem cell division — one stem + one committed | Capability inheritance + specialization |
| `founder` | Neural crest migration — daughter seeds a new organ | New cell type progenitor |
| `repair` | Wound healing — healthy neighbor replaces dead cell | Dead cell replacement (bypasses load/capability gates) |

### Living Skeleton and Infrastructure Access

Every organism is born with a skeletal tissue containing three ordinary, persisted cells:

- An **osteoblast** proposes structural growth.
- An **osteoclast** proposes remodeling or retirement.
- An **osteocyte** monitors the resulting structure.

Structural resources use a provider-neutral desired-state model covering database schemas, tables, indexes, blob/object namespaces, queues, topics, service contracts, and adapters. An approved plan materializes an organism-owned resource record. Other cells receive revocable, operation- and namespace-scoped `ResourceGrant` records; they do not receive raw provider credentials and do not route every data operation through a bone cell.

Phase 5A ships a deterministic in-memory provider and durable PostgreSQL control-plane persistence. Provider labels such as `postgres`, `s3`, and `azure_blob` do not themselves mutate live infrastructure. Live provider adapters remain a production-hardening step behind the same plan/apply/inspect contract.

See [Living Skeleton and Structural Resource Growth](docs/skeletal-growth.md) for the model, lifecycle, and API contract.

Phase 5.5 adds opt-in live PostgreSQL and S3-compatible adapters,
skeletal-cell execution provenance, and a durable queued-effect lifecycle.
Approval returns `202 Accepted`; the Skeleton inspector shows effect progress
and desired/observed resource health.

#### Phase 5.5 validation status

The real provider contract has been exercised against the dedicated Prisma
staging resources:

- PostgreSQL: `preon-cell-staging-db` in the `preon-internal-prod-db` project
- Object storage: `preon-cell-staging` (S3-compatible)
- Live structural round-trips: PostgreSQL schema create/inspect/retire and S3
  namespace marker create/inspect/retire both pass
- Python suite: `162 passed, 2 skipped`; the two skipped tests are the opt-in
  live-provider tests when staging credentials are not present in the process

The live tests use `PREON_TEST_DATABASE_URL` and the `PREON_TEST_S3_*` settings
documented by the integration test contract. Credentials are supplied through
the environment only and are never committed to the repository. Production
resources must not be used for this test suite.

### Durable Organism Memory

Valid protein output is not automatically long-term memory. Phase 5B admits only explicit candidates that pass confidence, importance, novelty, provenance, ownership, and data-policy checks. Operator-created memory remains an explicit admission path.

Before protein execution, a deterministic `ContextBuilder` retrieves relevant admitted memory by keywords, type, recency, importance, and confidence; filters by owner, lifecycle, TTL, and data class; deduplicates content; and enforces a bounded context budget. Only records actually injected into context have their access metadata updated.

The first memory operation grows an organism-owned memory resource and scoped grant through the living skeleton. See [Durable Organism Memory and Context Construction](docs/organism-memory.md).

Memory admission thresholds and context budgets are immutable organism policy
versions. Recalled memory reaches model providers only as bounded, untrusted
supporting data.

---

## Repository Layout

```
preon-systems-cell-v2/
├── preon_systems_cell/          # Python backend (FastAPI)
│   ├── web.py                   # All HTTP routes
│   ├── api.py                   # Business logic layer
│   ├── engine.py                # Organism runtime engine
│   ├── skeletal.py              # Structural provider contract, planning, and skeletal cell identities
│   ├── memory.py                # Admission policy, lifecycle helpers, deterministic ContextBuilder
│   ├── coordination.py          # Phase 4 cell execution plans and safe DAG coordinator
│   ├── execution_service.py     # Shared bounded execution, deadlines, cancellation
│   ├── protein_output.py        # Canonical structured-output schemas and normalization
│   ├── resilience.py            # Typed failures, retry budgets, circuit breakers
│   ├── security.py              # Bounded payload redaction by DataClass
│   ├── models.py                # Pydantic domain models
│   ├── auth.py                  # Session auth, OAuth2, CSRF
│   ├── email.py                 # Transactional email via Gmail OAuth2
│   ├── email_setup.py           # One-time refresh token setup script
│   ├── llm_providers.py         # Provider adapters (Anthropic, OpenAI, Grok, Gemini)
│   ├── bones/                   # Phase 1: skeletal capability framework
│   │   ├── models.py            # BoneContract, EnzymeGene, CompiledEnzyme
│   │   ├── compiler.py          # EnzymeCompiler + _safe_eval (AST whitelist)
│   │   ├── cortex.py            # BoneCortex, Osteocyte, Osteoclast, load_defaults()
│   │   ├── defaults.yaml        # 14 bone contracts + 14 enzyme genes
│   │   └── data/                # Pure python_ref modules (calculator, periodic table, etc.)
│   ├── model_routing/           # Phase 2: model interface layer & provider routing
│   │   ├── types.py             # LlmProteinInstantiationRequest, ModelRoutingDecision, etc.
│   │   ├── registry.py          # ProviderModelProfile + MODEL_REGISTRY (10 profiles)
│   │   ├── cell_router.py       # CellModelRouter — Day-One deterministic policy
│   │   ├── fallback.py          # Fallback chain builder
│   │   ├── telemetry.py         # ModelExecutionTelemetry in-memory log
│   │   ├── tissue_council.py    # Stub — Phase 6A
│   │   ├── organ_policy.py      # Stub — Phase 9
│   │   └── organism_authority.py # Stub — Phase 9
│   └── storage/                 # PostgreSQL + in-memory stores
│
├── frontend/                    # Next.js 16 Operations Console
│   └── src/
│       ├── app/                 # App Router pages
│       │   ├── organisms/       # Organism console, cells, genome, memory, events
│       │   ├── growth/          # Genesis panel, Primordial Soup, Reproduction
│       │   ├── contracts/       # Contract registry
│       │   ├── login/           # Auth pages
│       │   └── auth/            # OAuth2 callback
│       ├── components/
│       │   ├── auth/            # Auth forms, session watchdog, toast
│       │   ├── console/         # Signal submission, pipeline trace
│       │   ├── cells/           # Cell inspector, division
│       │   ├── genome/          # Genome viewer, division policy editor
│       │   ├── growth/          # Genesis panel, primordial soup
│       │   └── layout/          # App shell, sidebar
│       └── lib/
│           ├── api.ts           # All backend API calls
│           └── email-server.ts  # Nodemailer server utility
│
└── docs/
    ├── architecture/
    │   └── decisions/           # ADR-001 through ADR-013
    ├── llm-proteins/            # LLM Protein architecture spec (§1–§19)
    ├── deployment.md            # Reference topology (Fly.io)
    ├── deployment/              # Cloud-specific variants
    │   ├── aws.md               # ECS Fargate + RDS
    │   ├── azure.md             # Container Apps + Key Vault
    │   ├── gcp.md               # Cloud Run + Cloud SQL
    │   └── blended.md           # Cross-provider decision framework
    ├── implementation-roadmap.md
    └── postgres/                # Schema SQL
```

---

## Deployment

See [`docs/deployment.md`](docs/deployment.md) for the reference topology (Fly.io + Vercel) and [`docs/deployment/`](docs/deployment/) for AWS, Azure, GCP, and blended cloud variants. The blended doc includes a decision framework and the Preon-specific recommendation by phase.

---

## Stack

**Backend**
- Python 3.12+
- FastAPI + Uvicorn
- Pydantic v2
- Argon2 password hashing
- PostgreSQL (optional — falls back to in-memory)
- Gmail OAuth2 SMTP for transactional email (stdlib only, no extra deps)
- Bones capability framework (deterministic enzyme execution, safe AST evaluator)
- Model routing layer (Day-One deterministic policy, provider registry, telemetry)

**Frontend**
- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS v4
- Radix UI primitives
- Recharts
- Three.js
- Nodemailer (server-side email utility)

---

## Getting Started

### 1. Clone and install

```bash
git clone https://github.com/hgarg1/preon-systems-cell-v2.git
cd preon-systems-cell-v2

# Python backend
python -m pip install -e ".[dev,postgres]"

# Next.js frontend
cd frontend && npm install
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Minimum required for local development (no email, no OAuth):

```env
PREON_COOKIE_DOMAIN=localhost
PREON_COOKIE_SECURE=0
PREON_FRONTEND_URL=http://localhost:3000
```

### 3. Set up Google OAuth (optional but recommended)

Create a **Web application** credential in [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials.

Add these authorized redirect URIs:
- `http://localhost:3000/auth/oauth2callback` (dev)
- `https://yourdomain.com/auth/oauth2callback` (production)

Add to `.env`:

```env
PREON_GOOGLE_OAUTH_CLIENT_ID=<your-client-id>
PREON_GOOGLE_OAUTH_CLIENT_SECRET=<your-client-secret>
PREON_GOOGLE_OAUTH_REDIRECT_URI=http://localhost:3000/auth/oauth2callback
PREON_GOOGLE_OAUTH_AUTHORIZE_URL=https://accounts.google.com/o/oauth2/v2/auth
PREON_GOOGLE_OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
PREON_GOOGLE_OAUTH_USERINFO_URL=https://www.googleapis.com/oauth2/v3/userinfo
```

### 4. Set up transactional email (optional)

Obtain a Gmail OAuth2 refresh token for the sending account:

```bash
# Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env first, then:
python -m preon_systems_cell.email_setup
```

This opens a browser, completes the consent flow, and prints `GOOGLE_REFRESH_TOKEN` to paste into `.env`. Then add:

```env
GOOGLE_REFRESH_TOKEN=<token-from-setup>
GOOGLE_OAUTH_EMAIL=you@gmail.com
```

Without these vars, verification and reset emails fall back to dev mode — the URLs are returned in the API response and shown as toasts in the frontend.

### 5. Run

```bash
# Terminal 1 — Python backend
organism-web
# or: python -m preon_systems_cell.web

# Terminal 2 — Next.js frontend
cd frontend && npm run dev
```

| Interface | URL | Purpose |
|---|---|---|
| Operations Console | `http://localhost:3000` | Full CRUD — organisms, signals, cells, genome, growth |
| Python API | `http://localhost:8000` | FastAPI + Swagger docs at `/docs` |
| Python static dashboard | `http://localhost:8000` | Read-only monitoring (served by FastAPI) |

---

## Auth

Session auth uses an HttpOnly `preon_session` cookie shared between the Next.js frontend and Python backend via a Next.js rewrite proxy (`/backend/*` → `http://localhost:8000/*`). `PREON_COOKIE_DOMAIN=localhost` in dev lets both ports share the same cookie.

| Feature | Detail |
|---|---|
| Registration | Email + password, email verification via tokenized link |
| Login | Email + password, or Google OAuth |
| Session TTL | 14 days, sliding window (extended on each `/auth/me` poll when < 7 days remain) |
| Password reset | Token-based, invalidates all existing sessions on completion |
| Session watchdog | Polls `/auth/me` every 30 s; shows "Session ended" banner + redirects on 401 |
| CSRF protection | Origin header validation on all mutating requests |
| Rate limiting | 8 attempts per 5-minute window on login, signup, and forgot-password |

---

## Core API Routes

```http
# Organisms
POST   /api/organisms
GET    /api/organisms
GET    /api/organisms/{id}
POST   /api/organisms/{id}/wake
POST   /api/organisms/{id}/hibernate
POST   /api/organisms/{id}/die
POST   /api/organisms/{id}/food
POST   /api/organisms/{id}/oxygen

# Signals and events
POST   /api/organisms/{id}/signals
GET    /api/organisms/{id}/events

# Cells
GET    /api/organisms/{id}/cells
POST   /api/organisms/{id}/cells
POST   /api/organisms/{id}/cells/{cell_id}/divide
GET    /api/organisms/{id}/cells/{cell_id}/division-readiness

# Genome
GET    /api/genomes/{id}
PATCH  /api/genomes/{id}/division-policy

# Growth
POST   /api/reproduction/zygote
POST   /api/zygotes/{id}/develop
POST   /api/zygotes/{id}/birth

# Contracts and capabilities
GET    /api/contracts
POST   /api/contracts
GET    /api/capabilities

# Auth
POST   /auth/signup
POST   /auth/login
POST   /auth/logout
GET    /auth/me
POST   /auth/forgot-password
POST   /auth/reset-password
POST   /auth/verify-email
GET    /auth/oauth/google
POST   /auth/oauth/google/callback
```

---

## Architecture Decisions

Thirteen accepted decisions are documented in [`docs/architecture/decisions/`](docs/architecture/decisions/):

| ADR | Decision | Status |
|---|---|---|
| [ADR-001](docs/architecture/decisions/ADR-001-atp-continuous-stream-model.md) | Resources are continuous streams; interruptions are pathological | Accepted |
| [ADR-002](docs/architecture/decisions/ADR-002-genesis-no-parents.md) | The first organism has no parents — Digital Adam & Eve | Accepted |
| [ADR-003](docs/architecture/decisions/ADR-003-primordial-soup-provisioning.md) | Genesis food is pre-provisioned through a Primordial Soup | Accepted |
| [ADR-004](docs/architecture/decisions/ADR-004-oxygen-before-food-invariant.md) | Oxygen is always granted before food delivery | Accepted |
| [ADR-005](docs/architecture/decisions/ADR-005-cell-division-three-gate-model.md) | Cell division requires three co-required gates: load, capability, lifecycle | Accepted |
| [ADR-006](docs/architecture/decisions/ADR-006-division-policy-in-genome.md) | Division policy belongs in the genome — cells don't decide to divide | Accepted |
| [ADR-007](docs/architecture/decisions/ADR-007-division-modes-taxonomy.md) | Four division modes with distinct biological purposes | Accepted |
| [ADR-008](docs/architecture/decisions/ADR-008-structured-provider-output-boundary.md) | Normalize provider output at a canonical protein boundary | Accepted |
| [ADR-009](docs/architecture/decisions/ADR-009-shared-execution-service.md) | Use a shared bounded execution service | Accepted |
| [ADR-010](docs/architecture/decisions/ADR-010-hierarchical-trace-context.md) | Propagate an explicit hierarchical trace context | Accepted |
| [ADR-011](docs/architecture/decisions/ADR-011-durable-execution-run-ledger.md) | Persist cell runs as a durable execution ledger | Accepted |
| [ADR-012](docs/architecture/decisions/ADR-012-data-classification-and-provider-enforcement.md) | Enforce canonical data classification at provider invocation | Accepted |
| [ADR-013](docs/architecture/decisions/ADR-013-bounded-resilience-semantics.md) | Use typed failures and bounded resilience semantics | Accepted |
| [ADR-014](docs/architecture/decisions/ADR-014-first-class-skeletal-cells.md) | Model skeletal roles as first-class cells | Accepted |
| [ADR-015](docs/architecture/decisions/ADR-015-governed-structural-resources-and-grants.md) | Use governed structural resources and scoped access grants | Accepted |
| [ADR-016](docs/architecture/decisions/ADR-016-explicit-memory-admission-boundary.md) | Separate working state from admitted durable memory | Accepted |
| [ADR-017](docs/architecture/decisions/ADR-017-deterministic-bounded-memory-context.md) | Build memory context deterministically within a fixed budget | Accepted |
| [ADR-018](docs/architecture/decisions/ADR-018-modular-runtime-ports-and-adapters.md) | Use a modular runtime with ports and adapters | Accepted |
| [ADR-019](docs/architecture/decisions/ADR-019-skeletal-cell-command-execution.md) | Execute structural commands through skeletal cells | Accepted |
| [ADR-020](docs/architecture/decisions/ADR-020-transactional-structural-outbox.md) | Use a transactional outbox for structural effects | Accepted |

---

## Development

```bash
# Run backend tests
python -m pytest -q

# TypeScript type check
cd frontend && npx tsc --noEmit

# Lint
cd frontend && npm run lint

# Production build
cd frontend && npm run build
```

### Persistence

The runtime defaults to in-memory storage. To use PostgreSQL:

```env
PREON_DATABASE_URL=postgresql://user:pass@localhost:5432/preon_cell
```

Schema: [`preon_systems_cell/storage/sql/schema.sql`](preon_systems_cell/storage/sql/schema.sql)

Tables include `users`, `sessions`, `organisms`, `cells`, `genomes`, `signals`, `proteins`, `contracts`, `runtime_events`, `memory_records`, `structure_requests`, `bone_structures`, `structure_proposals`, `resource_grants`, `tissues`, `organs`, `souls`, `zygotes`, and auth token tables.

---

## Signal Pipeline Trace

Every signal admitted through the membrane produces a full execution trace visible in the Operations Console:

```
Signal admitted
  └─ Membrane: admission check (contract match, capability validation)
       └─ Cytoplasm: context routing
            └─ Nucleus: genome/module selection
                 └─ Ribosome: deterministic execution
                      └─ Protein: output validation
                           └─ Golgi: response shaping
                                └─ Event log + checkpoint
```

The console renders each stage with timing, pass/fail, and the data flowing through.

### Multi-Protein Cell Execution

A `GenomeModule` may declare an `execution_plan` to process one admitted signal through multiple proteins inside the selected cell. Plans are bounded DAGs with dependency ordering, parallel-ready waves, safe conditional branches, input mapping from prior results, and bounded iteration:

```json
{
  "plan_id": "research_then_summarize",
  "steps": [
    {
      "step_id": "lookup",
      "module_id": "retrieval",
      "input_map": {"query": "$signal.term"}
    },
    {
      "step_id": "combine",
      "module_id": "aggregation",
      "depends_on": ["lookup"],
      "condition": "lookup.confidence >= 0.7",
      "input_map": {"inputs": ["$steps.lookup.result"]}
    }
  ],
  "final_step_id": "combine",
  "fail_fast": true,
  "max_parallelism": 4
}
```

Step references can read `$signal`, `$steps`, `$shared`, `$result`, and `$iteration`. Conditions use a call-free expression evaluator; execution plans are limited to 100 steps, 16 parallel workers, and 10 iterations per step.

The response preserves the existing final `protein` field and adds `execution_run` with ordered step outcomes. Legacy modules without an execution plan continue through the original single-protein path.
