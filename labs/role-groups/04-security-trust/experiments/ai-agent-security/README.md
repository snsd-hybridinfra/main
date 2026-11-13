# 07 AI Agent Security: 서명된 실행 범위와 도구 호출 경계

## 이걸 해본 이유

[Google Cloud의 Agent 기반 인프라 보안 글](https://cloud.google.com/blog/topics/systems/using-ai-agents-to-secure-google-infrastructure/)(2026-09-18)을 읽고 Agent에게 도구를 연결할 때 어디서 멈추게 할지를 먼저 만들어 봤다. 이후 [Microsoft Execution Containers](https://blogs.windows.com/windowsdeveloper/2026/10/07/microsoft-execution-containers-policy-driven-containment-for-ai-agents/)(2026-10-07)를 보며 Agent ID와 파일·네트워크 경계도 같은 게이트에 넣었다.

[ServiceNow의 AI Passport 발표](https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-advances-its-operational-harness-for-enterprise-AI-with-AI-Passport-and-expanded-governance-capabilities/default.aspx)(2026-10-15)는 Agent와 MCP 서버가 실행 시점에 허가 범위를 증명하고, 범위를 벗어나면 제한하거나 중단하는 구조를 설명한다. 제품을 재현할 수는 없지만, 문자열 Agent ID만 믿던 기존 실습은 약하다는 점이 분명했다.

새 랩을 만들지 않고 기존 게이트를 고쳤다. 로컬 HMAC 서명을 붙인 테스트 Passport에 Agent ID와 허용 도구 목록을 넣고, 서명 변조·범위 초과·폐기된 Identity를 실제 도구 실행 전에 거부하는지 확인했다.

## 확인하려던 것

1. 서명된 Passport가 없거나 변조되면 도구 실행 전에 멈추는가?
2. 유효한 Passport라도 담긴 도구 범위를 넘거나 Identity가 폐기되면 거부되는가?
3. 유효한 Identity 안에서도 파일·통신·예산·쓰기 승인을 계속 제한할 수 있는가?

## 게이트를 만든 방법

[policy.json](policy.json)은 허용 Agent ID, Passport Key ID, 폐기된 Agent ID, 도구·경로·통신·비용·승인 규칙을 담는다. [run-lab.py](run-lab.py)는 테스트용 HMAC Key로 Passport를 발급·검증하고, 임시 디렉터리와 루프백 HTTP 서버에서 실제 파일 읽기·HTTP GET·파일 쓰기를 수행한다.

HMAC Key는 재현을 위한 로컬 테스트 값이며 운영 비밀이나 ServiceNow 구현이 아니다. 운영에서는 비대칭 서명, Key Rotation, IdP, 중앙 폐기 목록과 감사 저장소가 필요하다.

실행:

    python F:\main\labs\07-ai-agent-security\run-lab.py --evidence F:\main\labs\07-ai-agent-security\evidence\2026-10-18.json

## 직접 확인한 결과

[2026-10-18 정제 실행 결과](evidence/2026-10-18.json):

| 호출 | 실제 판정 |
|---|---|
| Passport 없음 | passport_required |
| 서명 변조 | passport_invalid |
| 폐기된 Agent Passport | identity_revoked |
| 읽기 전용 Passport로 HTTP 시도 | scope_denied |
| 허용된 Agent의 파일 읽기 | allow |
| 등록되지 않은 Agent ID | identity_denied |
| 등록되지 않은 셸 도구 | tool_denied |
| 임시 작업 공간 밖 읽기 | path_denied |
| 외부 호스트로 향하는 HTTP 요청 | network_denied |
| 허용된 로컬 호스트의 다른 경로 요청 | network_denied |
| 지정된 루프백 HTTP GET | allow |
| 미허용 보고서 경로 쓰기 | path_denied |
| 승인 없는 보고서 쓰기 | approval_required, 파일 없음 |
| 합성 승인 뒤 보고서 쓰기 | allow |
| 4단위 소진 뒤 읽기 | budget_exceeded |

15개 판정이 예상값과 일치했고, 거부 시나리오는 파일·HTTP·쓰기 동작 전에 끝났다. 허용된 세 번의 실행만 비용 4단위를 사용했다.

## 이번 결과의 범위

- ServiceNow AI Passport, Super Intelligence Control Tower, NVIDIA OpenShell을 실행하지 않았다.
- Passport는 내 실험 설계인 HMAC 토큰이다. 비대칭 서명, PKI, Key Rotation, IdP, CMDB, GRC와 분산 폐기는 검증하지 않았다.
- 실제 LLM Agent나 MCP 서버가 연결된 것이 아니며 Python 프로세스 자체가 게이트 밖 API를 직접 부르면 우회할 수 있다.
- 승인도 테스트 코드가 넣은 합성 상태다. 운영에서는 모든 도구 실행을 단일 경계로 통과시키고 OS 수준 격리와 사람 승인 기록을 추가해야 한다.

이전 [2026-10-08 증적](evidence/2026-10-08.json)은 서명된 Passport를 추가하기 전 기준선으로 남겼다.

## 프로젝트에 붙이기 전에 남은 것

서브 프로젝트의 AI 운영 보조 기능에 적용한다면 읽기 권한부터 시작하고, 짧은 수명의 서명된 Workload Identity와 중앙 폐기, 도구별 Scope, 쓰기 승인, 불변 감사 로그를 함께 붙인다. 이 결과는 서브 프로젝트 Agent 배포 증거가 아니다.
