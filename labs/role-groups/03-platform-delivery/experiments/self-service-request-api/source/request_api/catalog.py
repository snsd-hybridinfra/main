from __future__ import annotations

from typing import Any

from .policies import PRODUCT_PARAMETERS


DURATION_HOURS = [4, 8, 24, 72, 168]

ARTIFACT_DIGESTS = {
    "DEV-OS-VM-S": "sha256:97f4ece588f80e2ea24524e07d5662c5d6d93b78bcccf75bb935fad99ae090f0",
    "DEV-OS-VM-M": "sha256:624d5ff0d50bfc97c733a48b78d2d4e4f3cdf4633898a1b5e52ad4003f28a10a",
    "DEV-OS-VM-L": "sha256:b09a0e5e839100bfb09e09469738eca9195418bf2e93153e5f03bcc21db2deae",
    "DEV-OS-K3S-S": "sha256:fa1542d73dd9f6c3e7981bd9fe6d0c18564180055f7890ed98aa6575e3286960",
    "DEV-OS-K3S-M": "sha256:12867fb8f7fef31fe34d63305b13555fb1ef3fd37ea789daa6e67b9a4ba5b03a",
}
K3S_CONFIGURATION_DIGEST = (
    "sha256:27ae92895d90f49a118c2fa5db7e897173e15fa002796090765872769c4a6e18"
)

PRODUCT_RUNTIME_SPECS = {
    "DEV-OS-VM-S": {"cpu": 2, "memory_gib": 2, "storage_gib": 30},
    "DEV-OS-VM-M": {"cpu": 2, "memory_gib": 4, "storage_gib": 50},
    "DEV-OS-VM-L": {"cpu": 2, "memory_gib": 8, "storage_gib": 80},
    "DEV-OS-K3S-S": {"cpu": 2, "memory_gib": 4, "storage_gib": 40},
    "DEV-OS-K3S-M": {"cpu": 2, "memory_gib": 8, "storage_gib": 80},
}


def _product(
    code: str,
    *,
    name: str,
    description: str,
    module_name: str,
    size: str,
    primary: bool = False,
) -> dict[str, Any]:
    runtime = PRODUCT_RUNTIME_SPECS[code]
    return {
        "product_code": code,
        "product_version": 1,
        "name": name,
        "description": description,
        "mvp_primary": primary,
        "requires_compute_spec": False,
        "category": "COMPUTE",
        "provisioner": "terraform",
        "module_name": module_name,
        "module_version": "1.0.0",
        "artifact_digest": ARTIFACT_DIGESTS[code],
        "allowed_duration_hours": list(DURATION_HOURS),
        "max_resources_per_user": 1,
        "fixed_spec": {
            "클라우드": "OpenStack Nova",
            "운영체제": "운영자 승인 Glance 기본 이미지",
            "사양": f"운영자 승인 {size} flavor / {runtime['cpu']} vCPU / {runtime['memory_gib']} GiB",
            "루트 디스크": f"Nova flavor 로컬 디스크, 최소 {runtime['storage_gib']} GiB",
            "네트워크": "기존 Private Neutron network / Floating IP 없음",
            "보안": "기존 승인 Security Group / Port Security 활성화",
            "접근": "Zero Trust PEP 경로만 허용",
        },
        "parameters": list(PRODUCT_PARAMETERS[code]),
    }


def _k3s_product(
    code: str,
    *,
    name: str,
    description: str,
    module_name: str,
    size: str,
    memory_gib: int,
    storage_gib: int,
    primary: bool = False,
) -> dict[str, Any]:
    return {
        **_product(
            code,
            name=name,
            description=description,
            module_name=module_name,
            size=size,
            primary=primary,
        ),
        "configuration_digest": K3S_CONFIGURATION_DIGEST,
        "category": "PAAS",
        "fixed_spec": {
            "클라우드": "OpenStack Nova + Neutron",
            "플랫폼": "운영자 승인 기본 Glance 이미지 + Ansible 오프라인 k3s 구성",
            "사양": f"운영자 승인 {size} flavor / 2 vCPU / {memory_gib} GiB",
            "루트 디스크": f"Nova flavor 로컬 디스크, 최소 {storage_gib} GiB",
            "네트워크": "Private Kubernetes API / Floating IP 없음",
            "기본 구성": "CoreDNS / metrics-server / local-path-provisioner",
            "기본 정책": "dev namespace / ResourceQuota / LimitRange / default-deny",
            "접근": "Zero Trust PEP와 검증된 Grant 경로만 허용",
        },
        "parameters": list(PRODUCT_PARAMETERS[code]),
    }


CATALOG: tuple[dict[str, Any], ...] = (
    _product(
        "DEV-OS-VM-S",
        name="OpenStack 개발 VM Small",
        description="소규모 개발과 제한된 보안 검증을 위한 private Nova VM 1대입니다.",
        module_name="openstack-dev-vm-small",
        size="small",
        primary=True,
    ),
    _product(
        "DEV-OS-VM-M",
        name="OpenStack 개발 VM Medium",
        description="백엔드 통합 테스트를 위한 private Nova VM 1대입니다.",
        module_name="openstack-dev-vm-medium",
        size="medium",
    ),
    _product(
        "DEV-OS-VM-L",
        name="OpenStack 개발 VM Large",
        description="높은 메모리가 필요한 제한된 개발 검증용 private Nova VM 1대입니다.",
        module_name="openstack-dev-vm-large",
        size="large",
    ),
    _k3s_product(
        "DEV-OS-K3S-S",
        name="OpenStack k3s PaaS Small",
        description="Terraform과 Ansible로 자동 구성하는 private 단일 노드 개발 PaaS입니다.",
        module_name="openstack-dev-k3s-small",
        size="medium",
        memory_gib=4,
        storage_gib=40,
        primary=True,
    ),
    _k3s_product(
        "DEV-OS-K3S-M",
        name="OpenStack k3s PaaS Medium",
        description="통합 배포 검증용 private 단일 노드 k3s PaaS입니다.",
        module_name="openstack-dev-k3s-medium",
        size="large",
        memory_gib=8,
        storage_gib=80,
    ),
)

CATALOG_BY_CODE = {item["product_code"]: item for item in CATALOG}
