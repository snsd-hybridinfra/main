# KISA 매핑 범위와 제한

인증된 2026 가이드의 목차를 화면과 텍스트로 대조해 다음 원문 범위를 등록했다.

| Domain | 원문 절 | Pages |
|---|---|---:|
| UNIX_SERVER | Unix 서버 | 7-171 |
| WINDOWS_SERVER | Windows 서버 | 172-270 |
| WEB_SERVICE | 웹 서비스 | 271-352 |
| SECURITY_DEVICE | 보안 장비 | 353-386 |
| NETWORK_DEVICE | 네트워크 장비 | 387-466 |
| CONTROL_SYSTEM | 제어시스템 | 467-551 |
| PC_ENDPOINT | PC | 552-592 |
| DBMS | DBMS | 593-669 |
| MOBILE_TELECOMMUNICATION | 이동통신 | 670-675 |
| WEB_APPLICATION | Web Application(웹) | 676-786 |
| VIRTUALIZATION_PLATFORM | 가상화 장비 | 787-850 |
| CLOUD | 클라우드 | 851-873 |

현재 39개 exact-item record는 FND, NET, VIS, ID의 필수 초기 항목과 APP/DATA 미래 항목을 다룬다. CV, RV, SCH는 기술 항목을 추정하지 않고 3개 `GOVERNANCE_ONLY` record로 분류했다. DEV, SYS, AUTO 및 아직 선택되지 않은 제품별 항목은 package summary의 미해결 범위로 남는다.

16개 target class는 EVE-NG, OpenStack, Linux/Windows, 네트워크·보안 장비, Kubernetes, 데이터베이스, 웹, 모니터링, 중앙 ID, 가상화와 public cloud를 구분한다. AWS, Azure, OCI, Kubernetes, 중앙 모니터링과 중앙 ID는 구현 또는 런타임 완료로 기록하지 않는다.

금지하는 추론은 다음과 같다.

- 매핑 존재 = 통제 구현 또는 KISA item 통과
- 패키지의 다른 범위 증적 = 매핑된 기술 항목의 런타임 증적
- KISA item 통과 = KISA 준수, 인증 또는 법적 적합성
- 단일 랩 결과 = 전사·다중환경·생산 검증
- 문서, 설계, 설치 또는 평균 점수 = L3/L4 성숙도

raw PDF, 사설 절대 경로, 계정 값, 비밀과 개인 승인 데이터는 추적하지 않는다.
