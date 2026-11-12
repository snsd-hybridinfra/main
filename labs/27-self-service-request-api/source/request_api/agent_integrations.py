from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from .agent_jobs import canonical_digest


QUEUE_TRANSPORT_CONTRACT = "REDIS_STREAMS_XADD_XREADGROUP"
LOCAL_QUEUE_ADAPTER = "DATABASE_OUTBOX"
LEASE_TTL_SECONDS = 900
CREDENTIAL_CLASSES = ("GITHUB_APP", "MODEL_BROKER")
EGRESS_RULES: dict[str, tuple[str, int]] = {
    "GITHUB_SERVICE": ("HTTPS", 443),
    "MODEL_BROKER": ("HTTPS", 443),
    "APPROVED_PACKAGE_MIRROR": ("HTTPS", 443),
    "PLATFORM_TELEMETRY": ("OTLP_GRPC", 4317),
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def build_queue_envelope(job: Any) -> tuple[dict[str, Any], str]:
    envelope = {
        "schema_version": "1.0.0",
        "transport_contract": QUEUE_TRANSPORT_CONTRACT,
        "local_adapter": LOCAL_QUEUE_ADAPTER,
        "job_id": job.job_id,
        "sandbox_spec_digest": job.sandbox_spec_digest,
        "repository_alias": job.repository_alias,
        "source_commit": job.source_commit,
        "task_digest": job.task_digest,
        "environment": job.environment,
        "size": job.size,
        "runtime_authorized": False,
    }
    return envelope, canonical_digest(envelope)


def build_egress_policy(job_id: str) -> tuple[dict[str, Any], str]:
    policy = {
        "schema_version": "1.0.0",
        "job_id": job_id,
        "broker_required": True,
        "direct_network_allowed": False,
        "raw_ip_allowed": False,
        "alternate_dns_allowed": False,
        "rules": [
            {"destination_class": destination, "protocol": protocol, "port": port}
            for destination, (protocol, port) in EGRESS_RULES.items()
        ],
        "runtime_authorized": False,
    }
    return policy, canonical_digest(policy)


def decide_egress(
    *,
    destination_class: str,
    protocol: str,
    port: int,
    via_authenticated_broker: bool,
    raw_ip: bool = False,
) -> str:
    expected = EGRESS_RULES.get(destination_class)
    if raw_ip or not via_authenticated_broker or expected != (protocol, port):
        return "DENY"
    return "ALLOW_BROKERED"


def new_lease_metadata(job_id: str, credential_class: str, event_version: int) -> dict[str, Any]:
    if credential_class not in CREDENTIAL_CLASSES:
        raise ValueError("unsupported credential class")
    issued_at = utcnow()
    lease_id = str(uuid4())
    return {
        "lease_id": lease_id,
        "job_id": job_id,
        "credential_class": credential_class,
        "lease_reference": f"local-invalid://credential-lease/{lease_id}",
        "status": "ACTIVE",
        "issued_for_event_version": event_version,
        "issued_at": issued_at,
        "expires_at": issued_at + timedelta(seconds=LEASE_TTL_SECONDS),
    }
