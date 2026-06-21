CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT,
    email_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS password_policy (
    policy_id TEXT PRIMARY KEY DEFAULT 'default',
    min_length INTEGER NOT NULL DEFAULT 12,
    require_uppercase BOOLEAN NOT NULL DEFAULT true,
    require_lowercase BOOLEAN NOT NULL DEFAULT true,
    require_digit BOOLEAN NOT NULL DEFAULT true,
    require_special BOOLEAN NOT NULL DEFAULT true
);

INSERT INTO password_policy (policy_id)
VALUES ('default')
ON CONFLICT (policy_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS organisms (
    organism_id TEXT PRIMARY KEY,
    owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    lifecycle_state TEXT NOT NULL,
    identity_profile JSONB NOT NULL,
    long_term_memory JSONB NOT NULL,
    goals JSONB NOT NULL,
    policies JSONB NOT NULL,
    organ_registry JSONB NOT NULL,
    tissue_templates JSONB NOT NULL,
    cell_blueprints JSONB NOT NULL,
    genome_id TEXT NOT NULL,
    development_stage TEXT NOT NULL DEFAULT 'born',
    growth_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    lineage_log JSONB NOT NULL,
    last_state_snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE organisms ADD COLUMN IF NOT EXISTS development_stage TEXT NOT NULL DEFAULT 'born';
ALTER TABLE organisms ADD COLUMN IF NOT EXISTS growth_state JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS genomes (
    genome_id TEXT PRIMARY KEY,
    version INTEGER NOT NULL CHECK (version > 0),
    core_instruction_set JSONB NOT NULL,
    modules JSONB NOT NULL,
    regulatory_rules JSONB NOT NULL,
    capability_registry JSONB NOT NULL,
    constraints JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS cells (
    cell_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    organ_id TEXT NOT NULL DEFAULT 'core',
    tissue_id TEXT NOT NULL,
    cell_type TEXT NOT NULL,
    cell_genome_id TEXT,
    expression_profile JSONB NOT NULL,
    local_state JSONB NOT NULL,
    lifecycle_state TEXT NOT NULL,
    health_state TEXT NOT NULL DEFAULT 'alive',
    health_score DOUBLE PRECISION NOT NULL DEFAULT 1,
    parent_cell_id TEXT,
    generation INTEGER NOT NULL DEFAULT 0,
    resource_budget JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    last_active_at TIMESTAMPTZ
);

ALTER TABLE cells ADD COLUMN IF NOT EXISTS organ_id TEXT NOT NULL DEFAULT 'core';
ALTER TABLE cells ADD COLUMN IF NOT EXISTS cell_genome_id TEXT;
ALTER TABLE cells ADD COLUMN IF NOT EXISTS health_state TEXT NOT NULL DEFAULT 'alive';
ALTER TABLE cells ADD COLUMN IF NOT EXISTS health_score DOUBLE PRECISION NOT NULL DEFAULT 1;
ALTER TABLE cells ADD COLUMN IF NOT EXISTS parent_cell_id TEXT;
ALTER TABLE cells ADD COLUMN IF NOT EXISTS generation INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS signals (
    signal_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    actor JSONB NOT NULL,
    type TEXT NOT NULL,
    payload JSONB NOT NULL,
    context_refs JSONB NOT NULL,
    priority INTEGER NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS proteins (
    protein_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    source_signal_id TEXT NOT NULL,
    type TEXT NOT NULL,
    payload JSONB NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL,
    validation_report JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS contracts (
    contract_id TEXT PRIMARY KEY,
    owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    schema JSONB NOT NULL,
    allowed_actions JSONB NOT NULL,
    permissions JSONB NOT NULL,
    rate_limits JSONB NOT NULL,
    dependencies JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_by TEXT,
    deprecated_reason TEXT,
    status TEXT NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE contracts ADD COLUMN IF NOT EXISTS dependencies JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS created_by TEXT;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS deprecated_reason TEXT;

CREATE TABLE IF NOT EXISTS runtime_events (
    event_id TEXT PRIMARY KEY,
    organism_id TEXT,
    cell_id TEXT,
    signal_id TEXT,
    protein_id TEXT,
    contract_id TEXT,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    values JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_records (
    memory_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    scope TEXT NOT NULL DEFAULT 'organism',
    kind TEXT NOT NULL,
    payload JSONB NOT NULL,
    source_signal_id TEXT,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active',
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE memory_records ADD COLUMN IF NOT EXISTS scope TEXT NOT NULL DEFAULT 'organism';
ALTER TABLE memory_records ADD COLUMN IF NOT EXISTS source_signal_id TEXT;
ALTER TABLE memory_records ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION NOT NULL DEFAULT 1;
ALTER TABLE memory_records ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE memory_records ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE memory_records ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE TABLE IF NOT EXISTS capabilities (
    capability_id TEXT PRIMARY KEY,
    owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    schema JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS genome_versions (
    version_id TEXT PRIMARY KEY,
    genome_id TEXT NOT NULL,
    owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    version INTEGER NOT NULL,
    genome JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    activated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS replay_runs (
    replay_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    signal_id TEXT NOT NULL,
    original_protein JSONB,
    replay_protein JSONB,
    events JSONB NOT NULL,
    divergence_report JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS policy_versions (
    policy_version_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    policies JSONB NOT NULL,
    created_by TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS maintenance_runs (
    run_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    results JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_alerts (
    alert_id TEXT PRIMARY KEY,
    organism_id TEXT,
    severity TEXT NOT NULL,
    source TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    related_event_id TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS review_requests (
    review_id TEXT PRIMARY KEY,
    owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    action TEXT NOT NULL,
    before JSONB NOT NULL,
    after JSONB NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    reviewer_id TEXT,
    decision_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    decided_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS structure_requests (
    request_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    signal_id TEXT,
    requested_contract TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS zygotes (
    zygote_id TEXT PRIMARY KEY,
    owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    mother_organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    father_organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    genome JSONB NOT NULL,
    stage TEXT NOT NULL,
    oxygen_restricted BOOLEAN NOT NULL,
    food_log JSONB NOT NULL,
    founder_plan JSONB NOT NULL,
    born_organism_id TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS organs (
    organ_id TEXT NOT NULL,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    target_cell_count INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (organism_id, organ_id)
);

CREATE TABLE IF NOT EXISTS tissues (
    tissue_id TEXT NOT NULL,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    organ_id TEXT NOT NULL,
    name TEXT NOT NULL,
    target_cell_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (organism_id, tissue_id)
);

CREATE TABLE IF NOT EXISTS cell_divisions (
    division_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    parent_cell_id TEXT NOT NULL,
    daughter_cell_ids JSONB NOT NULL,
    mode TEXT NOT NULL,
    genome_copied BOOLEAN NOT NULL,
    organelles_duplicated BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS food_intakes (
    food_id TEXT PRIMARY KEY,
    organism_id TEXT REFERENCES organisms(organism_id) ON DELETE CASCADE,
    zygote_id TEXT,
    food_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    routed_to JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS oxygen_profiles (
    oxygen_id TEXT PRIMARY KEY,
    organism_id TEXT REFERENCES organisms(organism_id) ON DELETE CASCADE,
    zygote_id TEXT,
    compute_units INTEGER NOT NULL,
    memory_units INTEGER NOT NULL,
    storage_units INTEGER NOT NULL,
    gpu_units INTEGER NOT NULL,
    restricted BOOLEAN NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS umbilical_cords (
    cord_id TEXT PRIMARY KEY,
    zygote_id TEXT NOT NULL,
    mother_organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    oxygen_profile_id TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS soul_snapshots (
    soul_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    snapshot JSONB NOT NULL,
    reincarnated_organism_id TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS bone_structures (
    bone_id TEXT PRIMARY KEY,
    owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    structure_type TEXT NOT NULL,
    definition JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS structure_proposals (
    proposal_id TEXT PRIMARY KEY,
    owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    requested_by TEXT,
    name TEXT NOT NULL,
    structure_type TEXT NOT NULL,
    definition JSONB NOT NULL,
    status TEXT NOT NULL,
    decision_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    decided_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS organelle_pipelines (
    pipeline_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    cell_id TEXT NOT NULL,
    stages JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS vesicle_messages (
    vesicle_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    source_cell_id TEXT NOT NULL,
    target_cell_id TEXT,
    payload JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS cytoskeleton_topologies (
    topology_id TEXT PRIMARY KEY,
    organism_id TEXT NOT NULL REFERENCES organisms(organism_id) ON DELETE CASCADE,
    organ_edges JSONB NOT NULL,
    tissue_edges JSONB NOT NULL,
    cell_edges JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions (token_hash);
CREATE INDEX IF NOT EXISTS idx_organisms_owner_created ON organisms (owner_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cells_organism ON cells (organism_id);
CREATE INDEX IF NOT EXISTS idx_signals_organism_created ON signals (organism_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_proteins_organism_created ON proteins (organism_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_runtime_events_organism_created ON runtime_events (organism_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_structure_requests_organism_status ON structure_requests (organism_id, status);
CREATE INDEX IF NOT EXISTS idx_memory_records_organism_status ON memory_records (organism_id, status);
CREATE INDEX IF NOT EXISTS idx_genome_versions_genome_version ON genome_versions (genome_id, version);
CREATE INDEX IF NOT EXISTS idx_replay_runs_organism_signal ON replay_runs (organism_id, signal_id);
CREATE INDEX IF NOT EXISTS idx_policy_versions_organism_version ON policy_versions (organism_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_runtime_alerts_status ON runtime_alerts (status, severity);
CREATE INDEX IF NOT EXISTS idx_review_requests_owner_status ON review_requests (owner_user_id, status);
CREATE INDEX IF NOT EXISTS idx_zygotes_owner_stage ON zygotes (owner_user_id, stage);
CREATE INDEX IF NOT EXISTS idx_cells_organ_tissue ON cells (organism_id, organ_id, tissue_id);
CREATE INDEX IF NOT EXISTS idx_cell_divisions_organism_created ON cell_divisions (organism_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_food_intakes_organism_created ON food_intakes (organism_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oxygen_profiles_organism ON oxygen_profiles (organism_id);
CREATE INDEX IF NOT EXISTS idx_soul_snapshots_organism ON soul_snapshots (organism_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_structure_proposals_owner_status ON structure_proposals (owner_user_id, status);
CREATE INDEX IF NOT EXISTS idx_bone_structures_owner_status ON bone_structures (owner_user_id, status);
