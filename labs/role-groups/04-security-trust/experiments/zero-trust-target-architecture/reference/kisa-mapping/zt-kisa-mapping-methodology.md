# 통합 매핑 방법론

## 권위 계층

1. 제로트러스트 가이드라인 2.0은 요구 보안 속성, 아키텍처와 성숙도 의미를 정한다.
2. 인증된 2026 KISA 가이드는 자산별 기술 점검·판단·하드닝 참조를 제공한다.
3. 패키지는 실제 대상, 구성, 보호 범위, 롤백과 증적을 소유한다.
4. 스키마·읽기 전용 validator·테스트·정제 증적은 기록의 일관성을 검증한다.

상위 참조가 패키지 구현을 대신하지 않고, validator 성공이 상태를 자동 승격하지 않는다.

## 필수 기술통제 흐름

```text
ZT capability selected
-> target asset identified
-> applicable KISA item selected from authenticated source
-> version and patch applicability checked
-> current state inspected
-> risk and service impact assessed
-> backup and rollback prepared
-> minimum approved remediation applied
-> positive behavior tested
-> negative behavior tested
-> bypass tested
-> persistence tested
-> rollback tested
-> sanitized evidence generated
-> package status evaluated separately
```

## 분류 규칙

- `DIRECT`: 제로트러스트 통제 목적과 KISA 항목 목적이 직접 연결된다. 구현 증거라는 뜻은 아니다.
- `SUPPORTING`: 패키지 목적을 기술적으로 보조한다.
- `PARTIAL`: 목적의 일부만 연결된다.
- `GOVERNANCE_ONLY`: 검증·반복·예약 오케스트레이션이며 정확한 KISA 코드가 없다.
- `FUTURE_SCOPE`: 정확한 항목은 확인했지만 현재 승인 대상이 없다.
- `NOT_APPLICABLE`: 대상과의 비적용 판단이 증거로 확정된 경우에만 사용한다.

적용성은 `APPLICABLE`, `CONDITIONALLY_APPLICABLE`, `NOT_APPLICABLE`, `NOT_YET_ASSESSED`로 별도 기록한다. 같은 KISA 항목을 여러 패키지가 참조하면 소유 경계가 다른 이유를 `duplicate_mapping_rationale`에 기록한다. 중복 `DIRECT`에는 모든 record의 명시적 근거가 필요하다.

## 판단과 예외

KISA 판단 기준은 기술 참조다. 정확한 제품·버전·패치·벤더 구현·운영 정책·서비스 영향을 먼저 확인하며 맹목적으로 조치하지 않는다. 기술적으로 다른 등가 구성은 대상 증적, 영향 검토와 패키지 수용이 있을 때만 인정한다.

예외는 개인 이름이 아닌 역할 소유자를 사용하고, 사유·보상통제·증적·잔여 위험·검토 규칙·승인 증거를 기록한다. 보상통제에는 실제 동작 증거가 필요하다. 미지원·노후 지침은 버전 제한으로 남긴다.
