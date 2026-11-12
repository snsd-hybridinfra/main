from __future__ import annotations

import copy
import re
from typing import Any

from .blueprints import canonical_manifest_digest, load_authorities


BLUEPRINT_ID = "API_DEVELOPMENT_STACK"
NETWORK_PROFILE = "PRIVATE_SAAS_INGRESS"
EXPECTED_COMPONENT_ORDER = [
    "K3S_RUNTIME",
    "APPLICATION_RUNTIME",
    "POSTGRESQL",
    "CACHE",
    "MESSAGE_QUEUE",
    "OBJECT_STORAGE",
    "NAS_FILE_EXCHANGE",
    "LOAD_BALANCER",
    "NETWORK_POLICY",
    "OPERATIONS_PROFILE",
]
EXPECTED_RUNTIME_GATES = [
    "K3S_TENANT_BASELINE",
    "APPROVED_INTERNAL_REGISTRY",
    "OIDC_AND_RBAC",
    "EXTERNAL_SECRET_MANAGER",
    "POSTGRESQL_ADAPTER",
    "REDIS_ADAPTER",
    "MESSAGE_QUEUE_ADAPTER",
    "OBJECT_STORAGE_ADAPTER",
    "NAS_FILE_EXCHANGE_ADAPTER",
    "PRIVATE_INGRESS_ADAPTER",
    "OTEL_PIPELINE",
]
SIZE_LIMITS = {
    "SMALL": {
        "requests.cpu": "1",
        "requests.memory": "2Gi",
        "limits.cpu": "2",
        "limits.memory": "4Gi",
        "pods": "12",
        "services": "8",
        "persistentvolumeclaims": "4",
    },
    "STANDARD": {
        "requests.cpu": "2",
        "requests.memory": "4Gi",
        "limits.cpu": "4",
        "limits.memory": "8Gi",
        "pods": "24",
        "services": "12",
        "persistentvolumeclaims": "8",
    },
}


class FinancialSaaSBundleError(ValueError):
    pass


def _verify_resolution(resolution: dict[str, Any]) -> None:
    expected_keys = {
        "schema_version",
        "blueprint_id",
        "environment",
        "size",
        "duration_hours",
        "purpose",
        "business_domain_profiles",
        "network_profile",
        "component_plan",
        "selected_execution_profile",
        "deployment_transaction",
        "rollback_component_order",
        "resolution_status",
        "blocking_components",
        "blocking_gates",
        "runtime_authorized",
        "manifest_digest",
    }
    if set(resolution) != expected_keys:
        raise FinancialSaaSBundleError("resolution fields differ from the canonical contract")
    source = copy.deepcopy(resolution)
    supplied_digest = source.pop("manifest_digest", None)
    if canonical_manifest_digest(source) != supplied_digest:
        raise FinancialSaaSBundleError("resolution manifest digest mismatch")
    if resolution.get("blueprint_id") != BLUEPRINT_ID:
        raise FinancialSaaSBundleError("resolution is not the financial SaaS PaaS blueprint")
    catalog, _ = load_authorities()
    approved = next(item for item in catalog["blueprints"] if item["blueprint_id"] == BLUEPRINT_ID)
    if resolution.get("business_domain_profiles") != approved.get("business_domain_profiles", []):
        raise FinancialSaaSBundleError("financial SaaS PaaS business domain profiles mismatch")
    if resolution.get("environment") not in {"DEV", "TEST", "STG"}:
        raise FinancialSaaSBundleError("financial SaaS PaaS is non-production only")
    if resolution.get("size") not in SIZE_LIMITS:
        raise FinancialSaaSBundleError("financial SaaS PaaS size is not approved")
    if resolution.get("network_profile") != NETWORK_PROFILE:
        raise FinancialSaaSBundleError("financial SaaS PaaS network profile mismatch")
    component_ids = [item.get("component_id") for item in resolution.get("component_plan", [])]
    if component_ids != EXPECTED_COMPONENT_ORDER:
        raise FinancialSaaSBundleError("financial SaaS PaaS component plan mismatch")
    if resolution.get("rollback_component_order") != list(reversed(EXPECTED_COMPONENT_ORDER)):
        raise FinancialSaaSBundleError("financial SaaS PaaS rollback order mismatch")
    if resolution.get("blocking_gates") != EXPECTED_RUNTIME_GATES:
        raise FinancialSaaSBundleError("financial SaaS PaaS runtime gates mismatch")
    if resolution.get("runtime_authorized") is not False:
        raise FinancialSaaSBundleError("source resolution must remain runtime unauthorized")


def _network_policy(name: str, namespace: str, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": name, "namespace": namespace},
        "spec": spec,
    }


