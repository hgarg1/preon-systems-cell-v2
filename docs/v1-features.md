# V1 Feature Plan

This plan defines the first production-oriented feature set for the Cell Survival Requirements organism runtime. V1 should keep the runtime deterministic, preserve the existing FastAPI/Postgres/Next stack, and focus on making organism behavior inspectable, durable, and safe to operate.

## V1 Product Goals

- Make an organism easy to create, wake, feed with signals, inspect, and hibernate.
- Make every runtime decision observable through ordered `runtime_events`.
- Keep deterministic execution reliable for exact tasks such as arithmetic and known contract calls.
- Prevent cells from inventing infrastructure access; missing access must create structure requests.
- Make operators able to understand membrane admission, organelle execution, protein validation, contract status, and resource budget state from the console.

## Feature 1: Organism Lifecycle Console

Operators can create organisms, inspect persistent identity, wake/hibernate them, and verify that compute state is disposable while identity, genome, memory, and snapshots persist.

Backend tasks:
- Ensure `POST /api/organisms`, `GET /api/organisms`, and `GET /api/organisms/{id}` return lifecycle, genome, cells, recent events, proteins, and structure requests.
- Keep organisms hibernated by default after creation and after signal processing.
- Include `last_state_snapshot` updates after hibernation with cell state and protein counts.
- Add lifecycle events for explicit wake, signal-triggered wake, checkpoint, and hibernate.

Frontend tasks:
- Show organism list with lifecycle status and selected organism details.
- Add wake and hibernate controls with loading/error states.
- Show persistent identity, goals, genome id, and last snapshot summary.
- Show cell resource budgets near lifecycle controls.

Acceptance criteria:
- A new organism appears in the list as `hibernated`.
- Submitting a valid signal wakes the organism and returns it to `hibernated`.
- The trace includes lifecycle events for wake and checkpoint.

## Feature 2: Signal Submission and Membrane Admission

Operators can submit signal payloads and see why a signal was accepted or rejected.

Backend tasks:
- Derive `actor.actor_id` from the authenticated user; do not accept client-supplied actor identity.
- Map session roles into the signal actor in v1, defaulting authenticated users to `operator`.
- Validate signal schema by type.
- Enforce actor auth, required roles, rate limits, signal relevance to genome modules, and toxic-input filters.
- Emit membrane events for both accepted and rejected signals.
- Guarantee rejected signals create no protein.

Frontend tasks:
- Add signal type input and JSON payload editor.
- Show membrane decision code, reason, actor id, and trace payload after submission.
- Display rejected-state feedback without showing a protein panel result.
- Preserve the default smoke payload: `calculate` with `{ "expression": "1+1" }`.

Acceptance criteria:
- Valid calculate signals are accepted.
- Missing calculate `expression`, unsafe text, unauthorized actor roles, and rate-limit breaches are rejected.
- Rejected signals show membrane events and no protein.

## Feature 3: Organelle Execution Trace

Operators can inspect how a signal moved through cytoplasm, nucleus, mitochondria, ribosome, golgi, lysosome, peroxisome, vacuole, and skeleton.

Backend tasks:
- Emit cytoplasm events for context refs, priority, and route selection.
- Emit nucleus events with selected module and expression profile.
- Emit mitochondria events with budget reservation and remaining compute/tool-call budget.
- Emit ribosome events with selected strategy and deterministic tool name.
- Emit golgi events with final protein status and validation report.
- Emit lysosome cleanup events for temporary state and misfolded proteins.
- Emit peroxisome events when toxic outputs are blocked.
- Emit vacuole events when runtime artifacts are cached.

Frontend tasks:
- Add an execution trace tab sorted newest-first.
- Show event type, timestamp, message, and `values` JSON.
- Add visual emphasis for membrane, mitochondria, ribosome, protein, peroxisome, and structure-request events.
- Keep long JSON payloads scrollable inside fixed-height blocks.

Acceptance criteria:
- A successful calculate signal displays membrane, cytoplasm, nucleus, mitochondria, ribosome, golgi, lysosome, vacuole, and lifecycle events.
- Toxic protein output displays a peroxisome event.
- Quota exhaustion displays a mitochondria event with `reserved: false`.

## Feature 4: Deterministic Ribosome Routing

Exact tasks must route to deterministic tools and never to `llm_stub`.

Backend tasks:
- Route arithmetic signals to the calculator deterministic tool.
- Route known contract calls to the contract gateway deterministic tool.
- Keep `llm_stub` only for non-exact query work.
- Add tests proving exact schema-matched tasks never use `llm_stub`.
- Catch deterministic tool errors and convert them into execution misfolding reports instead of server errors.

Frontend tasks:
- Show ribosome strategy and deterministic tool in the execution trace.
- Display protein method, status, confidence, and validation report in the protein viewer.

Acceptance criteria:
- `calculate {"expression":"1+1"}` returns result `2` with `method: deterministic_calculator`.
- Ribosome trace shows `strategy: deterministic_tool` and `deterministic_tool: calculator`.
- Invalid arithmetic does not crash the API; it produces a dropped protein with execution misfolding.

## Feature 5: Protein Validation and Misfolding Pipeline

Every generated protein is validated before approval, repair, drop, or block.

Backend tasks:
- Add `validation_report.misfolding_types`.
- Classify misfolding as `structural`, `semantic`, `execution`, `context`, or `toxic`.
- Validate structure, expected payload fields, semantic constraints, context/permission constraints, and safety.
- Attempt deterministic repair only where explicit rules exist.
- Mark toxic proteins as `blocked`.
- Mark unresolved non-toxic misfolding as `dropped`.
- Emit protein, golgi, lysosome, and peroxisome events as appropriate.

