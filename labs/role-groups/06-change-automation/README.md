# Operations, Change Validation & Evidence

**Primary role group** `06-change-automation` · **이관 자료는 런타임 재검증 전**

이 역할군은 하나의 *운영 책임 경계*와 **재현 가능한 통합 검증 흐름**을 제공해. 원본 개별 랩은 유일한 소스의 진실이며 이 인덱스는 코드 복제/성공 상태 승격이 아님.

## 운영 목적
장비·클라우드 변경 전 읽기 → 위험 승인 → 실행 제안 → 결과·회귀 증적

## 단일 실습 흐름
RESTCONF Read-Only(03) + Remote Validator(45) → Change Policy(21) → Repeatability/Evidence(22,37) → Day-2 Runbooks(36) → Repository Gates(47)

## 소속 랩

| ID | 랩 (canonical) | 현재 출처 기반 상태 |
|---|---|---|
| 03 | [03-restconf-python](../../03-restconf-python/README.md) | 기존 로컬 검증 기록 |
| 21 | [21-automation-approval](../../21-automation-approval/README.md) | 이관·재검증 대기 |
| 22 | [22-continuous-verification](../../22-continuous-verification/README.md) | 이관·재검증 대기 |
| 36 | [36-day2-operations-runbooks](../../36-day2-operations-runbooks/README.md) | 이관·재검증 대기 |
| 37 | [37-validation-fixtures](../../37-validation-fixtures/README.md) | 이관·재검증 대기 |
| 45 | [45-remote-readonly-validation](../../45-remote-readonly-validation/README.md) | 이관·재검증 대기 |
| 47 | [47-repository-quality-gates](../../47-repository-quality-gates/README.md) | 이관·재검증 대기 |

## 통합 대상, 중복 기능 정리
- 03+45: 멀티벤더 읽기 전용 수집과 증적 표준화
- 21+22+37+47: 정책·승인·테스트·회귀·증적 갱신을 하나의 변경 게이트로 연결

## 역할군 공통 인터페이스

- **Input:** sanitized state snapshot, proposed diff, policy decision, synthetic approval
- **Output:** change plan, denied/allowed audit, test evidence, rollback checkpoint
- **Mandatory gate:** 승인 없음, 위험도 누락, 오래된 증적, 명령 주입, 실패 후 중단, 롤백 검증

개별 랩에서 입력·출력 형식을 먼저 고정한 뒤 기능을 연결해. 기존 성공/실패 증적은 해당 랩에 유지하고, 통합 흐름의 결과는 **새로운 증적**을 따로 남겨야 해. 읽기 전용 관측과 변경·배포·삭제 코드는 같은 권한으로 실행하지 않음.

## 다음 조합 단계
1. 모든 랩의 의존성/하드코딩 경로를 해소하고 합성 데이터를 표준화한다.
2. 최소 단위 정상/거부/장애/복구 검증 후 통합 대상으로 승격한다.
3. 공통 인터페이스에 맞춰 각 랩을 조합하고 전체 흐름·회귀·롤백을 재검증한다.
4. 기존 `labs/NN-...` 경로는 링크/증적 보존을 위해 유지하며, 완성된 통합 코드만 향후 역할군 하위에 작성한다.

[전체 역할군 목록](../README.md) · [인터페이스 규격](../../../docs/lab-interface-contract.md)
