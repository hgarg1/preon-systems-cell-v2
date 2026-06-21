export type LifecycleState = "hibernated" | "active" | "degraded" | "terminated";
export type ProteinStatus = "generated" | "approved" | "repaired" | "dropped" | "blocked";
export type ContractStatus = "active" | "deprecated";
export type MisfoldingType = "structural" | "semantic" | "execution" | "context" | "toxic";
export type DevelopmentStage = "zygote" | "embryo" | "fetus" | "born" | "juvenile" | "adult" | "degraded" | "dead";
export type DivisionMode = "symmetric" | "asymmetric" | "founder" | "repair";

export interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  email_verified: boolean;
  created_at: string;
}

export interface AuthSessionResponse {
  user: AuthUser;
  email_verification_url?: string | null;
}

export interface ForgotPasswordResponse {
  ok: boolean;
  reset_url?: string | null;
}

export interface HealthResponse {
  status: string;
  runtime: string;
  storage: {
    mode: string;
    primary: string;
    fallback: string;
    degraded: boolean;
  };
}

export interface IdentityProfile {
  name: string;
  purpose: string;
}

export interface OrganismRecord {
  organism_id: string;
  identity_profile: IdentityProfile;
  lifecycle_state: LifecycleState;
  development_stage: DevelopmentStage;
  growth_state: Record<string, unknown>;
  goals: string[];
  genome_id: string;
  long_term_memory: Record<string, unknown>;
  last_state_snapshot: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CellRecord {
  cell_id: string;
  organism_id: string;
  organ_id: string;
  tissue_id: string;
  cell_type: string;
  cell_genome_id: string | null;
  expression_profile: Record<string, number>;
  lifecycle_state: LifecycleState;
  health_state: "alive" | "stressed" | "degraded" | "hibernating" | "self_consuming" | "dead";
  health_score: number;
  parent_cell_id: string | null;
  generation: number;
  resource_budget: Record<string, number>;
  last_active_at: string | null;
}

export interface GenomeModule {
  module_id: string;
  signal_types: string[];
  execution_strategy: "precomputed" | "deterministic_tool" | "llm_stub";
  deterministic_tool: string | null;
}

export interface DivisionLoadGate {
  min_protein_throughput: number;
}

export interface DivisionCapabilityGate {
  min_successful_proteins: number;
  min_distinct_signal_types: number;
  min_avg_confidence: number;
}

export interface DivisionLifecycleGate {
  max_generation: number;
  required_lifecycle_state: string;
}

export interface DivisionGates {
  load: DivisionLoadGate;
  capability: DivisionCapabilityGate;
  lifecycle: DivisionLifecycleGate;
}

export interface DivisionPolicy {
  can_divide: boolean;
  gates: DivisionGates;
  allowed_modes: DivisionMode[];
  preferred_mode: DivisionMode;
  cooldown_ms: number;
  max_daughters_per_division: number;
}

export interface GateResult {
  passed: boolean;
  reason: string;
  measured: Record<string, unknown>;
}

export interface DivisionReadinessResult {
  cell_id: string;
  organism_id: string;
  eligible: boolean;
  blocked_by: string | null;
  load_gate: GateResult;
  capability_gate: GateResult;
  lifecycle_gate: GateResult;
  recommended_mode: DivisionMode;
  policy_applied: boolean;
}

export interface Genome {
  genome_id: string;
  version: number;
  core_instruction_set: string[];
  modules: GenomeModule[];
  regulatory_rules: Record<string, unknown>[];
  capability_registry: Record<string, unknown>;
  constraints: Record<string, unknown>;
  division_policy: DivisionPolicy | null;
}

export interface Signal {
  signal_id: string;
  organism_id: string;
  type: string;
  payload: Record<string, unknown>;
  priority: number;
  created_at: string;
}

export interface MembraneDecision {
  action: "accept" | "reject";
  reason: string;
  code: string;
}

export interface Protein {
  protein_id: string;
  organism_id: string;
  source_signal_id: string;
  type: string;
  payload: Record<string, unknown>;
  confidence: number;
  status: ProteinStatus;
  validation_report: {
    valid: boolean;
    errors: string[];
    repaired: boolean;
    misfolding_types: MisfoldingType[];
  };
  created_at: string;
}

export interface RuntimeEvent {
  event_id: string;
  organism_id: string | null;
  cell_id: string | null;
  signal_id: string | null;
  protein_id: string | null;
  contract_id: string | null;
  type: string;
  message: string;
  values: Record<string, unknown>;
  created_at: string;
}

export interface Contract {
  contract_id: string;
  owner_user_id: string | null;
  name: string;
  schema: Record<string, unknown>;
  allowed_actions: string[];
  permissions: string[];
  rate_limits: Record<string, number>;
  dependencies: string[];
  adapter_id: string | null;
  input_mapping: Record<string, string>;
  output_mapping: Record<string, string>;
  capability_ids: string[];
  test_vectors: Record<string, unknown>[];
  created_by: string | null;
  deprecated_reason: string | null;
  status: ContractStatus;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface StructureRequest {
  request_id: string;
  organism_id: string;
  signal_id: string | null;
  requested_contract: string;
  reason: string;
  status: "open" | "resolved" | "blocked";
  created_at: string;
}

export interface MemoryRecord {
  memory_id: string;
  organism_id: string;
  scope: string;
  kind: string;
  payload: Record<string, unknown>;
  source_signal_id: string | null;
  confidence: number;
  status: "active" | "deprecated" | "pending" | "approved" | "rejected";
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Capability {
  capability_id: string;
  owner_user_id: string | null;
  name: string;
  description: string;
  schema: Record<string, unknown>;
  status: "active" | "deprecated" | "pending" | "approved" | "rejected";
  created_at: string;
  updated_at: string;
}

export interface ReplayRun {
  replay_id: string;
  organism_id: string;
  signal_id: string;
  original_protein: Protein | null;
  replay_protein: Protein | null;
  events: RuntimeEvent[];
  divergence_report: Record<string, unknown>;
  created_at: string;
}

export interface PolicyVersion {
  policy_version_id: string;
  organism_id: string;
  version: number;
  policies: Record<string, unknown>;
  status: "active" | "superseded";
  created_at: string;
}

export interface GenomeVersion {
  version_id: string;
  genome_id: string;
  version: number;
  genome: Genome;
  status: "draft" | "active" | "deprecated";
  created_at: string;
  activated_at: string | null;
}

export interface ReviewRequest {
  review_id: string;
  resource_type: string;
  resource_id: string;
  action: string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  reason: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}

export interface OrganismDetail {
  organism: OrganismRecord;
  genome: Genome;
  cells: CellRecord[];
  events: RuntimeEvent[];
  proteins: Protein[];
  structure_requests: StructureRequest[];
  memory_records: MemoryRecord[];
}

export interface SubmitSignalResponse {
  signal: Signal;
  membrane_decision: MembraneDecision;
  cell: CellRecord | null;
  protein: Protein | null;
  events: RuntimeEvent[];
  structure_request: StructureRequest | null;
}

export interface ZygoteRecord {
  zygote_id: string;
  mother_organism_id: string;
  father_organism_id: string;
  stage: DevelopmentStage;
  genome: Record<string, unknown>;
  born_organism_id: string | null;
  food_log: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
}

export interface V3Summary {
  negotiation?: Record<string, unknown>;
  zygote?: ZygoteRecord;
  growth?: Record<string, unknown>;
  division?: Record<string, unknown>;
  food?: Record<string, unknown>;
  oxygen?: Record<string, unknown>;
  health?: Record<string, unknown>;
  soul?: Record<string, unknown>;
  proposal?: Record<string, unknown>;
  bones?: Record<string, unknown>[];
}

const API_PREFIX = "/backend";
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health", { signal });
}

export async function getCurrentUser(signal?: AbortSignal): Promise<AuthUser> {
  const payload = await apiFetch<{ user: AuthUser }>("/auth/me", { signal });
  return payload.user;
}

export async function signup(input: { email: string; password: string; name?: string }): Promise<AuthSessionResponse> {
  return apiFetch<AuthSessionResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function login(input: { email: string; password: string }): Promise<AuthSessionResponse> {
  return apiFetch<AuthSessionResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function logout(): Promise<void> {
  await apiFetch<{ ok: boolean }>("/auth/logout", { method: "POST" });
}

export async function forgotPassword(email: string): Promise<ForgotPasswordResponse> {
  return apiFetch<ForgotPasswordResponse>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(input: { token: string; password: string }): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function verifyEmail(token: string): Promise<AuthSessionResponse> {
  return apiFetch<AuthSessionResponse>("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export async function getOAuthProvider(provider: string): Promise<{ provider: string; configured: boolean; authorization_url?: string | null }> {
  return apiFetch(`/auth/oauth/${encodeURIComponent(provider)}`);
}

export async function exchangeOAuthCode(provider: string, code: string, state?: string): Promise<AuthSessionResponse> {
  return apiFetch<AuthSessionResponse>(`/auth/oauth/${encodeURIComponent(provider)}/callback`, {
    method: "POST",
    body: JSON.stringify({ code, state }),
  });
}

export async function listOrganisms(signal?: AbortSignal): Promise<OrganismRecord[]> {
  const payload = await apiFetch<{ organisms: OrganismRecord[] }>("/api/organisms", { signal });
  return payload.organisms;
}

export async function createOrganism(input: { name: string; purpose: string; goals: string[] }): Promise<OrganismRecord> {
  const payload = await apiFetch<{ organism: OrganismRecord }>("/api/organisms", {
    method: "POST",
    body: JSON.stringify({
      identity_profile: { name: input.name, purpose: input.purpose },
      goals: input.goals,
    }),
  });
  return payload.organism;
}

export async function getOrganism(organismId: string, signal?: AbortSignal): Promise<OrganismDetail> {
  return apiFetch<OrganismDetail>(`/api/organisms/${encodeURIComponent(organismId)}`, { signal });
}

export async function wakeOrganism(organismId: string): Promise<OrganismRecord> {
  const payload = await apiFetch<{ organism: OrganismRecord }>(`/api/organisms/${encodeURIComponent(organismId)}/wake`, {
    method: "POST",
  });
  return payload.organism;
}

export async function hibernateOrganism(organismId: string): Promise<OrganismRecord> {
  const payload = await apiFetch<{ organism: OrganismRecord }>(`/api/organisms/${encodeURIComponent(organismId)}/hibernate`, {
    method: "POST",
  });
  return payload.organism;
}

export async function submitSignal(organismId: string, input: { type: string; payload: Record<string, unknown>; priority?: number }): Promise<SubmitSignalResponse> {
  return apiFetch<SubmitSignalResponse>(`/api/organisms/${encodeURIComponent(organismId)}/signals`, {
    method: "POST",
    body: JSON.stringify({ type: input.type, payload: input.payload, priority: input.priority ?? 5 }),
  });
}

export async function listContracts(signal?: AbortSignal): Promise<Contract[]> {
  const payload = await apiFetch<{ contracts: Contract[] }>("/api/contracts", { signal });
  return payload.contracts;
}

export async function createContract(input: { name: string; allowedActions: string[]; schema?: Record<string, unknown>; dependencies?: string[] }): Promise<Contract> {
  const payload = await apiFetch<{ contract: Contract }>("/api/contracts", {
    method: "POST",
    body: JSON.stringify({
      name: input.name,
      allowed_actions: input.allowedActions,
      schema: input.schema ?? {},
      dependencies: input.dependencies ?? [],
    }),
  });
  return payload.contract;
}

export async function createCell(organismId: string, input: { tissueId: string; cellType: string; expressionProfile: Record<string, number> }): Promise<CellRecord> {
  const payload = await apiFetch<{ cell: CellRecord }>(`/api/organisms/${encodeURIComponent(organismId)}/cells`, {
    method: "POST",
    body: JSON.stringify({
      tissue_id: input.tissueId,
      cell_type: input.cellType,
      expression_profile: input.expressionProfile,
    }),
  });
  return payload.cell;
}

export async function negotiateReproduction(input: { motherOrganismId: string; fatherOrganismId: string }): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ negotiation: Record<string, unknown> }>("/api/reproduction/negotiate", {
    method: "POST",
    body: JSON.stringify({
      mother_organism_id: input.motherOrganismId,
      father_organism_id: input.fatherOrganismId,
    }),
  });
  return payload.negotiation;
}

export async function createZygote(input: { motherOrganismId: string; fatherOrganismId: string }): Promise<ZygoteRecord> {
  const payload = await apiFetch<{ zygote: ZygoteRecord }>("/api/reproduction/zygote", {
    method: "POST",
    body: JSON.stringify({
      mother_organism_id: input.motherOrganismId,
      father_organism_id: input.fatherOrganismId,
    }),
  });
  return payload.zygote;
}

export async function developZygote(zygoteId: string, targetStage: DevelopmentStage = "embryo"): Promise<ZygoteRecord> {
  const payload = await apiFetch<{ zygote: ZygoteRecord }>(`/api/zygotes/${encodeURIComponent(zygoteId)}/develop`, {
    method: "POST",
    body: JSON.stringify({ target_stage: targetStage, food_payload: { source: "console" } }),
  });
  return payload.zygote;
}

export async function birthZygote(zygoteId: string): Promise<OrganismRecord> {
  const payload = await apiFetch<{ organism: OrganismRecord }>(`/api/zygotes/${encodeURIComponent(zygoteId)}/birth`, { method: "POST" });
  return payload.organism;
}

export async function listZygotes(signal?: AbortSignal): Promise<ZygoteRecord[]> {
  const payload = await apiFetch<{ zygotes: ZygoteRecord[] }>("/api/zygotes", { signal });
  return payload.zygotes;
}

export async function applyGrowthTemplate(organismId: string): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ growth: Record<string, unknown> }>(`/api/organisms/${encodeURIComponent(organismId)}/growth/apply-template`, {
    method: "POST",
    body: JSON.stringify({ template_name: "human_minimal_v3" }),
  });
  return payload.growth;
}

export async function divideCell(organismId: string, cellId: string, mode: DivisionMode = "symmetric"): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ division: Record<string, unknown> }>(
    `/api/organisms/${encodeURIComponent(organismId)}/cells/${encodeURIComponent(cellId)}/divide`,
    { method: "POST", body: JSON.stringify({ mode }) },
  );
  return payload.division;
}

