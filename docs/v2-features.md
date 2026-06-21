# V2 Feature Plan

V2 builds on the V1 organism runtime. V1 establishes deterministic organism lifecycle, membrane admission, organelle traces, protein validation, skeletal contracts, structure requests, durable persistence, auth boundaries, and the organism operations console. V2 should make the runtime useful for larger workflows: multiple cells, durable memory, contract adapters, replay/debugging, policy management, and production operations.

V2 remains deterministic-first. Live LLM provider calls, enterprise credentials, Terraform mutation, and destructive infrastructure actions remain out of scope unless explicitly introduced in a later release.

## V2 Product Goals

- Support multi-cell organisms with tissue-specific routing and coordination.
- Promote memory from raw JSON into queryable, versioned, scoped records.
- Make contract adapters first-class so deterministic contract calls can transform inputs and outputs safely.
- Give operators replay, comparison, and debugging tools for runtime events without restoring the old simulator.
- Provide policy and genome editing workflows with validation, preview, and rollback.
- Improve production readiness: retention, pagination, audit trails, metrics, and background maintenance.

## Feature 1: Multi-Cell Tissue Runtime

V1 processes through a single default worker cell. V2 should support multiple cells per organism with tissue roles and expression profiles.

Backend tasks:
- Add APIs for cell management:
  - `GET /api/organisms/{id}/cells`
  - `POST /api/organisms/{id}/cells`
  - `PATCH /api/organisms/{id}/cells/{cell_id}`
  - `POST /api/organisms/{id}/cells/{cell_id}/hibernate`
- Extend `CellRecord` usage to support tissue-specific capabilities, expression weights, and local state ownership.
- Update Cytoplasm routing to select cells by tissue, cell type, signal priority, resource budget, and expression profile.
- Add cell lifecycle events for created, activated, selected, skipped, exhausted, and hibernated.
- Add tests for routing to the correct cell and fallback when a cell is exhausted.

Frontend tasks:
- Add a Cells/Tissues view in the organism console.
- Show cell list grouped by tissue with lifecycle, expression profile, budget, and last active time.
- Add a form to create or edit cells.
- Show why a cell was selected or skipped in the execution trace.

Acceptance criteria:
- An organism can have at least two cells with different expression profiles.
- A query signal routes to the highest-ranked relevant cell.
- An exhausted cell is skipped and trace explains the fallback.

## Feature 2: Memory Records and Recall

V1 stores memory as raw organism state. V2 should make memory durable, scoped, searchable, and traceable.

Backend tasks:
- Implement `memory_records` repository operations.
- Add APIs:
  - `GET /api/organisms/{id}/memory`
  - `POST /api/organisms/{id}/memory`
  - `GET /api/organisms/{id}/memory/{memory_id}`
  - `POST /api/organisms/{id}/memory/{memory_id}/deprecate`
- Add memory fields: `memory_id`, `organism_id`, `scope`, `kind`, `payload`, `source_signal_id`, `confidence`, `status`, `version`, `created_at`, `updated_at`.
- Add deterministic memory write rules for approved proteins.
- Add Cytoplasm recall step that loads relevant memory by signal type, context refs, and scope.
- Emit memory events for recall, write, update, deprecate, and skipped write.
- Add tests for scoped recall and owner isolation.

Frontend tasks:
- Add a Memory tab with filters for kind, scope, status, and source signal.
- Show memory records linked to source signals/proteins.
- Show memory loaded for the latest signal in the trace.
- Add manual memory creation and deprecation controls.

Acceptance criteria:
- Approved proteins can write memory when a rule exists.
- Later signals can recall matching memory.
- Deprecated memory is hidden from recall but remains auditable.

## Feature 3: Contract Adapters and Capability Registry

V1 validates contracts and allowed actions. V2 should support deterministic adapters that map signal payloads to contract schemas and back to protein payloads.

Backend tasks:
- Extend `Contract` with adapter metadata:
  - `adapter_id`
  - `input_mapping`
  - `output_mapping`
  - `capability_ids`
  - `test_vectors`
- Add `capabilities` registry records or a structured registry table.
- Add APIs:
  - `GET /api/capabilities`
  - `POST /api/capabilities`
  - `POST /api/contracts/{id}/validate-adapter`
  - `POST /api/contracts/{id}/test-adapter`
- Implement deterministic adapter validation against schema and test vectors.
- Emit skeleton events for adapter validation, capability registration, and adapter test results.
- Add tests for valid adapter mapping, schema mismatch, missing capability, and adapter test failure.

Frontend tasks:
- Add adapter fields to contract creation/editing.
- Add a contract adapter test panel with sample payload input and output preview.
- Show capability coverage and missing capability warnings in the registry.
- Show adapter validation errors inline.

Acceptance criteria:
- A contract adapter can transform a `contract.call` payload into the contract input schema.
- Invalid mappings are rejected before contract activation.
- Adapter test vectors are visible and executable from the console.

## Feature 4: Runtime Replay and Event Debugger

V1 shows event traces. V2 should let operators replay and compare deterministic signal execution without mutating current state.

