from __future__ import annotations

from typing import Any


def scopes_for_product(product_code: str, parameters: dict[str, Any]) -> list[str]:
    if product_code in {"DEV-OS-VM-S", "DEV-OS-VM-M", "DEV-OS-VM-L"}:
        return ["openstack:vm:access"]
    if product_code in {"DEV-OS-K3S-S", "DEV-OS-K3S-M"}:
        return ["openstack:k3s:admin"]
    raise ValueError("unsupported product policy")
