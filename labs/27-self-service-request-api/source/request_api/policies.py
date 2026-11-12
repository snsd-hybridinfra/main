from __future__ import annotations

import re
from typing import Any


PROJECT = {
    "key": "project_name",
    "label": "프로젝트명",
    "type": "text",
    "default": "payment-api-test",
    "required": True,
    "help": "영문 소문자, 숫자, 하이픈만 사용합니다.",
}

COMPUTE_PURPOSE = {
    "key": "workload_purpose",
    "label": "워크로드 용도",
    "type": "select",
    "default": "saas-application-development",
    "required": True,
    "options": [
        {"value": "saas-application-development", "label": "SaaS 애플리케이션 개발"},
        {"value": "backend-integration-test", "label": "백엔드 통합 테스트"},
        {"value": "security-validation", "label": "보안 검증"},
    ],
}

KUBERNETES_PURPOSE = {
    "key": "workload_purpose",
    "label": "PaaS 용도",
    "type": "select",
    "default": "saas-deployment-test",
    "required": True,
    "options": [
        {"value": "saas-deployment-test", "label": "SaaS 배포 테스트"},
        {"value": "microservice-container-lab", "label": "마이크로서비스 컨테이너 실습"},
        {"value": "cicd-integration-test", "label": "CI/CD 연동 테스트"},
    ],
}

PRODUCT_PARAMETERS: dict[str, tuple[dict[str, Any], ...]] = {
    "DEV-OS-VM-S": (PROJECT, COMPUTE_PURPOSE),
    "DEV-OS-VM-M": (PROJECT, COMPUTE_PURPOSE),
    "DEV-OS-VM-L": (PROJECT, COMPUTE_PURPOSE),
    "DEV-OS-K3S-S": (PROJECT, KUBERNETES_PURPOSE),
    "DEV-OS-K3S-M": (PROJECT, KUBERNETES_PURPOSE),
}


def normalize_parameters(product_code: str, raw: dict[str, Any] | None) -> dict[str, str | int]:
    specs = PRODUCT_PARAMETERS.get(product_code)
    if specs is None:
        raise ValueError("unknown product_code")
    supplied = raw or {}
    allowed = {str(spec["key"]) for spec in specs}
    if set(supplied) - allowed:
        raise ValueError("unsupported product parameter")

    normalized: dict[str, str | int] = {}
    for spec in specs:
        key = str(spec["key"])
        text = str(supplied.get(key, spec.get("default")) or "").strip()
        if spec.get("required") and not text:
            raise ValueError(f"{key} is required")
        options = {str(option["value"]) for option in spec.get("options", [])}
        if options and text not in options:
            raise ValueError(f"{key} is not an allowed option")
        if key == "project_name" and not re.fullmatch(r"[a-z][a-z0-9-]{2,39}", text):
            raise ValueError("project_name must use lowercase letters, numbers, or hyphens")
        normalized[key] = text
    return normalized