export async function feedOrganism(organismId: string): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ food: Record<string, unknown> }>(`/api/organisms/${encodeURIComponent(organismId)}/food`, {
    method: "POST",
    body: JSON.stringify({ food_type: "training_data", payload: { sample: "console food" } }),
  });
  return payload.food;
}

export async function feedOrganismCustom(
  organismId: string,
  input: { food_type: string; payload: Record<string, unknown> },
): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ food: Record<string, unknown> }>(`/api/organisms/${encodeURIComponent(organismId)}/food`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return payload.food;
}

export async function grantOxygen(
  organismId: string,
  amounts?: { compute_units: number; memory_units: number; storage_units: number; gpu_units: number },
): Promise<Record<string, unknown>> {
  const body = amounts
    ? { ...amounts, restricted: false }
    : { compute_units: 12, memory_units: 8, storage_units: 24, gpu_units: 1, restricted: false };
  const payload = await apiFetch<{ oxygen: Record<string, unknown> }>(`/api/organisms/${encodeURIComponent(organismId)}/oxygen`, {
    method: "POST",
    body: JSON.stringify(body),
  });
  return payload.oxygen;
}

export async function getOrganismHealth(organismId: string): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ health: Record<string, unknown> }>(`/api/organisms/${encodeURIComponent(organismId)}/health`);
  return payload.health;
}