Backend tasks:
- Add APIs:
  - `GET /api/organisms/{id}/signals/{signal_id}/replay`
  - `POST /api/organisms/{id}/signals/{signal_id}/replay`
  - `GET /api/organisms/{id}/events?cursor=&limit=&type=&signal_id=`
- Implement replay mode that reconstructs signal processing from stored organism/cell/genome snapshots and returns replay events/protein without persisting side effects.
- Add event pagination and filtering.
- Add replay divergence report comparing original and replayed membrane/ribosome/protein outcomes.
- Add tests for deterministic replay matching original results and no persistence side effects.

Frontend tasks:
- Add event filters by type, signal id, cell id, protein id, and contract id.
- Add replay action from a signal or event trace.
- Show original vs replay comparison.
- Add copyable debug bundle JSON for support/debugging.

Acceptance criteria:
- Replaying a deterministic calculate signal produces the same protein payload.
- Replay does not append normal runtime proteins/signals.
- Operators can filter a long event stream without loading the whole history.

## Feature 5: Policy Editor and Admission Simulator

V1 has policy enforcement. V2 should let operators edit policies safely and simulate admission before applying changes.

Backend tasks:
- Add APIs:
  - `GET /api/organisms/{id}/policies`
  - `PUT /api/organisms/{id}/policies`
  - `POST /api/organisms/{id}/policies/validate`
  - `POST /api/organisms/{id}/policies/simulate`
- Version policy changes and store policy audit events.
- Validate rate limits, required roles, allowed signal types, and forbidden terms.
- Simulate membrane admission for sample signals without persisting signals or proteins.
- Add tests for policy validation, simulation, rollback, and owner boundaries.

Frontend tasks:
- Add a Policy tab with editable allowed signal types, forbidden terms, required roles, and rate limits.
- Add dry-run simulation panel using sample signal JSON.
- Show policy version history and rollback action.
- Highlight changes before save.

Acceptance criteria:
- Invalid policy edits are rejected with actionable errors.
- Operators can simulate whether a signal would be accepted or rejected before saving.
- Policy updates emit audit/runtime events.

## Feature 6: Genome Versioning and Expression Preview

V1 validates genomes. V2 should version genomes and preview module/cell selection before applying changes.

Backend tasks:
- Add genome version records and activation state.
- Add APIs:
  - `GET /api/genomes`
  - `POST /api/genomes`
  - `POST /api/genomes/{id}/versions`
  - `POST /api/genomes/{id}/versions/{version}/activate`
  - `POST /api/genomes/{id}/preview`
- Validate modules, deterministic tools, regulatory rules, constraints, and capability references.
- Preview nucleus module selection for sample signals and cell expression profiles.
- Emit nucleus/genome events for version creation, activation, validation, and preview.
- Add tests for duplicate modules, invalid deterministic tools, disabled rules, and preview output.

Frontend tasks:
- Add Genome Versions view.
- Add module/regulatory-rule editor.
- Add expression preview panel with sample signal and selected module result.
- Show active version and rollback controls.

Acceptance criteria:
- Operators can create a new genome version without activating it.
- Preview shows which module would run for a sample signal.
- Activating a version changes future signal routing and emits an event.

## Feature 7: Background Maintenance Organelles

V1 emits lysosome/peroxisome/vacuole events during signal processing. V2 should add scheduled maintenance for cleanup, retention, and stale structure monitoring.

Backend tasks:
- Add a background maintenance runner with configurable interval.
- Implement maintenance jobs:
  - stale structure request detection
  - event retention summary
  - vacuole artifact pruning
  - memory deprecation suggestions
  - contract stale usage monitoring
- Add APIs:
  - `GET /api/maintenance/status`
  - `POST /api/maintenance/run`
- Emit runtime events for each maintenance job result.
- Add tests for stale request detection and non-destructive cleanup.

Frontend tasks:
- Add Maintenance panel in the console.
- Show last run, job statuses, stale requests, stale contracts, and cleanup suggestions.
- Add manual run button for local/demo mode.

Acceptance criteria:
- Maintenance can run without mutating contracts or infrastructure destructively.
- Stale structure requests and stale contracts are visible to operators.
- Maintenance results are auditable through runtime events.

## Feature 8: Metrics, Alerts, and Operational Health

V1 exposes traces. V2 should expose operational metrics and lightweight alerts.

Backend tasks:
- Add metrics endpoints:
  - `GET /api/metrics/runtime`
  - `GET /api/metrics/organisms/{id}`
- Track counts and rates for accepted/rejected signals, protein statuses, misfolding types, quota exhaustion, structure requests, contract usage, and replay divergence.
- Add alert rules for repeated rejections, toxic attempts, quota exhaustion, unresolved structure requests, and storage degradation.
- Emit alert events and expose active alerts.
- Add tests for metrics aggregation and alert triggering.

Frontend tasks:
- Add compact metrics summary to the console header.
- Add Alerts panel with severity, source, reason, and related event links.
- Add trend cards for signal decisions, protein status, misfolding, and contract usage.

