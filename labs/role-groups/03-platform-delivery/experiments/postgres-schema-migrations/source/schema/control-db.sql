BEGIN;

CREATE SCHEMA IF NOT EXISTS control_service AUTHORIZATION control_migrator;
SET LOCAL search_path = control_service, pg_catalog;

CREATE TABLE IF NOT EXISTS approval_requests (
    request_id varchar(36) PRIMARY KEY,
    idempotency_key varchar(128) NOT NULL UNIQUE,
    requester_id varchar(255) NOT NULL,
    product_code varchar(64) NOT NULL,
    cpu integer NOT NULL CHECK (cpu BETWEEN 0 AND 64),
    memory_gib integer NOT NULL CHECK (memory_gib BETWEEN 0 AND 512),
    storage_gib integer NOT NULL CHECK (storage_gib BETWEEN 0 AND 4096),
    duration_hours integer NOT NULL CHECK (duration_hours BETWEEN 1 AND 2160),
    purpose text NOT NULL CHECK (char_length(purpose) BETWEEN 5 AND 2000),
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(parameters) = 'object'),
    status varchar(32) NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')),
    event_version integer NOT NULL DEFAULT 1 CHECK (event_version >= 1),
    retry_count integer NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    delivery_status varchar(16) NOT NULL DEFAULT 'PENDING' CHECK (delivery_status IN ('PENDING', 'DELIVERED', 'FAILED', 'SKIPPED')),
    last_error text,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_approval_requests_requester_id ON approval_requests (requester_id);
CREATE INDEX IF NOT EXISTS ix_approval_requests_status ON approval_requests (status);

CREATE TABLE IF NOT EXISTS approval_decisions (
    decision_id varchar(36) PRIMARY KEY,
    request_id varchar(36) NOT NULL REFERENCES approval_requests(request_id) ON DELETE RESTRICT,
    decision varchar(16) NOT NULL CHECK (decision IN ('APPROVED', 'REJECTED')),
    actor_id varchar(255) NOT NULL,
    reason text,
    event_version integer NOT NULL CHECK (event_version >= 2),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (request_id, event_version)
);

CREATE INDEX IF NOT EXISTS ix_approval_decisions_request_id ON approval_decisions (request_id);

CREATE TABLE IF NOT EXISTS provisioning_jobs (
    job_id varchar(36) PRIMARY KEY,
    request_id varchar(36) NOT NULL REFERENCES approval_requests(request_id) ON DELETE RESTRICT,
    idempotency_key varchar(128) NOT NULL UNIQUE,
    operation varchar(16) NOT NULL CHECK (operation IN ('APPLY', 'DESTROY')),
    product_code varchar(64) NOT NULL,
    product_version integer NOT NULL,
    module_name varchar(64) NOT NULL,
    module_version varchar(32) NOT NULL,
    artifact_digest varchar(80) NOT NULL,
    approved_by varchar(255) NOT NULL,
    expires_at timestamptz NOT NULL,
    state_key varchar(255) NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'QUEUED',
    input_values jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(input_values) = 'object'),
    output_values jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(output_values) = 'object'),
    resource_id varchar(36),
    resource_event_version integer NOT NULL DEFAULT 0 CHECK (resource_event_version >= 0),
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    runner_id varchar(128),
    last_error text,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at timestamptz,
    finished_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_provisioning_jobs_request_id ON provisioning_jobs (request_id);
CREATE INDEX IF NOT EXISTS ix_provisioning_jobs_operation ON provisioning_jobs (operation);
CREATE INDEX IF NOT EXISTS ix_provisioning_jobs_status ON provisioning_jobs (status);
CREATE INDEX IF NOT EXISTS ix_provisioning_jobs_state_key ON provisioning_jobs (state_key);

CREATE TABLE IF NOT EXISTS grants (
    grant_id varchar(36) PRIMARY KEY,
    request_id varchar(36) NOT NULL UNIQUE,
    idempotency_key varchar(128) NOT NULL UNIQUE,
    subject_id varchar(255) NOT NULL,
    scopes jsonb NOT NULL CHECK (jsonb_typeof(scopes) = 'array'),
    status varchar(16) NOT NULL CHECK (status IN ('ACTIVE', 'REVOKED', 'EXPIRED')),
    issued_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL CHECK (expires_at > issued_at),
    revoked_at timestamptz,
    event_version integer NOT NULL CHECK (event_version >= 1),
    retry_count integer NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    callback_status varchar(16) NOT NULL DEFAULT 'PENDING' CHECK (callback_status IN ('PENDING', 'DELIVERED', 'FAILED', 'SKIPPED')),
    last_error text,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK ((status = 'REVOKED' AND revoked_at IS NOT NULL) OR status <> 'REVOKED')
);

CREATE INDEX IF NOT EXISTS ix_grants_subject_id ON grants (subject_id);
CREATE INDEX IF NOT EXISTS ix_grants_status ON grants (status);
CREATE INDEX IF NOT EXISTS ix_grants_expires_at ON grants (expires_at);

CREATE TABLE IF NOT EXISTS audit_events (
    audit_id varchar(36) PRIMARY KEY,
    event_type varchar(64) NOT NULL,
    aggregate_type varchar(32) NOT NULL CHECK (aggregate_type IN ('request', 'grant', 'provisioning-job')),
    aggregate_id varchar(36) NOT NULL,
    actor_id varchar(255) NOT NULL,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_audit_events_event_type ON audit_events (event_type);
CREATE INDEX IF NOT EXISTS ix_audit_events_aggregate_id ON audit_events (aggregate_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_created_at ON audit_events (created_at DESC);

COMMIT;