export async function dieOrganism(organismId: string): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ soul: Record<string, unknown> }>(`/api/organisms/${encodeURIComponent(organismId)}/die`, { method: "POST" });
  return payload.soul;
}

export async function createBoneProposal(): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ proposal: Record<string, unknown> }>("/api/bones/proposals", {
    method: "POST",
    body: JSON.stringify({ name: "ConsoleGeneratedBoneSchema", structure_type: "schema", definition: { input: "object", output: "object" } }),
  });
  return payload.proposal;
}

export async function approveBoneProposal(proposalId: string): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ proposal: Record<string, unknown> }>(`/api/bones/proposals/${encodeURIComponent(proposalId)}/approve`, {
    method: "POST",
    body: JSON.stringify({ reason: "Approved from V3 console" }),
  });
  return payload.proposal;
}

export async function createMemory(organismId: string, input: { scope: string; kind: string; payload: Record<string, unknown> }): Promise<MemoryRecord> {
  const payload = await apiFetch<{ memory_record: MemoryRecord }>(`/api/organisms/${encodeURIComponent(organismId)}/memory`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return payload.memory_record;
}

export async function createCapability(input: { name: string; description?: string; schema?: Record<string, unknown> }): Promise<Capability> {
  const payload = await apiFetch<{ capability: Capability }>("/api/capabilities", {
    method: "POST",
    body: JSON.stringify({ name: input.name, description: input.description ?? "", schema: input.schema ?? {} }),
  });
  return payload.capability;
}

export async function listCapabilities(signal?: AbortSignal): Promise<Capability[]> {
  const payload = await apiFetch<{ capabilities: Capability[] }>("/api/capabilities", { signal });
  return payload.capabilities;
}

export async function validateContractAdapter(contractId: string): Promise<{ valid: boolean; errors: string[]; repaired: boolean; misfolding_types: MisfoldingType[] }> {
  const payload = await apiFetch<{ report: { valid: boolean; errors: string[]; repaired: boolean; misfolding_types: MisfoldingType[] } }>(
    `/api/contracts/${encodeURIComponent(contractId)}/validate-adapter`,
    { method: "POST" },
  );
  return payload.report;
}

export async function replaySignal(organismId: string, signalId: string): Promise<ReplayRun> {
  const payload = await apiFetch<{ replay: ReplayRun }>(`/api/organisms/${encodeURIComponent(organismId)}/signals/${encodeURIComponent(signalId)}/replay`, {
    method: "POST",
  });
  return payload.replay;
}

export async function getPolicy(organismId: string): Promise<PolicyVersion> {
  const payload = await apiFetch<{ policy_version: PolicyVersion }>(`/api/organisms/${encodeURIComponent(organismId)}/policies`);
  return payload.policy_version;
}

export async function simulatePolicy(organismId: string): Promise<MembraneDecision> {
  const payload = await apiFetch<{ membrane_decision: MembraneDecision }>(`/api/organisms/${encodeURIComponent(organismId)}/policies/simulate`, {
    method: "POST",
    body: JSON.stringify({ signal: { type: "calculate", payload: { expression: "1+1" } } }),
  });
  return payload.membrane_decision;
}

export async function previewGenome(organismId: string): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ preview: Record<string, unknown> }>(`/api/organisms/${encodeURIComponent(organismId)}/genome/preview`, {
    method: "POST",
    body: JSON.stringify({ signal_type: "calculate", payload: { expression: "1+1" } }),
  });
  return payload.preview;
}

