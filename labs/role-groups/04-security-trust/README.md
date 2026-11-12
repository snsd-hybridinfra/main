# Security, Identity & Zero Trust

정책 적용 전에 주체, 역할 신뢰, 세션 권한과 명시적 거부를 확인합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 04-security-trust
```

Lab 04의 합성 IAM/STS 정책에서 신뢰 관계, 세션 범위, 허용·거부 사례 7개를 검증합니다. `iam.json`에서 어떤 조건이 각 판정에 사용됐는지 확인합니다.

실습 범위는 로컬 정책 판정입니다. 클러스터 권한과 단말 신뢰는 아래 자료를 사용합니다.

## 번호 랩

| ID | 실습과 자료 | 번호 랩의 기록 |
|---|---|---|
| 04 | [04-iam-sts](../../04-iam-sts/README.md) | 기존 로컬 증적 |
| 06 | [06-aaa-radius](../../06-aaa-radius/README.md) | 기존 로컬 증적 |
| 07 | [07-ai-agent-security](../../07-ai-agent-security/README.md) | 기존 로컬 증적 |
| 11 | [11-vulnerability-prioritization](../../11-vulnerability-prioritization/README.md) | 기존 로컬 증적 |
| 13 | [13-kubernetes-rbac](../../13-kubernetes-rbac/README.md) | 기존 로컬 증적 |
| 32 | [32-security-baselines](../../32-security-baselines/README.md) | 이관 참고 |
| 38 | [38-identity-device-assurance](../../38-identity-device-assurance/README.md) | 이관 참고 |
| 40 | [40-zero-trust-package-contracts](../../40-zero-trust-package-contracts/README.md) | 이관 참고 |
| 46 | [46-zero-trust-target-architecture](../../46-zero-trust-target-architecture/README.md) | 이관 참고 |

[역할 랩 인덱스](../README.md) · [대표 사례 검증 결과](../evidence/2026-11-12.json)
