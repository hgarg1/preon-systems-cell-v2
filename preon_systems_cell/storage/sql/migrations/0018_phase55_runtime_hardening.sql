ALTER TABLE memory_records ADD COLUMN IF NOT EXISTS admission_policy_version_id TEXT;
ALTER TABLE structure_proposals ADD COLUMN IF NOT EXISTS source_run_id TEXT;
ALTER TABLE structure_proposals ADD COLUMN IF NOT EXISTS source_protein_ids JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS memory_policy_versions (
    policy_version_id TEXT PRIMARY KEY,
    organism_id TEXT REFERENCES organisms(organism_id) ON DELETE CASCADE,
    owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    version INTEGER NOT NULL,
    min_confidence DOUBLE PRECISION NOT NULL,
    min_importance DOUBLE PRECISION NOT NULL,
    default_ttl_seconds INTEGER,
    context_token_budget INTEGER NOT NULL,
    low_value_importance DOUBLE PRECISION NOT NULL,
    low_value_age_days INTEGER NOT NULL,
    allow_baseline_substrate_growth BOOLEAN NOT NULL,
    status TEXT NOT NULL,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (organism_id, version)
);

CREATE TABLE IF NOT EXISTS structural_effects (
    effect_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL REFERENCES structure_proposals(proposal_id) ON DELETE CASCADE,
    organism_id TEXT REFERENCES organisms(organism_id) ON DELETE CASCADE,
    owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    provider TEXT NOT NULL,
    plan_digest TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL,
    max_attempts INTEGER NOT NULL,
    next_attempt_at TIMESTAMPTZ NOT NULL,
    lease_owner TEXT,
    lease_expires_at TIMESTAMPTZ,
    last_error TEXT,
    source_run_id TEXT,
    source_protein_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_memory_policy_versions_active
    ON memory_policy_versions (organism_id, status, version DESC);
CREATE INDEX IF NOT EXISTS idx_structural_effects_claim
    ON structural_effects (status, next_attempt_at, lease_expires_at);
