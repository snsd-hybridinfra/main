# 04 IAM / STS: 탈취된 역할의 행동 범위 줄이기

## 왜 이 실습을 했나

[Google Threat Intelligence Group의 적대적 AI 분석](https://cloud.google.com/blog/topics/threat-intelligence/from-prompting-to-autonomy-the-evolution-of-adversarial-ai)(2026-09-08)을 읽으면서 클라우드 자격증명이 탈취됐을 때 피해 범위를 어디까지 줄일 수 있는지가 궁금했다. 이어서 [Microsoft의 Storm-3168 분석](https://www.microsoft.com/en-us/security/blog/2026/09/25/storm-3168-agentic-driven-cloud-attacks-using-compromised-service-principals/)(2026-09-25)을 확인했다. 공격자는 탈취한 Azure Service Principal로 자원을 대량 삭제하고 다른 자격증명도 수집했다. 일부 Storage 삭제는 Resource Lock과 삭제 보호에 막혔다.

기사의 공격을 재현하지는 않았다. 대신 더 작은 질문으로 바꿨다.

> 역할 자격증명이 노출되더라도 신뢰 관계, 역할 권한, 세션 정책, 명시적 거부를 겹쳐 두면 허용된 작업 밖으로 나가지 못하게 할 수 있을까?

실제 계정에서 바로 시험하기 전에 정책 관계부터 확실히 이해하고 싶어서 AWS 형식의 합성 정책과 작은 로컬 평가기를 만들었다.

## 이번에 만든 환경

실제 AWS나 Azure 계정은 연결하지 않았다. Python 3 표준 라이브러리만 사용했고, 계정 번호 `111122223333`과 버킷 이름 `lab-synthetic-artifacts`도 모두 실습용 값이다.

정책은 네 부분으로 나눴다.

- [`caller-permissions.example.json`](caller-permissions.example.json): 호출자가 요청할 수 있는 역할을 하나로 제한했다.
- [`trust-policy.example.json`](trust-policy.example.json): 지정한 호출자 역할만 신뢰하도록 했다.
- [`role-permissions.example.json`](role-permissions.example.json): 합성 버킷 조회는 허용하고 객체 쓰기와 삭제는 명시적으로 거부했다.
- [`session-policy.example.json`](session-policy.example.json): 세션에서는 버킷 목록 조회만 남겼다.

[`scenarios.json`](scenarios.json)에는 정상 요청과 거부돼야 할 요청을 합쳐 7개를 적었다. [`evaluate_policy.py`](evaluate_policy.py)는 이 실습에서 사용한 `Action`, `Resource`, `Principal`, `Allow`, `Deny`만 판정한다. AWS IAM 전체를 흉내 낸 도구는 아니다. 조건 키, SCP, Permission Boundary, Resource Policy는 처리하지 않는다.

## 실행

```powershell
cd F:\main\labs\04-iam-sts
python .\evaluate_policy.py --directory . --evidence .\evidence\2026-09-28.json
```

평가기는 각 시나리오의 예상값과 실제 판정을 비교하고 하나라도 다르면 실패 코드로 끝난다. 실행 결과는 날짜별 JSON으로 남긴다.

## 내가 확인한 결과

2026-09-28 실행에서는 7개 시나리오가 전부 예상과 같았다. 허용은 2건, 거부는 5건이었다.

| 해본 요청 | 나온 결과 | 확인한 이유 |
|---|---|---|
| 지정 호출자가 역할 요청 | 허용 | 호출자 정책과 신뢰 정책이 모두 일치했다. |
| 다른 호출자가 같은 역할 요청 | 거부 | 호출자 쪽 허용만으로는 부족했고 신뢰 정책에서 막혔다. |
| 합성 버킷 목록 조회 | 허용 | 역할 정책과 세션 정책에 모두 포함됐다. |
| 객체 조회 | 묵시적 거부 | 역할은 허용했지만 세션 정책이 권한을 더 좁혔다. |
| 객체 쓰기와 삭제 | 명시적 거부 | `NoBucketWrites`가 두 요청을 막았다. |
| 계정 전체 버킷 조회 | 묵시적 거부 | 어느 정책에도 허용 규칙이 없었다. |

결과 원본은 [2026-09-28 실행 증적](evidence/2026-09-28.json)에 저장했다. 입력 정책과 시나리오의 SHA-256도 같이 기록해 어떤 파일로 실행했는지 다시 확인할 수 있게 했다.

## 해보고 정리한 점

역할 정책에 읽기 권한이 있어도 세션 정책에 없으면 최종 권한에서 빠졌다. 반대로 세션 정책에 항목을 더 넣는다고 역할 정책보다 권한이 커지지는 않았다. 쓰기와 삭제는 명시적 거부가 우선했다. 이번 실습에서 확인하고 싶었던 것은 이 세 가지 관계였다.

다만 결과를 AWS나 Azure의 실제 방어 효과로 해석할 수는 없다. 로컬 평가기가 정해 둔 정책 일부만 계산했기 때문이다. 아직 다음 항목은 직접 확인하지 못했다.

- AWS `AssumeRole` 호출과 임시 자격증명의 발급·만료
- Azure Service Principal과 실제 RBAC 판정
- 노출된 자격증명의 폐기와 회전
- Azure Resource Lock과 삭제 보호의 실제 차단
- 운영 자원에 대한 공격이나 삭제

그래서 현재 상태는 **로컬 정책 판정 7/7 통과**로 기록했다. 클라우드 런타임 검증은 아니다.

## 다음에 실제 계정에서 해볼 순서

1. 격리된 실습 계정에 빈 버킷과 호출자·대상 역할을 만든다.
2. 900초 세션 정책으로 `AssumeRole`을 호출하고 `get-caller-identity`와 만료 시각을 기록한다.
3. 허용한 `ListBucket`·`GetObject`는 성공하고 `DeleteObject`·`DeleteBucket`은 명시적 거부되는지 확인한다.
4. CloudTrail에서 같은 세션의 `userIdentity`, `eventName`, `eventTime`과 거부 오류를 대조한다.
5. 세션 만료 후 `ExpiredToken`을 확인한다.
6. 역할과 버킷을 지우고 결정 결과와 오류 코드만 정리해 남긴다.

이 흐름은 나중에 `snsd-multicloud-ops`의 Public Cloud Adapter와 Agent Workload Identity를 붙일 때 다시 사용할 생각이다. 현재 그 어댑터는 `DEFERRED` 상태라서 이번 결과를 서브 프로젝트 구현 증거로 포함하지 않았다.
