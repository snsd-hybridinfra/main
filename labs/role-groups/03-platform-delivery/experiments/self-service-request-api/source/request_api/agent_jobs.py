from __future__ import annotations

import hashlib
import json
from typing import Any


IMAGE_REFERENCE = (
    "registry.invalid/mini-ona/agent@sha256:"
    "0000000000000000000000000000000000000000000000000000000000000000"
)
RUNTIME_CLASS = "kata-qemu-runtime-rs"
BROKER_PORT = 8443

SIZE_POLICIES: dict[str, dict[str, int | str]] = {
    "STANDARD": {
        "cpu": "2",
        "memory": "4Gi",
        "ephemeral_storage": "8Gi",
        "active_deadline_seconds": 900,
        "max_iterations": 5,
        "model_token_budget": 100_000,
        "monetary_budget_microunits": 2_000_000,
        "budget_currency": "USD",
        "external_call_budget": 25,
        "concurrency_limit": 1,
        "egress_byte_budget": 104_857_600,
    },
    "LARGE": {
        "cpu": "4",
        "memory": "8Gi",
        "ephemeral_storage": "16Gi",
        "active_deadline_seconds": 1800,
        "max_iterations": 10,
        "model_token_budget": 250_000,
        "monetary_budget_microunits": 5_000_000,
        "budget_currency": "USD",
        "external_call_budget": 50,
        "concurrency_limit": 1,
        "egress_byte_budget": 262_144_000,
    },
}

TRANSITIONS: dict[str, dict[str, str]] = {
    "RECEIVED": {"ENQUEUE": "QUEUED", "CANCEL": "CANCELLED"},
    "QUEUED": {"START": "STARTING", "CANCEL": "CANCELLED", "TIMEOUT": "TIMED_OUT"},
    "STARTING": {"POD_READY": "RUNNING", "FAIL": "FAILED", "CANCEL": "CANCELLED", "TIMEOUT": "TIMED_OUT"},
    "RUNNING": {"CHECKPOINT": "CHECKPOINTED", "COMPLETE": "COMPLETED", "FAIL": "FAILED", "CANCEL": "CANCELLED", "TIMEOUT": "TIMED_OUT"},
    "CHECKPOINTED": {"WAIT_FOR_APPROVAL": "AWAITING_APPROVAL", "RESUME": "RESUMING", "CANCEL": "CANCELLED", "TIMEOUT": "TIMED_OUT"},
    "AWAITING_APPROVAL": {"APPROVE": "RESUMING", "REJECT": "CANCELLED", "CANCEL": "CANCELLED", "TIMEOUT": "TIMED_OUT"},
    "RESUMING": {"POD_READY": "RUNNING", "FAIL": "FAILED", "CANCEL": "CANCELLED", "TIMEOUT": "TIMED_OUT"},
}
TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT", "BUDGET_EXHAUSTED"}
APPROVAL_ACTIONS = {
    "MAIN_BRANCH_MUTATION",
    "BRANCH_PROTECTION_BYPASS",
    "PRODUCTION_ACCESS",
    "DATABASE_SCHEMA_CHANGE",
    "SECRET_ACCESS",
    "NEW_EGRESS_DESTINATION",
    "INFRASTRUCTURE_MUTATION",
    "DEPENDENCY_SOURCE_CHANGE",
}


class AgentJobError(ValueError):
    pass


