BEGIN;

CREATE SCHEMA IF NOT EXISTS request_service AUTHORIZATION request_migrator;
SET LOCAL search_path = request_service, pg_catalog;

CREATE TABLE IF NOT EXISTS access_requests (
    request_id varchar(36) PRIMARY KEY,
    idempotency_key varchar(128) NOT NULL UNIQUE,
    owner_id varchar(255) NOT NULL,
    product_code varchar(64) NOT NULL,
    cpu integer NOT NULL CHECK (cpu BETWEEN 0 AND 64),
    memory_gib integer NOT NULL CHECK (memory_gib BETWEEN 0 AND 512),
    storage_gib integer NOT NULL CHECK (storage_gib BETWEEN 0 AND 4096),
    duration_hours integer NOT NULL CHECK (duration_hours BETWEEN 1 AND 2160),
    purpose text NOT NULL CHECK (char_length(purpose) BETWEEN 5 AND 2000),
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(parameters) = 'object'),
    status varchar(32) NOT NULL CHECK (status IN (
        'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'GRANTED',
        'REVOKED', 'EXPIRED', 'PROVISIONING', 'RUNNING', 'TERMINATING',
        'TERMINATED', 'PROVISION_FAILED', 'TERMINATION_FAILED'
    )),
    rejection_reason text,
    grant_id varchar(36),
    grant_expires_at timestamptz,
    resource_id varchar(36),
    resource_status varchar(32),
    event_version integer NOT NULL DEFAULT 1 CHECK (event_version >= 1),
    retry_count integer NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    delivery_status varchar(16) NOT NULL DEFAULT 'PENDING' CHECK (delivery_status IN ('PENDING', 'DELIVERED', 'FAILED', 'SKIPPED')),
    last_error text,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_access_requests_owner_id ON access_requests (owner_id);
CREATE INDEX IF NOT EXISTS ix_access_requests_status ON access_requests (status);
CREATE INDEX IF NOT EXISTS ix_access_requests_grant_id ON access_requests (grant_id);
CREATE INDEX IF NOT EXISTS ix_access_requests_resource_id ON access_requests (resource_id);

CREATE TABLE IF NOT EXISTS resource_projections (
    resource_id varchar(36) PRIMARY KEY,
    request_id varchar(36) NOT NULL UNIQUE REFERENCES access_requests(request_id) ON DELETE CASCADE,
    owner_id varchar(255) NOT NULL,
    status varchar(32) NOT NULL,
    endpoint varchar(512),
    resource_type varchar(64) NOT NULL DEFAULT 'DEV-OS-VM-S',
    display_name varchar(255) NOT NULL DEFAULT '할당 자원',
    details jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(details) = 'object'),
    event_version integer NOT NULL CHECK (event_version >= 1),
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_resource_projections_owner_id ON resource_projections (owner_id);

CREATE TABLE IF NOT EXISTS portal_usage (
    usage_id varchar(36) PRIMARY KEY,
    idempotency_key varchar(64) NOT NULL UNIQUE,
    tenant_id varchar(128) NOT NULL,
    owner_id varchar(255) NOT NULL,
    model varchar(64) NOT NULL,
    input_units integer NOT NULL,
    output_units integer NOT NULL,
    created_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_portal_usage_tenant_id ON portal_usage (tenant_id);
CREATE INDEX IF NOT EXISTS ix_portal_usage_owner_id ON portal_usage (owner_id);

COMMIT;
