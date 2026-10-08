# 07 AI Agent Security: 도구 호출 경계

## 이걸 해본 이유

[Google Cloud의 Agent 기반 인프라 보안 글(2026-09-18)](https://cloud.google.com/blog/topics/systems/using-ai-agents-to-secure-google-infrastructure/)을 읽고 Agent에게 도구를 연결할 때 어디서 멈추게 할지를 먼저 만들어 보고 싶었다. **허용 도구, 파일 경로, 통신 대상, 실행 예산, 쓰기 승인을 한곳에서 검사할 수 있는가?**를 로컬 게이트로 시험했다.

2026-10-07에 공개된 [Microsoft Execution Containers(MXC)](https://blogs.windows.com/windowsdeveloper/2026/10/07/microsoft-execution-containers-policy-driven-containment-for-ai-agents/)는 Agent의 파일·네트워크 접근을 정책으로 제한하고 Agent 행위를 사용자와 구분하는 방향을 설명했다. 새 랩을 만들지 않고 기존 게이트에 허용 Agent ID, 정확한 루프백 경로, 정확한 보고서 경로 검사를 추가했다.

실제 LLM이나 MXC는 붙이지 않았다. 입력이 같으면 같은 결과가 나오는 로컬 호출 하네스에서 정책부터 확인했다. OS 수준 격리와 실제 사람 승인 절차는 다음 단계로 남겼다.

## 확인하려던 것

Agent ID와 Agent가 사용할 도구, 파일 경로, 통신 대상, 실행 예산, 쓰기 승인 범위를 정책으로 제한할 수 있는가?

## 게이트를 만든 방법

[`policy.json`](policy.json)은 지정된 Agent ID에만 읽기, 지정된 루프백 HTTP GET, 보고서 쓰기를 허용한다. 요청당 비용을 합산해 4단위에서 멈추고, 보고서 쓰기 전에는 승인 상태를 요구한다. `run-lab.py`는 임시 디렉터리와 루프백 HTTP 서버를 만들고 실제 파일 읽기·HTTP GET·파일 쓰기를 게이트를 통해 실행한다.

```powershell
python F:\main\labs\07-ai-agent-security\run-lab.py --evidence F:\main\labs\07-ai-agent-security\evidence\2026-10-08.json
```

## 직접 확인한 결과

[2026-10-08 정제 실행 결과](evidence/2026-10-08.json):

| 호출 | 기대 | 실제 |
|---|---|---|
| 허용된 Agent의 파일 읽기 | 허용 | allow |
| 등록되지 않은 Agent ID | 거부 | identity_denied |
| 등록되지 않은 셸 도구 | 거부 | tool_denied |
| 임시 작업 공간 밖 읽기 | 거부 | path_denied |
| 외부 호스트 HTTP | 호출 전 거부 | network_denied |
| 루프백의 미허용 경로 | 호출 전 거부 | network_denied |
| 지정된 루프백 HTTP GET | 허용 | allow |
| 미허용 보고서 경로 쓰기 | 거부 | path_denied |
| 승인 없는 보고서 쓰기 | 거부, 파일 없음 | approval_required, 파일 없음 |
| 합성 승인 뒤 보고서 쓰기 | 허용 | allow |
| 4단위 소진 뒤 읽기 | 거부 | budget_exceeded |

외부 호스트 요청과 루프백의 미허용 경로 요청은 실행되지 않았다. 허용 Agent ID도 이 하네스가 전달한 문자열이므로 운영 Identity Provider가 발급·검증한 신원을 뜻하지 않는다. 예산은 이 하네스의 **호출 비용 단위**이며 모델 토큰·API 과금 한도가 아니다. 승인은 테스트 코드가 넣은 합성 상태이므로 실제 사람의 신원·승인 기록을 증명하지 않는다. Python 프로세스 자체가 다른 네트워크·파일 API를 직접 호출할 수 있다면 이 게이트를 우회할 수 있다. 실제 Agent에 적용할 때는 도구 실행 인터페이스를 단일 게이트로 제한하고 MXC 같은 OS 수준 파일·네트워크 격리, 검증된 Workload Identity와 승인 기록을 추가해야 한다. 이전 [2026-09-22 증적](evidence/2026-09-22.json)은 확장 전 기준선으로 남겼다.

## 프로젝트에 붙이기 전에 남은 것

서브 프로젝트에 AI 운영 보조 기능을 붙일 때 실행 권한을 읽기부터 시작하고 쓰기는 명시적 승인 후 수행하는 정책의 초안으로 활용한다. 이 결과는 서브 프로젝트 Agent 배포 증거가 아니다.
