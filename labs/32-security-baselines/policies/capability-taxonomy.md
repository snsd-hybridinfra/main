# Zero Trust Capability Taxonomy

Canonical Korean display names and capability numbering follow the authoritative source. English slugs are stable repository identifiers, not official translations.

Source: 제로트러스트 가이드라인 2.0, p. 53, Figure 3-3; pp. 54-55, Table 3-10.

## 식별자·신원 (`identity`)

### 식별자 관리 (`identifier-management`)

- `ZT-1.1.1` 사용자 인벤토리 (`user-inventory`)
- `ZT-1.1.2` ID 연계 및 사용자 자격 증명 (`id-federation-user-credentials`)

### 인증 (`authentication`)

- `ZT-1.2.1` 다중인증 (MFA) (`multi-factor-authentication`)
- `ZT-1.2.2` 지속 인증 (`continuous-authentication`)

### 위험도 평가 (`risk-assessment`)

- `ZT-1.3.1` 통합 ICAM 플랫폼 (`integrated-icam-platform`)
- `ZT-1.3.2` 행동, 컨텍스트 기반 ID 및 생체 인식 (`behavior-context-id-biometric-recognition`)

### 접근관리 (`access-management`)

- `ZT-1.4.1` 조건부 사용자 접근 (`conditional-user-access`)
- `ZT-1.4.2` 최소 권한 접근 (`least-privilege-access`)

## 기기 및 엔드포인트 (`device-endpoint`)

### 정책 준수 모니터링 (`policy-compliance-monitoring`)

- `ZT-2.1.1` 기기 감지 및 규정 준수 (`device-detection-compliance`)

### 데이터 접근제어 (`data-access-control`)

- `ZT-2.2.1` 실시간 검사를 통한 기기 권한 부여 (`real-time-inspection-device-authorization`)

### 자산관리 (`asset-management`)

- `ZT-2.3.1` 기기 인벤토리 (`device-inventory`)
- `ZT-2.3.2` 통합 엔드포인트 관리 및 모바일 기기 관리 (`unified-endpoint-mobile-device-management`)

### 기기 위협 보호 (`device-threat-protection`)

- `ZT-2.4.1` 엔드포인트 및 확장된 탐지·대응 (EDR 및 XDR) (`endpoint-extended-detection-response`)
- `ZT-2.4.2` 자산, 취약성 및 패치 관리 자동화 (`asset-vulnerability-patch-automation`)

## 네트워크 (`network`)

### 네트워크 세분화 (`network-segmentation`)

- `ZT-3.1.1` 매크로 세그멘테이션 (`macro-segmentation`)
- `ZT-3.1.2` 마이크로 세그멘테이션 (`micro-segmentation`)
- `ZT-3.1.3` 소프트웨어 정의 네트워킹 (`software-defined-networking`)

### 위협 대응 (`threat-response`)

- `ZT-3.2.1` 위협 대응 (`threat-response`)

### 트래픽 암호화 (`traffic-encryption`)

- `ZT-3.3.1` 트래픽 암호화 (`traffic-encryption`)

### 트래픽 관리 (`traffic-management`)

- `ZT-3.4.1` 데이터 흐름 매핑 (`data-flow-mapping`)

### 네트워크 회복성 (`network-resilience`)

- `ZT-3.5.1` 네트워크 회복성 (`network-resilience`)

## 시스템 (`system`)

### 접근통제 (`access-control`)

- `ZT-4.1.1` 접근통제 (`access-control`)

### 시스템 계정 관리 (`system-account-management`)

- `ZT-4.2.1` PAM (`privileged-access-management`)
- `ZT-4.2.2` 자격 증명 관리 (`credential-management`)

### 네트워크 분리 정책 (`network-separation-policy`)

- `ZT-4.3.1` 네트워크 세분화 및 그룹 간 이동 (`network-segmentation-intergroup-movement`)