Frontend tasks:
- Show protein status badges.
- Show misfolding type badges.
- Show validation errors and repaired state.
- Make the raw protein JSON available for debugging.

Acceptance criteria:
- Valid deterministic proteins are `approved`.
- Toxic proteins are `blocked` and include `toxic` misfolding.
- Execution failures include `execution` misfolding and do not return HTTP 500.
- Repaired proteins show `repaired: true`.

## Feature 6: Skeletal Contract Registry

Operators can manage contracts and cells can use only known contracts.

Backend tasks:
- Add contract fields: `dependencies`, `created_by`, and `deprecated_reason`.
- Implement osteoblast behavior for contract creation/update.
- Implement osteoclast behavior for safe deprecation with dependency and usage checks.
- Implement osteocyte monitoring through runtime events and read APIs.
- Increment usage count when a known active contract is consumed.
- Reject or drop invalid contract calls with semantic/context validation.

Frontend tasks:
- Add contract registry view.
- Show allowed actions, permissions, rate limits, dependencies, usage count, creator, and deprecation reason.
- Add contract creation shortcut for demo/runtime smoke.
- Add deprecate action and show conflict errors when dependencies or usage block deprecation.

Acceptance criteria:
- Known active contracts are consumed by `contract.call`.
- Deprecation is blocked when usage or dependency checks fail.
- Dependency-free unused contracts can be deprecated.

## Feature 7: Structure Request Queue

Missing contracts create explicit structure requests instead of implicit access.

Backend tasks:
- Add `GET /api/structure-requests`.
- Add `POST /api/structure-requests/{id}/resolve`.
- Add `POST /api/structure-requests/{id}/block`.
- Scope structure requests by organism owner.
- Emit structure-request and skeleton events for open, resolved, and blocked requests.

Frontend tasks:
- Add structure-request queue to the contract/skeleton tab.
- Show requested contract, reason, status, id, and created timestamp.
- Add resolve and block actions for open requests.
- Refresh queue after signal submission and queue actions.

Acceptance criteria:
- Missing contract calls create an open structure request and no protein.
- Open requests can be resolved or blocked.
- Users cannot view or mutate another user’s structure requests.

## Feature 8: Durable Runtime Persistence

Postgres should persist runtime records without deleting observability history.

Backend tasks:
- Use per-table upsert repositories for organisms, cells, genomes, signals, proteins, contracts, and structure requests.
- Keep `runtime_events` append-only with `ON CONFLICT DO NOTHING`.
- Keep memory-mode runtime only as degraded local/demo mode.
- Add schema migrations for new contract fields.
- Add persistence tests for restart/load behavior.

Frontend tasks:
- Show storage mode/degraded status in the console header or settings surface.
- Warn operators when running in memory mode.

Acceptance criteria:
- Fresh schema applies cleanly.
- Runtime records survive process restart when Postgres is configured.
- Runtime events remain ordered and append-only.

## Feature 9: Auth Boundaries and Operator Safety

All organism runtime resources are user-scoped in v1.

Backend tasks:
- Enforce owner boundaries for organisms, events, proteins, contracts, and structure requests.
- Return 404 for cross-user resource access.
- Keep CSRF origin checks compatible with configured frontend origins.
- Add API tests for cross-user reads and mutations.

Frontend tasks:
- Keep session bootstrap for local demo mode.
- Add clear login/signup paths for non-demo operation.
- Show actionable errors for expired sessions or unauthorized access.

Acceptance criteria:
- User A cannot access User B’s organisms, contracts, events, proteins, or structure requests.
- Signal actor id always equals the authenticated user id.

## Feature 10: Removed Simulator Surface Hardening

The ATP simulator and run dashboard must remain unreachable.

Backend tasks:
- Keep `/api/runs*` and `/api/default-scenario` absent from OpenAPI.
- Keep removed BI/export modules as explicit removed-feature stubs or delete unused imports.
- Remove dead imports that reference run dashboards, population charts, ATP simulation, BI exports, or lineage scenes.

Frontend tasks:
- Ensure no active UI imports run detail, compare-runs, metrics charts, BI export panel, lineage scene, or scenario editor components.
- Keep the organism console as the first authenticated screen.

Acceptance criteria:
- `/api/runs*` and `/api/default-scenario` return 404.
- Frontend build has no active references to removed simulator components.

## V1 Test Matrix

Backend:
- `python -m pytest -q`
- Unit tests for membrane, nucleus, mitochondria, ribosome, protein pipeline, lifecycle, skeleton, and structure requests.
- API tests for full signal flow, contract flow, structure-request flow, auth boundaries, and removed endpoints.
- Persistence tests for schema application, upserts, reload behavior, and append-only events.

Frontend:
- `npm run lint`
- `npm run build`
- Browser smoke: console loads, creates or selects organism, submits `calculate {"expression":"1+1"}`, displays approved deterministic protein, and shows organelle trace.

Manual checks:
- Submit unsafe input and confirm membrane rejection.
- Submit missing contract call and confirm open structure request.
- Resolve/block structure requests from the console.
- Attempt contract deprecation with usage/dependencies and confirm conflict handling.

## V1 Non-Goals

- No live LLM provider calls.
- No Terraform or destructive infrastructure mutation.
- No compatibility with old ATP run data.
- No population simulation, scenario editor, lineage scene, or BI export UI.
- No enterprise credential access in cells or contracts.