export async function runMaintenance(): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ run: Record<string, unknown> }>("/api/maintenance/run", { method: "POST" });
  return payload.run;
}

export async function getRuntimeMetrics(organismId?: string): Promise<Record<string, unknown>> {
  const path = organismId ? `/api/metrics/organisms/${encodeURIComponent(organismId)}` : "/api/metrics/runtime";
  const payload = await apiFetch<{ metrics: Record<string, unknown> }>(path);
  return payload.metrics;
}

export async function exportOrganism(organismId: string): Promise<Record<string, unknown>> {
  const payload = await apiFetch<{ bundle: Record<string, unknown> }>(`/api/organisms/${encodeURIComponent(organismId)}/export`);
  return payload.bundle;
}

export async function createReview(input: { resourceType: string; resourceId: string; action: string; reason: string }): Promise<ReviewRequest> {
  const payload = await apiFetch<{ review: ReviewRequest }>("/api/reviews", {
    method: "POST",
    body: JSON.stringify({
      resource_type: input.resourceType,
      resource_id: input.resourceId,
      action: input.action,
      reason: input.reason,
    }),
  });
  return payload.review;
}

export async function listReviews(signal?: AbortSignal): Promise<ReviewRequest[]> {
  const payload = await apiFetch<{ reviews: ReviewRequest[] }>("/api/reviews", { signal });
  return payload.reviews;
}

