# 수용된 Zero Trust - KISA 기술통제 프레임워크

기계 권위는 `zt-kisa-technical-control-map.yaml`이다. `ZT-GOV-MAP-001`은 42개 매핑 record를 수용했다. 39개는 원문 exact-item record, 3개는 코드 없는 `GOVERNANCE_ONLY` record다.

| Package | Mapping | Exact KISA items | Governance | 미해결 경계 |
|---|---|---|---|---|
| ZT-FND-001 | MAPPED | U-05, U-16, U-17, U-18, U-21, U-23, U-64 | - | 항목별 런타임 수용 없음 |
| ZT-NET-001 | PARTIALLY_MAPPED | U-28, S-06, N-06, CA-06 | - | 벤더·가상화 네트워크 적용성 |
| ZT-VIS-001 | PARTIALLY_MAPPED | U-21, U-65, U-66, U-67, S-10, N-14, HV-15, CA-13 | - | 중앙·지속 가시성 |
| ZT-ID-001 | MAPPED | U-01, U-05, U-06, U-07, U-08, U-10, U-11, U-12, U-16, U-18, U-23, U-63, W-06, HV-04, CA-03 | - | 런타임 수용, 중앙 ID/MFA |
| ZT-CV-001 | MAPPED | - | MAP-ZT-CV-001-GOVERNANCE | 교차검증 구현 및 부분 실행, FND 경고 예산으로 BLOCKED; KISA 기술항목 수용 주장은 없음 |
| ZT-RV-001 | MAPPED | - | MAP-ZT-RV-001-GOVERNANCE | 3회 반복 실행 없음 |
| ZT-SCH-001 | MAPPED | - | MAP-ZT-SCH-001-GOVERNANCE | scheduler installed and disabled; deferred final gate; 0 accepted scheduled dates |
| ZT-DEV-001 | UNMAPPED | - | - | 제품·OS별 적용성 검토 필요 |
| ZT-APP-001 | PARTIALLY_MAPPED | WEB-06, CI, IA | - | 현재 pilot이 항목 수용을 증명하지 않음 |
| ZT-DATA-001 | PARTIALLY_MAPPED | D-04, D-10 | - | 승인된 DBMS 대상 없음 |
| ZT-SYS-001 | UNMAPPED | - | - | OS·버전·구성 소유권별 검토 필요 |
| ZT-AUTO-001 | UNMAPPED | - | - | KISA 코드를 추정하지 않음 |

유형 합계는 `DIRECT 3`, `SUPPORTING 28`, `FUTURE_SCOPE 8`, `GOVERNANCE_ONLY 3`이다. `PARTIAL`과 `NOT_APPLICABLE` record는 현재 0개이며, 이는 비적용 또는 불완전성을 억지로 판단하지 않았다는 뜻이다.

Phase 1 흐름은 `ZT-ARC-001`이 둘러싼 `ZT-FND-001 -> ZT-NET-001 -> ZT-VIS-001 -> ZT-ID-001 -> ZT-CV-001 -> ZT-RV-001 -> P1-ACC-001`이다. ZT-SCH-001 매핑은 보존되지만 패키지는 최종 Phase 5 게이트로 연기되었다.

모든 exact-item과 governance-only record는 구현 `REFERENCED_ONLY`, 로컬·런타임 검증 `NOT_VALIDATED`, 증적 `SOURCE_METADATA_ONLY`, 성숙도 `UNASSESSED`, 컴플라이언스 `NOT_ASSESSED`다. 이 값은 매핑 관계의 상태이며 독립 패키지 상태를 낮추거나 올리지 않는다.