Acceptance criteria:
- Metrics update after signal submission.
- Repeated unsafe input creates an active alert.
- Storage degradation is visible as an alert.

## Feature 9: Import, Export, and Debug Bundle

V1 removed BI exports. V2 should add runtime-native import/export for support, backups, and debugging, not BI dashboards.

Backend tasks:
- Add APIs:
  - `GET /api/organisms/{id}/export`
  - `POST /api/organisms/import`
  - `GET /api/organisms/{id}/debug-bundle`
- Export organism identity, cells, genome versions, contracts, memory, structure requests, recent events, and proteins as JSON.
- Redact auth/session data and any fields marked sensitive.
- Validate imports before writing records.
- Add tests for round-trip export/import and redaction.

Frontend tasks:
- Add export and debug-bundle actions to organism settings.
- Add import flow with validation preview.
- Show redaction summary before download.

Acceptance criteria:
- Exported bundles can be imported into a fresh local runtime.
- Debug bundle excludes auth secrets and session tokens.
- Import validation catches id collisions and schema mismatch.

## Feature 10: Collaboration and Review Workflow

V1 is single-operator oriented. V2 should add review workflows for high-impact changes.

Backend tasks:
- Add review records for policy changes, genome activation, contract deprecation, and structure-request resolution.
- Add APIs:
  - `GET /api/reviews`
  - `POST /api/reviews`
  - `POST /api/reviews/{id}/approve`
  - `POST /api/reviews/{id}/reject`
- Require review for configurable actions.
- Store reviewer id, decision, reason, and resulting runtime event.
- Add tests for review requirements and owner boundaries.

Frontend tasks:
- Add Reviews queue.
- Show pending changes with before/after diff.
- Add approve/reject controls and required reason fields.
- Link review decisions to affected contracts, policies, genomes, or structure requests.

Acceptance criteria:
- Configured high-impact changes create pending reviews instead of applying immediately.
- Approved reviews apply the change and emit an event.
- Rejected reviews leave runtime state unchanged.

## V2 Data Model Additions

New or expanded records:
- `MemoryRecord`
- `GenomeVersion`
- `Capability`
- `ContractAdapter`
- `ReplayRun`
- `PolicyVersion`
- `MaintenanceJobRun`
- `RuntimeMetric`
- `RuntimeAlert`
- `DebugBundle`
- `ReviewRequest`

Persistence tasks:
- Add Postgres tables and indexes for new records.
- Add per-record upsert repositories.
- Keep runtime events append-only.
- Add pagination indexes for large event streams.
- Add migration checks for existing V1 databases.

## V2 API Summary

New API families:
- `/api/organisms/{id}/cells*`
- `/api/organisms/{id}/memory*`
- `/api/capabilities*`
- `/api/contracts/{id}/validate-adapter`
- `/api/contracts/{id}/test-adapter`
- `/api/organisms/{id}/signals/{signal_id}/replay`
- `/api/organisms/{id}/policies*`
- `/api/genomes*`
- `/api/maintenance*`
- `/api/metrics*`
- `/api/organisms/{id}/export`
- `/api/organisms/import`
- `/api/organisms/{id}/debug-bundle`
- `/api/reviews*`

Existing V1 APIs remain stable unless explicitly versioned.

## V2 Frontend Navigation

Add or expand console sections:
- Overview
- Signal Console
- Execution Trace
- Cells and Tissues
- Memory
- Contracts and Capabilities
- Structure Requests
- Policies
- Genome Versions
- Replay Debugger
- Maintenance
- Metrics and Alerts
- Reviews
- Import/Export

The first screen should remain the actual organism operations console, not a marketing or landing page.

## V2 Test Matrix

Backend:
- `python -m pytest -q`
- Unit tests for multi-cell routing, memory recall, adapter validation, replay, policies, genome versions, maintenance, metrics, import/export, and reviews.
- API tests for each new route family.
- Persistence tests for all new tables and paginated event queries.
- Auth boundary tests for every new resource.

Frontend:
- `npm run lint`
- `npm run build`
- Browser smoke for:
  - create second cell and route signal
  - write/recall memory
  - validate contract adapter
  - replay a signal
  - simulate policy admission
  - view metrics/alerts

Manual checks:
- Confirm replay has no side effects.
- Confirm debug bundle redacts sensitive fields.
- Confirm review rejection leaves runtime state unchanged.
- Confirm event pagination handles large histories.

## V2 Non-Goals

- No live LLM calls.
- No direct enterprise credential use by cells.
- No Terraform, cloud resource mutation, or destructive infrastructure automation.
- No resurrection of ATP population simulation, run dashboards, lineage scenes, scenario editor, or BI export UI.
- No hidden background mutation outside explicit maintenance jobs and reviewable actions.

## Suggested Implementation Order

1. Event pagination and metrics foundations.
2. Multi-cell tissue routing.
3. Memory records and recall.
4. Contract adapters and capability registry.
5. Runtime replay/debugger.
6. Policy editor and admission simulator.
7. Genome versioning and expression preview.
8. Maintenance jobs and alerts.
9. Import/export/debug bundle.
10. Review workflow.

