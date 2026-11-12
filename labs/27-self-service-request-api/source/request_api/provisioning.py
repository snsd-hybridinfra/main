from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .policies import normalize_parameters


PRODUCT_LABELS = {
    "DEV-OS-VM-S": "OpenStack 개발 VM Small",
    "DEV-OS-VM-M": "OpenStack 개발 VM Medium",
    "DEV-OS-VM-L": "OpenStack 개발 VM Large",
    "DEV-OS-K3S-S": "OpenStack k3s PaaS Small",
    "DEV-OS-K3S-M": "OpenStack k3s PaaS Medium",
}


@dataclass(frozen=True, slots=True)
class MockResourceSpec:
    resource_id: str
    resource_type: str
    display_name: str
    endpoint: str
    details: dict[str, str | int | bool]


def _mock_ip(request_id: str) -> str:
    compact = request_id.replace("-", "")
    value = sum(ord(character) for character in compact) % 240 + 10
    return f"10.250.1.{value}"


def build_mock_resource(item: Any) -> MockResourceSpec:
    suffix = item.request_id.replace("-", "")[:8].upper()
    parameters = normalize_parameters(item.product_code, dict(item.parameters or {}))
    project = str(parameters["project_name"])
    paas_products = {
        "DEV-OS-K3S-S": ("Small", "2 vCPU / 4 GiB / 40 GiB"),
        "DEV-OS-K3S-M": ("Medium", "2 vCPU / 8 GiB / 80 GiB"),
    }
    if item.product_code in paas_products:
        size, spec = paas_products[item.product_code]
        return MockResourceSpec(
            resource_id=f"DEMO-OS-K3S-{suffix}",
            resource_type=item.product_code,
            display_name=f"{project} / OpenStack k3s PaaS {size}",
            endpoint=f"https://{_mock_ip(item.request_id)}:6443",
            details={
                "project_name": project,
                "cloud": "OpenStack",
                "topology": "single-node",
                "spec": spec,
                "default_namespace": "dev",
                "bootstrap_status": "READY",
                "network_exposure": "PRIVATE_ONLY",
                "floating_ip": False,
                "monitoring_status": "NOT_ONBOARDED",
                "provisioner": "Mock Terraform Runner",
            },
        )

    products = {
        "DEV-OS-VM-S": ("Small", "2 vCPU / 2 GiB / 30 GiB"),
        "DEV-OS-VM-M": ("Medium", "2 vCPU / 4 GiB / 50 GiB"),
        "DEV-OS-VM-L": ("Large", "2 vCPU / 8 GiB / 80 GiB"),
    }
    try:
        size, spec = products[item.product_code]
    except KeyError as exc:
        raise ValueError("unsupported mock product") from exc
    return MockResourceSpec(
        resource_id=f"DEMO-OS-VM-{suffix}",
        resource_type=item.product_code,
        display_name=f"{project} / OpenStack 개발 VM {size}",
        endpoint=_mock_ip(item.request_id),
        details={
            "project_name": project,
            "cloud": "OpenStack",
            "spec": spec,
            "network_exposure": "PRIVATE_ONLY",
            "floating_ip": False,
            "monitoring_status": "NOT_ONBOARDED",
            "provisioner": "Mock Terraform Runner",
        },
    )


def product_label(product_code: str) -> str:
    return PRODUCT_LABELS.get(product_code, product_code)
