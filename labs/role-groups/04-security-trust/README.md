# Security, Identity & Zero Trust

정책 적용 전에 주체, 역할 신뢰, 세션 권한과 명시적 거부를 확인합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 04-security-trust
```

IAM/STS 실험의 합성 IAM/STS 정책에서 신뢰 관계, 세션 범위, 허용·거부 사례 7개를 검증합니다. `iam.json`에서 어떤 조건이 각 판정에 사용됐는지 확인합니다.

실습 범위는 로컬 정책 판정입니다. 클러스터 권한과 단말 신뢰는 아래 자료를 사용합니다.

## 실험

| 실험 | 검증 기록 |
|---|---|
| [IAM / STS: 탈취된 역할의 행동 범위 줄이기](experiments/iam-sts/README.md) | 기존 로컬 검증 기록 |
| [AAA / RADIUS: 승인·거부 정책 확인](experiments/aaa-radius/README.md) | 기존 로컬 검증 기록 |
| [Kubernetes ServiceAccount 최소 권한 Lab](experiments/kubernetes-rbac/README.md) | 기존 로컬 검증 기록 |

<details>
<summary>다른 실험 보기</summary>

| 실험 | 검증 기록 |
|---|---|
| [AI Agent Security: 서명된 실행 범위와 도구 호출 경계](experiments/ai-agent-security/README.md) | 기존 로컬 검증 기록 |
| [Infrastructure Vulnerability Prioritization](experiments/vulnerability-prioritization/README.md) | 기존 로컬 검증 기록 |
| [Zero Trust Security Control Baselines](experiments/security-baselines/README.md) | 이관 자료 · 개별 재검증 전 |
| [Identity & Device Assurance Controls](experiments/identity-device-assurance/README.md) | 이관 자료 · 개별 재검증 전 |
| [Zero Trust Package Contracts & Rollback Criteria](experiments/zero-trust-package-contracts/README.md) | 이관 자료 · 개별 재검증 전 |
| [Zero Trust Target Architecture and Acceptance Maps](experiments/zero-trust-target-architecture/README.md) | 이관 자료 · 개별 재검증 전 |

</details>

[전체 랩](../README.md) · [공통 실행 기록](../evidence/2026-11-12.json)