def canonical_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def build_sandbox_bundle(
    *,
    job_id: str,
    repository_alias: str,
    source_commit: str,
    task_digest: str,
    environment: str,
    size: str,
) -> tuple[dict[str, Any], str]:
    policy = SIZE_POLICIES.get(size)
    if policy is None:
        raise AgentJobError("unsupported sandbox size")
    namespace = f"agent-job-{hashlib.sha256(job_id.encode()).hexdigest()[:12]}"
    labels = {"platform.snsd/workload": "ai-agent-sandbox", "platform.snsd/job-id": job_id}
    resources = {
        "requests": {"cpu": policy["cpu"], "memory": policy["memory"], "ephemeral-storage": policy["ephemeral_storage"]},
        "limits": {"cpu": policy["cpu"], "memory": policy["memory"], "ephemeral-storage": policy["ephemeral_storage"]},
    }
    job = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": "agent-task",
            "namespace": namespace,
            "labels": labels,
            "annotations": {
                "platform.snsd/runtime-authorized": "false",
                "platform.snsd/spec-purpose": "LOCAL_VALIDATION_ONLY",
            },
        },
        "spec": {
            "backoffLimit": 0,
            "activeDeadlineSeconds": policy["active_deadline_seconds"],
            "ttlSecondsAfterFinished": 300,
            "template": {
                "metadata": {"labels": labels},
                "spec": {
                    "runtimeClassName": RUNTIME_CLASS,
                    "restartPolicy": "Never",
                    "automountServiceAccountToken": False,
                    "hostNetwork": False,
                    "hostPID": False,
                    "hostIPC": False,
                    "securityContext": {
                        "runAsNonRoot": True,
                        "runAsUser": 65532,
                        "runAsGroup": 65532,
                        "fsGroup": 65532,
                        "fsGroupChangePolicy": "OnRootMismatch",
                        "seccompProfile": {"type": "RuntimeDefault"},
                    },
                    "containers": [
                        {
                            "name": "agent",
                            "image": IMAGE_REFERENCE,
                            "args": ["serve-approved-task"],
                            "env": [
                                {"name": "JOB_ID", "value": job_id},
                                {"name": "REPOSITORY_ALIAS", "value": repository_alias},
                                {"name": "SOURCE_COMMIT", "value": source_commit},
                                {"name": "TASK_DIGEST", "value": task_digest},
                                {"name": "ENVIRONMENT", "value": environment},
                            ],
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "privileged": False,
                                "readOnlyRootFilesystem": True,
                                "runAsNonRoot": True,
                                "runAsUser": 65532,
                                "runAsGroup": 65532,
                                "capabilities": {"drop": ["ALL"]},
                            },
                            "resources": resources,
                            "volumeMounts": [
                                {"name": "workspace", "mountPath": "/workspace"},
                                {"name": "scratch", "mountPath": "/tmp"},
                            ],
                        }
                    ],
                    "volumes": [
                        {"name": "workspace", "emptyDir": {"sizeLimit": policy["ephemeral_storage"]}},
                        {"name": "scratch", "emptyDir": {"sizeLimit": "1Gi"}},
                    ],
                },
            },
        },
    }
    network_policy = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": "agent-default-deny-and-broker-only", "namespace": namespace},
        "spec": {
            "podSelector": {"matchLabels": labels},
            "policyTypes": ["Ingress", "Egress"],
            "ingress": [],
            "egress": [
                {
                    "to": [
                        {
                            "namespaceSelector": {"matchLabels": {"platform.snsd/egress-plane": "true"}},
                            "podSelector": {"matchLabels": {"platform.snsd/service": "authenticated-egress-broker"}},
                        }
                    ],
                    "ports": [{"protocol": "TCP", "port": BROKER_PORT}],
                },
                {
                    "to": [
                        {
                            "namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "kube-system"}},
                            "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}},
                        }
                    ],
                    "ports": [{"protocol": "UDP", "port": 53}, {"protocol": "TCP", "port": 53}],
                },
            ],
        },
    }
    quota = {
        "apiVersion": "v1",
        "kind": "ResourceQuota",
        "metadata": {"name": "agent-task-quota", "namespace": namespace},
        "spec": {"hard": {"pods": "1", "requests.cpu": policy["cpu"], "requests.memory": policy["memory"], "requests.ephemeral-storage": policy["ephemeral_storage"], "limits.cpu": policy["cpu"], "limits.memory": policy["memory"], "limits.ephemeral-storage": policy["ephemeral_storage"]}},
    }
    bundle = {
        "schema_version": "1.0.0",
        "runtime_authorized": False,
        "deployable": False,
        "namespace": namespace,
        "job": job,
        "network_policy": network_policy,
        "resource_quota": quota,
        "admission_requirements": {
            "runtime_class": RUNTIME_CLASS,
            "pid_limit": 256,
            "pid_limit_enforcement": "NODE_RUNTIME_OR_ADMISSION_POLICY_REQUIRED",
        },
        "budgets": {
            key: value
            for key, value in policy.items()
            if key not in {"cpu", "memory", "ephemeral_storage"}
        },
    }
    return bundle, canonical_digest(bundle)


def transition_target(current: str, action: str, *, checkpoint_digest: str | None, approval_action: str | None) -> str:
    target = TRANSITIONS.get(current, {}).get(action)
    if target is None:
        raise AgentJobError(f"invalid agent job transition: {current} -> {action}")
    if action == "CHECKPOINT" and not checkpoint_digest:
        raise AgentJobError("checkpoint transition requires a checkpoint digest")
    if action != "CHECKPOINT" and checkpoint_digest is not None:
        raise AgentJobError("checkpoint digest is valid only for a checkpoint transition")
    if action == "WAIT_FOR_APPROVAL" and approval_action not in APPROVAL_ACTIONS:
        raise AgentJobError("approval wait requires an approved high-risk action identifier")
    if action != "WAIT_FOR_APPROVAL" and approval_action is not None:
        raise AgentJobError("approval action is valid only when entering approval wait")
    return target


def compute_is_allocated(status: str) -> bool:
    return status in {"STARTING", "RUNNING", "RESUMING"}