export async function deprecateContract(contractId: string): Promise<Contract> {
  const payload = await apiFetch<{ contract: Contract }>(`/api/contracts/${encodeURIComponent(contractId)}/deprecate`, {
    method: "POST",
  });
  return payload.contract;
}

export async function listStructureRequests(signal?: AbortSignal): Promise<StructureRequest[]> {
  const payload = await apiFetch<{ structure_requests: StructureRequest[] }>("/api/structure-requests", { signal });
  return payload.structure_requests;
}

export async function resolveStructureRequest(requestId: string, contractId?: string): Promise<StructureRequest> {
  const payload = await apiFetch<{ structure_request: StructureRequest }>(`/api/structure-requests/${encodeURIComponent(requestId)}/resolve`, {
    method: "POST",
    body: JSON.stringify({ contract_id: contractId ?? null }),
  });
  return payload.structure_request;
}

export async function blockStructureRequest(requestId: string, reason: string): Promise<StructureRequest> {
  const payload = await apiFetch<{ structure_request: StructureRequest }>(`/api/structure-requests/${encodeURIComponent(requestId)}/block`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
  return payload.structure_request;
}

export async function getGenome(genomeId: string, signal?: AbortSignal): Promise<Genome> {
  const payload = await apiFetch<{ genome: Genome }>(`/api/genomes/${encodeURIComponent(genomeId)}`, { signal });
  return payload.genome;
}

export async function updateGenomeDivisionPolicy(genomeId: string, policy: DivisionPolicy): Promise<Genome> {
  const payload = await apiFetch<{ genome: Genome }>(`/api/genomes/${encodeURIComponent(genomeId)}/division-policy`, {
    method: "PATCH",
    body: JSON.stringify({ policy }),
  });
  return payload.genome;
}

export async function checkDivisionReadiness(organismId: string, cellId: string): Promise<DivisionReadinessResult> {
  const payload = await apiFetch<{ readiness: DivisionReadinessResult }>(
    `/api/organisms/${encodeURIComponent(organismId)}/cells/${encodeURIComponent(cellId)}/division-readiness`,
  );
  return payload.readiness;
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    try {
      const payload = await response.json();
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (Array.isArray(payload.detail)) {
        message = payload.detail.join(", ");
      }
    } catch {
      // Keep default message.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function getBackendUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
