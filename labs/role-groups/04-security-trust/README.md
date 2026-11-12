# Security, Identity & Zero Trust

**Primary role group** `04-security-trust` · **이관 자료는 런타임 재검증 전**

이 역할군은 하나의 *운영 책임 경계*와 **재현 가능한 통합 검증 흐름**을 제공해. 원본 개별 랩은 유일한 소스의 진실이며 이 인덱스는 코드 복제/성공 상태 승격이 아님.

## 운영 목적
자산·사용자·워크로드 식별부터 정책 집행과 증적 유효성까지 검증

## 단일 실습 흐름
IAM/STS(04), AAA/RADIUS(06), Identity/Device(38) → Kubernetes RBAC(13) → Security Baselines(32) → Zero Trust package/traceability(40,46) → Agent Security(07)·Vulnerability Priority(11)

## 소속 랩

| ID | 랩 (canonical) | 현재 출처 기반 상태 |
|---|---|---|
| 04 | [04-iam-sts](../../04-iam-sts/README.md) | 기존 로컬 검증 기록 |
| 06 | [06-aaa-radius](../../06-aaa-radius/README.md) | 기존 로컬 검증 기록 |
| 07 | [07-ai-agent-security](../../07-ai-agent-security/README.md) | 기존 로컬 검증 기록 |
| 11 | [11-vulnerability-prioritization](../../11-vulnerability-prioritization/README.md) | 기존 로컬 검증 기록 |
| 13 | [13-kubernetes-rbac](../../13-kubernetes-rbac/README.md) | 기존 로컬 검증 기록 |
| 32 | [32-security-baselines](../../32-security-baselines/README.md) | 이관·재검증 대기 |
| 38 | [38-identity-device-assurance](../../38-identity-device-assurance/README.md) | 이관·재검증 대기 |
| 40 | [40-zero-trust-package-contracts](../../40-zero-trust-package-contracts/README.md) | 이관·재검증 대기 |
| 46 | [46-zero-trust-target-architecture](../../46-zero-trust-target-architecture/README.md) | 이관·재검증 대기 |

## 통합 대상, 중복 기능 정리
- 04+06+38: 계정·인증 강도·단말 신뢰·권한의 공통 주체 모델
- 13+32+40+46: 정책 기대 결과와 실제 차단 증적을 분리해 매핑

## 역할군 공통 인터페이스

- **Input:** fake principal, role, device posture, data class, control requirement
- **Output:** allow/deny decisions, policy provenance, expiry and exception record
- **Mandatory gate:** 권한 우회, MFA 누락, 단말 미신뢰, 과도한 RBAC, 민감정보 탈출, 증적 부재

개별 랩에서 입력·출력 형식을 먼저 고정한 뒤 기능을 연결해. 기존 성공/실패 증적은 해당 랩에 유지하고, 통합 흐름의 결과는 **새로운 증적**을 따로 남겨야 해. 읽기 전용 관측과 변경·배포·삭제 코드는 같은 권한으로 실행하지 않음.

## 다음 조합 단계
1. 모든 랩의 의존성/하드코딩 경로를 해소하고 합성 데이터를 표준화한다.
2. 최소 단위 정상/거부/장애/복구 검증 후 통합 대상으로 승격한다.
3. 공통 인터페이스에 맞춰 각 랩을 조합하고 전체 흐름·회귀·롤백을 재검증한다.
4. 기존 `labs/NN-...` 경로는 링크/증적 보존을 위해 유지하며, 완성된 통합 코드만 향후 역할군 하위에 작성한다.

[전체 역할군 목록](../README.md) · [인터페이스 규격](../../../docs/lab-interface-contract.md)