def build_financial_saas_tenant_bundle(
    resolution: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """Build an inert, deterministic k3s tenant baseline from an approved resolution."""

    _verify_resolution(resolution)
    digest_suffix = resolution["manifest_digest"].split(":", 1)[1][:12]
    namespace = f"saas-{resolution['environment'].lower()}-{digest_suffix}"
    if not re.fullmatch(r"saas-(dev|test|stg)-[0-9a-f]{12}", namespace):
        raise FinancialSaaSBundleError("derived tenant namespace is invalid")

    common_labels = {
        "platform.snsd/product": "financial-saas-development-paas",
        "platform.snsd/environment": resolution["environment"].lower(),
        "platform.snsd/resolution": digest_suffix,
    }
    objects: list[dict[str, Any]] = [
        {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace,
                "labels": {
                    **common_labels,
                    "pod-security.kubernetes.io/enforce": "restricted",
                    "pod-security.kubernetes.io/enforce-version": "v1.36",
                    "pod-security.kubernetes.io/audit": "restricted",
                    "pod-security.kubernetes.io/warn": "restricted",
                },
            },
        },
        {
            "apiVersion": "v1",
            "kind": "ResourceQuota",
            "metadata": {"name": "tenant-quota", "namespace": namespace},
            "spec": {"hard": SIZE_LIMITS[resolution["size"]]},
        },
        {
            "apiVersion": "v1",
            "kind": "LimitRange",
            "metadata": {"name": "container-defaults", "namespace": namespace},
            "spec": {
                "limits": [
                    {
                        "type": "Container",
                        "defaultRequest": {"cpu": "100m", "memory": "128Mi"},
                        "default": {"cpu": "500m", "memory": "512Mi"},
                    }
                ]
            },
        },
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": "application-runtime", "namespace": namespace},
            "automountServiceAccountToken": False,
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {"name": "tenant-observer", "namespace": namespace},
            "rules": [
                {
                    "apiGroups": [""],
                    "resources": ["pods", "services", "configmaps"],
                    "verbs": ["get", "list", "watch"],
                },
                {
                    "apiGroups": ["apps"],
                    "resources": ["deployments", "replicasets"],
                    "verbs": ["get", "list", "watch"],
                },
            ],
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {"name": "tenant-observers", "namespace": namespace},
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "Role",
                "name": "tenant-observer",
            },
            "subjects": [
                {
                    "apiGroup": "rbac.authorization.k8s.io",
                    "kind": "Group",
                    "name": f"idp:financial-saas:{resolution['environment'].lower()}:observers",
                }
            ],
        },
        _network_policy(
            "default-deny",
            namespace,
            {"podSelector": {}, "policyTypes": ["Ingress", "Egress"]},
        ),
        _network_policy(
            "allow-cluster-dns",
            namespace,
            {
                "podSelector": {},
                "policyTypes": ["Egress"],
                "egress": [
                    {
                        "to": [
                            {
                                "namespaceSelector": {
                                    "matchLabels": {"kubernetes.io/metadata.name": "kube-system"}
                                },
                                "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}},
                            }
                        ],
                        "ports": [
                            {"protocol": "UDP", "port": 53},
                            {"protocol": "TCP", "port": 53},
                        ],
                    }
                ],
            },
        ),
        _network_policy(
            "allow-private-ingress",
            namespace,
            {
                "podSelector": {"matchLabels": {"platform.snsd/tier": "application"}},
                "policyTypes": ["Ingress"],
                "ingress": [
                    {
                        "from": [
                            {
                                "namespaceSelector": {
                                    "matchLabels": {"platform.snsd/plane": "private-ingress"}
                                }
                            }
                        ],
                        "ports": [{"protocol": "TCP", "port": 8080}],
                    }
                ],
            },
        ),
        _network_policy(
            "allow-approved-data-services",
            namespace,
            {
                "podSelector": {"matchLabels": {"platform.snsd/tier": "application"}},
                "policyTypes": ["Egress"],
                "egress": [
                    {
                        "to": [
                            {
                                "namespaceSelector": {
                                    "matchLabels": {"platform.snsd/plane": "data-services"}
                                },
                                "podSelector": {
                                    "matchExpressions": [
                                        {
                                            "key": "platform.snsd/service-class",
                                            "operator": "In",
                                            "values": [
                                                "postgresql",
                                                "redis",
                                                "message-queue",
                                                "object-storage",
                                            ],
                                        }
                                    ]
                                },
                            }
                        ],
                        "ports": [
                            {"protocol": "TCP", "port": 5432},
                            {"protocol": "TCP", "port": 6379},
                            {"protocol": "TCP", "port": 5672},
                            {"protocol": "TCP", "port": 9000},
                        ],
                    }
                ],
            },
        ),
    ]
    bundle = {
        "schema_version": "1.0.0",
        "bundle_type": "FINANCIAL_SAAS_TENANT_BASELINE",
        "source_manifest_digest": resolution["manifest_digest"],
        "blueprint_id": BLUEPRINT_ID,
        "environment": resolution["environment"],
        "size": resolution["size"],
        "duration_hours": resolution["duration_hours"],
        "namespace": namespace,
        "objects": objects,
        "adapter_bindings": {
            "application_image": "APPROVED_INTERNAL_REGISTRY_DIGEST_REQUIRED",
            "identity": "OIDC_GROUP_BINDING_REQUIRED",
            "secrets": "EXTERNAL_SECRET_REFERENCES_ONLY",
            "postgresql": "POSTGRESQL_ADAPTER_REQUIRED",
            "cache": "REDIS_ADAPTER_REQUIRED",
            "message_queue": "MESSAGE_QUEUE_ADAPTER_REQUIRED",
            "object_storage": "OBJECT_STORAGE_ADAPTER_REQUIRED",
            "ingress": "PRIVATE_INGRESS_ADAPTER_REQUIRED",
            "telemetry": "OTEL_PIPELINE_REQUIRED",
        },
        "apply_order": [f"{item['kind']}/{item['metadata']['name']}" for item in objects],
        "rollback_order": [
            f"{item['kind']}/{item['metadata']['name']}" for item in reversed(objects)
        ],
        "deployment_transaction": "ALL_OR_NOTHING",
        "runtime_authorized": False,
        "deployable": False,
    }
    return bundle, canonical_manifest_digest(bundle)