### 시스템 보안 및 정책 관리 (`system-security-policy-management`)

- `ZT-4.4.1` 시스템 환경에 따른 정책 관리 (`environment-based-policy-management`)

## 애플리케이션 및 워크로드 (`application-workload`)

### 애플리케이션 접근 (`application-access`)

- `ZT-5.1.1` 리소스 권한 부여 및 통합 (`resource-authorization-integration`)

### 애플리케이션 위협 보호 (`application-threat-protection`)

- `ZT-5.2.1` 지속적인 모니터링 및 진행 중인 승인 (`continuous-monitoring-approval-in-progress`)

### 접근 가능한 애플리케이션 (`accessible-application`)

- `ZT-5.3.1` 원격 접속 (`remote-access`)

### 안전한 애플리케이션 배포 (`secure-application-deployment`)

- `ZT-5.4.1` 안전한 애플리케이션 배포 (`secure-application-deployment`)
- `ZT-5.4.2` 애플리케이션 인벤토리 (`application-inventory`)

### 소프트웨어·애플리케이션 보안 (`software-application-security`)

- `ZT-5.5.1` 안전한 소프트웨어·애플리케이션 개발 및 통합 (`secure-application-development-integration`)
- `ZT-5.5.2` 소프트웨어 취약 관리 (`software-vulnerability-management`)

## 데이터 (`data`)

### 데이터 목록 관리 (`data-inventory-management`)

- `ZT-6.1.1` 데이터 카탈로그 위험 정렬 (`data-catalog-risk-sorting`)
- `ZT-6.1.2` 기업 데이터 거버넌스 (`enterprise-data-governance`)

### 접근 결정방법 (`access-decision-method`)

- `ZT-6.2.1` 데이터 접근제어 (`data-access-control`)

### 데이터 암호화 (`data-encryption`)

- `ZT-6.3.1` 데이터 암호화 및 권한 관리 (`data-encryption-key-management`)

### 데이터 분류 (`data-classification`)

- `ZT-6.4.1` 데이터 라벨링 및 태그 지정 (`data-labeling-tagging`)

### 데이터 손실 방지 (`data-loss-prevention`)

- `ZT-6.5.1` 데이터 손실 방지 (DLP) (`data-loss-prevention`)
- `ZT-6.5.2` 데이터 모니터링 및 감지 (`data-monitoring-detection`)

## 가시성 및 분석 (`visibility-analytics`)

### 가시성 및 분석 (`visibility-analytics`)

- `ZT-7.1` 모든 관련 활동 기록 (`record-all-relevant-activities`)
- `ZT-7.2` 중앙집중적 보안 정보 및 이벤트 관리 (`centralized-security-information-event-management`)
- `ZT-7.3` 보안 위협 분석 (`security-threat-analysis`)
- `ZT-7.4` 사용자 및 기기 동작 분석 (`user-device-behavior-analysis`)
- `ZT-7.5` 위협 인텔리전스 통합 (`threat-intelligence-integration`)
- `ZT-7.6` 자동화된 동적 정책 (`automated-dynamic-policy`)

## 자동화 및 통합 (`automation-integration`)

### 자동화 및 통합 (`automation-integration`)

- `ZT-8.1` 정책 통합 (`policy-integration`)
- `ZT-8.2` 중요 프로세스 자동화 (`critical-process-automation`)
- `ZT-8.3` 인공지능 (`artificial-intelligence`)
- `ZT-8.4` 보안 통합, 자동화 및 대응 (`security-integration-automation-response`)
- `ZT-8.5` 데이터 교환 표준화 (`data-exchange-standardization`)
- `ZT-8.6` 보안 운영 조정 및 사고 대응 (`security-operations-coordination-incident-response`)

## Validation

The hierarchy contains 8 top-level domains and 52 detailed capabilities. Capability maturity characteristics remain in the source-specific tables referenced by `capability-catalog.yaml`; this taxonomy does not restate or invent those requirements.

