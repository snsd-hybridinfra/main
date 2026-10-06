# Terraform Security Validation: 공개 SSH 탐지와 수정 재검증

## 왜 이 랩을 만들었는가

[AWS Continuum 발표](https://aws.amazon.com/blogs/security/aws-continuum-sets-a-new-standard-in-autonomous-code-security/)(2026-10-05)는 취약점의 발견·재현·수정·기능 보존을 한 흐름으로 평가했다. [Google의 인프라 코드 보안 사례](https://cloud.google.com/blog/topics/systems/using-ai-agents-to-secure-google-infrastructure)(2026-09-18)도 코드 변경을 지속적으로 검사하고, 자동 수정안을 사람의 검토로 넘기는 방식을 설명한다.

두 원문의 Agent와 내부 시스템을 재현하지 않았다. 내가 시험한 질문은 더 작다. **Terraform 문법상 유효하지만 보안상 위험한 변경을 배포 전에 찾고, 수정본을 같은 규칙으로 다시 검사할 수 있는가?**

## 범위와 상태

- 상태: **로컬 검증**
- 실행 도구: Terraform 1.15.9, Checkov 3.3.21 컨테이너
- 선택한 규칙: `CKV_AWS_24` — SSH 22번 포트를 `0.0.0.0/0`에 열지 않음
- Cloud 자격증명: 사용하지 않음
- `terraform plan/apply`: 실행하지 않음

AWS Provider는 `terraform validate`를 위해 내려받았지만 AWS API는 호출하지 않았다. `before`와 `after` 구성은 임시 디렉터리에서 초기화하고 검증한 뒤 삭제한다.

## 내가 만든 Before와 After

```text
before/main.tf
0.0.0.0/0 → TCP 22
        │
        └─ Checkov CKV_AWS_24 실패

after/main.tf
203.0.113.10/32 → TCP 22
        │
        └─ 같은 규칙 통과
```

`203.0.113.10/32`는 실제 사무실 주소가 아니라 문서용 TEST-NET-3 주소다. 이 구성은 접근 가능한 관리망을 만든 것이 아니라 정적 분석 입력이다.

## 실행

```powershell
cd F:/main/labs/14-terraform-security-validation
./run.ps1
```

스크립트는 두 구성에 `terraform fmt -check`, `terraform init -backend=false`, `terraform validate`를 실행한 뒤 같은 Checkov 규칙으로 검사한다. 취약 구성의 종료 코드 1은 기대한 탐지 결과로 처리하고, 수정본은 종료 코드 0이어야 통과한다.

## 직접 확인한 결과

[2026-10-06 JSON 증적](evidence/2026-10-06.json):

| 단계 | Terraform Validate | Checkov 통과 | Checkov 실패 | 종료 코드 |
|---|---|---:|---:|---:|
| Before | 통과 | 0 | 1 (`CKV_AWS_24`) | 1 |
| After | 통과 | 1 | 0 | 0 |

Before에서는 `aws_security_group.admin`의 공개 SSH 규칙이 20~31행에서 탐지됐다. CIDR을 단일 문서용 관리 주소로 바꾼 After는 같은 규칙을 통과했다. “Scanner가 한 번 경고했다”에서 멈추지 않고 **같은 검사로 수정 결과를 다시 확인**했다.

첫 실행에서는 Checkov의 `--quiet` JSON이 통과 항목 상세를 생략하는 특성을 내 검증식이 고려하지 못해 전체 판정만 실패했다. 파서를 통과·실패 개수와 선택 규칙 기준으로 수정한 뒤 재실행해 네 검증 조건이 모두 통과했다.

## 원문과 내 실험의 경계

- 원문 사실: AWS와 Google은 Agent를 포함한 대규모 코드 보안 자동화와 자체 평가 결과를 설명했다.
- 내 실험 설계: 공개 SSH가 있는 작은 Terraform과 수정본을 Checkov 한 규칙으로 비교했다.
- 내 실행 결과: Before 1건 실패, After 1건 통과다.

## 확인하지 않은 범위

- AWS 인증, `terraform plan/apply`, 실제 Security Group과 네트워크 도달성
- AWS Continuum 또는 Google 내부 Agent 실행
- `CKV_AWS_24` 이외의 전체 Checkov 정책
- CI Merge 차단, 사람 승인, Drift 탐지, Rollback
- 실제 조직의 관리 CIDR과 변경 승인

다음 단계는 CI에서 이 랩을 반복 실행하고, 실패한 보안 검사가 Merge를 막는지 확인하는 것이다. 실제 AWS 적용은 별도의 비용·권한 경계와 승인 아래에서 진행해야 한다.
