
# Capability Traceability Matrix

All rows are target-selection records, not current maturity assignments. Full source-aligned stage summaries, dependencies, current evidence, limitations, and rationale are in `capability-traceability-matrix.yaml`.

| ID | Canonical Korean name | Domain | Selection | Target | Implementation | Validation | Evidence | Source |
|---|---|---|---|---|---|---|---|---|
| ZT-1.1.1 | 사용자 인벤토리 | identity | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 56 |
| ZT-1.1.2 | ID 연계 및 사용자 자격 증명 | identity | ADVANCED_PRIMARY_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 56 |
| ZT-1.2.1 | 다중인증 (MFA) | identity | ADVANCED_PRIMARY_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 57 |
| ZT-1.2.2 | 지속 인증 | identity | INITIAL_TARGET | INITIAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 57 |
| ZT-1.3.1 | 통합 ICAM 플랫폼 | identity | DESIGN_ONLY | NONE | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 58 |
| ZT-1.3.2 | 행동, 컨텍스트 기반 ID 및 생체 인식 | identity | OPTIMAL_ROADMAP_ONLY | OPTIMAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 58 |
| ZT-1.4.1 | 조건부 사용자 접근 | identity | ADVANCED_PRIMARY_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 59 |
| ZT-1.4.2 | 최소 권한 접근 | identity | ADVANCED_PRIMARY_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 59 |
| ZT-2.1.1 | 기기 감지 및 규정 준수 | device-endpoint | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 60 |
| ZT-2.2.1 | 실시간 검사를 통한 기기 권한 부여 | device-endpoint | INITIAL_TARGET | INITIAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 61 |
| ZT-2.3.1 | 기기 인벤토리 | device-endpoint | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 62 |
| ZT-2.3.2 | 통합 엔드포인트 관리 및 모바일 기기 관리 | device-endpoint | DESIGN_ONLY | NONE | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 62 |
| ZT-2.4.1 | 엔드포인트 및 확장된 탐지·대응 (EDR 및 XDR) | device-endpoint | OPTIMAL_ROADMAP_ONLY | OPTIMAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 63 |
| ZT-2.4.2 | 자산, 취약성 및 패치 관리 자동화 | device-endpoint | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 63 |
| ZT-3.1.1 | 매크로 세그멘테이션 | network | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | PARTIALLY_VALIDATED | RUNTIME | p. 64-65 |
| ZT-3.1.2 | 마이크로 세그멘테이션 | network | INITIAL_TARGET | INITIAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 64-65 |
| ZT-3.1.3 | 소프트웨어 정의 네트워킹 | network | DESIGN_ONLY | NONE | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 64-65 |
| ZT-3.2.1 | 위협 대응 | network | ADVANCED_SUPPORTING_TARGET | ADVANCED | MAPPED | REFERENCE_ONLY | DESIGN | p. 66 |
| ZT-3.3.1 | 트래픽 암호화 | network | ADVANCED_PRIMARY_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 67 |
| ZT-3.4.1 | 데이터 흐름 매핑 | network | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | PARTIALLY_VALIDATED | RUNTIME | p. 68 |
| ZT-3.5.1 | 네트워크 회복성 | network | ADVANCED_SUPPORTING_TARGET | ADVANCED | MAPPED | REFERENCE_ONLY | DESIGN | p. 69 |
| ZT-4.1.1 | 접근통제 | system | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | PARTIALLY_VALIDATED | RUNTIME | p. 70 |
| ZT-4.2.1 | PAM | system | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 71 |
| ZT-4.2.2 | 자격 증명 관리 | system | ADVANCED_PRIMARY_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 71 |
| ZT-4.3.1 | 네트워크 세분화 및 그룹 간 이동 | system | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | PARTIALLY_VALIDATED | RUNTIME | p. 72 |
| ZT-4.4.1 | 시스템 환경에 따른 정책 관리 | system | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | REFERENCE_ONLY | DESIGN | p. 73 |
| ZT-5.1.1 | 리소스 권한 부여 및 통합 | application-workload | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | REFERENCE_ONLY | DESIGN | p. 74 |
| ZT-5.2.1 | 지속적인 모니터링 및 진행 중인 승인 | application-workload | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 75 |
| ZT-5.3.1 | 원격 접속 | application-workload | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 76 |
| ZT-5.4.1 | 안전한 애플리케이션 배포 | application-workload | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | REFERENCE_ONLY | DESIGN | p. 77 |
| ZT-5.4.2 | 애플리케이션 인벤토리 | application-workload | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 77 |
| ZT-5.5.1 | 안전한 소프트웨어·애플리케이션 개발 및 통합 | application-workload | DESIGN_ONLY | NONE | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 78 |
| ZT-5.5.2 | 소프트웨어 취약 관리 | application-workload | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 78 |
| ZT-6.1.1 | 데이터 카탈로그 위험 정렬 | data | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 79 |
| ZT-6.1.2 | 기업 데이터 거버넌스 | data | DESIGN_ONLY | NONE | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 79 |
| ZT-6.2.1 | 데이터 접근제어 | data | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | REFERENCE_ONLY | DESIGN | p. 80 |
| ZT-6.3.1 | 데이터 암호화 및 권한 관리 | data | ADVANCED_PRIMARY_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 81 |
| ZT-6.4.1 | 데이터 라벨링 및 태그 지정 | data | ADVANCED_PRIMARY_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 82 |
| ZT-6.5.1 | 데이터 손실 방지 (DLP) | data | INITIAL_TARGET | INITIAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 83 |
| ZT-6.5.2 | 데이터 모니터링 및 감지 | data | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 83 |
| ZT-7.1 | 모든 관련 활동 기록 | visibility-analytics | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | PARTIALLY_VALIDATED | RUNTIME | p. 84-86 |
| ZT-7.2 | 중앙집중적 보안 정보 및 이벤트 관리 | visibility-analytics | ADVANCED_PRIMARY_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 84-86 |
| ZT-7.3 | 보안 위협 분석 | visibility-analytics | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 84-86 |
| ZT-7.4 | 사용자 및 기기 동작 분석 | visibility-analytics | OPTIMAL_ROADMAP_ONLY | OPTIMAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 84-86 |
| ZT-7.5 | 위협 인텔리전스 통합 | visibility-analytics | OPTIMAL_ROADMAP_ONLY | OPTIMAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 84-86 |
| ZT-7.6 | 자동화된 동적 정책 | visibility-analytics | OPTIMAL_ROADMAP_ONLY | OPTIMAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 84-86 |
| ZT-8.1 | 정책 통합 | automation-integration | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | REFERENCE_ONLY | DESIGN | p. 87-89 |
| ZT-8.2 | 중요 프로세스 자동화 | automation-integration | ADVANCED_PRIMARY_TARGET | ADVANCED | MAPPED | PARTIALLY_VALIDATED | RUNTIME | p. 87-89 |
| ZT-8.3 | 인공지능 | automation-integration | OPTIMAL_ROADMAP_ONLY | OPTIMAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 87-89 |
| ZT-8.4 | 보안 통합, 자동화 및 대응 | automation-integration | OPTIMAL_ROADMAP_ONLY | OPTIMAL | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 87-89 |
| ZT-8.5 | 데이터 교환 표준화 | automation-integration | ADVANCED_PRIMARY_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 87-89 |
| ZT-8.6 | 보안 운영 조정 및 사고 대응 | automation-integration | ADVANCED_SUPPORTING_TARGET | ADVANCED | GAP_IDENTIFIED | GAP_IDENTIFIED | NONE | p. 87-89 |
