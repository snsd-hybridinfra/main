<!-- STATUS: CURRENT -->

# Document Cleanup Policy

## 1. 문서 목적

본 문서는 GitHub 저장소 내 문서 정리 기준을 정의한다.

현재 저장소에는 과거 진행 기록, 날짜별 작업 문서, 최신 아키텍처 문서가 함께 존재한다.  
멘토링 및 최종 발표 시 문서 간 기준이 충돌하지 않도록 최신 기준 문서와 과거 기록 문서를 구분한다.

---

## 2. 문서 분류 기준

| 분류 | 설명 | 처리 기준 |
|---|---|---|
| Current | 최신 기준 문서 | 멘토링 / 발표 기준으로 사용 |
| Historical | 작성 당시 작업 기록 | 내용 보존, 상단 안내 문구 추가 |
| Draft | 초안 또는 검증 전 문서 | 최신 여부 표시 필요 |
| Deprecated | 더 이상 사용하지 않는 구조 | 삭제하지 않고 대체 기준 명시 |
| Evidence | 캡처 / 실행 결과 / 로그 | 날짜와 검증 대상 명시 |

---

## 3. 최신 기준 문서

다음 문서는 최신 기준으로 유지한다.

```text
README.md
docs/current-status.md
docs/architecture.md
docs/automation-scope.md
docs/mentoring-brief.md
docs/resource-plan.md
docs/validation-plan.md
docs/backup-recovery-plan.md
docs/monitoring-plan.md
presentation/presentation-outline.md
```

이 문서들은 최신 아키텍처, 최신 자동화 범위, 최신 진행 상태를 반영해야 한다.

---

## 4. 과거 기록 문서

다음 유형의 문서는 과거 기록으로 취급한다.

```text
ansible/26_06_*.md
scripts/phase*-*.md
submission/meeting-notes/*
submission/work-logs/*
```

과거 기록 문서는 당시 작업 상태를 보존하기 위해 삭제하지 않는다.

단, 최신 기준과 혼동될 수 있으므로 필요한 경우 상단에 다음 문구를 추가한다.

```text
> Note: 본 문서는 작성 당시 진행 상황을 기준으로 작성된 작업 기록이다.
> 최신 아키텍처 기준은 docs/current-status.md 및 docs/architecture.md를 따른다.
```

---

## 5. 오래된 표현 처리 기준

| 오래된 표현 | 처리 방식 |
|---|---|
| Web1 / Web2 + HAProxy Round Robin | 과거 기록이면 유지, 최신 문서에서는 Docker Swarm 기준으로 수정 |
| Proxy Node Load Balancer | 최신 문서에서는 Proxy / HAProxy 역할을 최신 구조 기준으로 재정리 |
| 단일 DB Node | 최신 문서에서는 MariaDB Replica 검증 진행 중으로 표기 |
| Prometheus 설치 예정 | 최신 문서에서는 설치 완료, Grafana / Alertmanager 설정 진행 중으로 수정 |
| backup.sh 중심 | 최신 문서에서는 Restic 기반 백업 및 복구 테스트로 수정 |
| DB 이중화 Post-Phase | 최신 문서에서는 진행 / 검증 항목으로 관리 |
| OpenStack 수동 인스턴스 생성 | 최신 문서에서는 Provisioning 자동화 보완 필요로 표기 |

---

## 6. 삭제하지 말아야 할 문서

다음 문서는 오래된 표현이 있어도 삭제하지 않는다.

```text
회의록
작업일지
날짜별 작업 정리
트러블슈팅 기록
실행 전 검토 문서
멘토링 전후 비교 문서
```

이 문서들은 프로젝트 진행 이력을 보여주는 증거로 사용할 수 있다.

---

## 7. 수정해야 할 문서

다음 문서는 최신 기준으로 수정해야 한다.

```text
README.md
docs/architecture.md
docs/resource-plan.md
docs/mentoring-brief.md
docs/automation-scope.md
presentation/presentation-outline.md
```

이 문서들은 멘토링과 발표에서 직접 참조될 가능성이 높기 때문에 오래된 구조가 남아 있으면 안 된다.

---

## 8. 문서 정리 우선순위

| 우선순위 | 작업 |
|---:|---|
| 1 | 최신 기준 문서 생성 |
| 2 | README.md 최신 요약 반영 |
| 3 | architecture.md 최신 구조 반영 |
| 4 | automation-scope.md로 자동화 범위 명확화 |
| 5 | mentoring-brief.md로 멘토링 질문 정리 |
| 6 | 과거 문서 상단에 작성 당시 기준 문구 추가 |
| 7 | 발표자료 outline 최신화 |
| 8 | 최종 제출 패키지 문서 정리 |

---

## 9. 검수 명령

오래된 표현 검색은 다음 명령으로 수행한다.

```powershell
$patterns = @(
  "Web1",
  "Web2",
  "Round Robin",
  "Load Balancer",
  "로드밸런서",
  "HAProxy RR",
  "단일 DB",
  "DB Node 이중화는 Post-Phase",
  "Prometheus 설치 예정",
  "backup.sh",
  "Docker Compose",
  "Phase 2 작업 진행 완료",
  "인스턴스 생성 수동",
  "A급",
  "B급",
  "C급",
  "Nginx",
  "MariaDB 컨테이너"
)

Get-ChildItem -Recurse -File -Include *.md,*.yml,*.yaml,*.ini,*.sh |
  Where-Object { $_.FullName -notmatch "\\.git\\" } |
  Select-String -Pattern $patterns |
  Select-Object Path, LineNumber, Line
```

검색 결과가 나와도 무조건 삭제하거나 치환하지 않는다.

먼저 해당 문서가 최신 기준 문서인지 과거 기록 문서인지 구분한다.

---

## 10. 최종 정리 원칙

```text
최신 문서는 현재 구조 기준으로 통일한다.
과거 기록은 작성 당시 기준으로 보존한다.
오래된 표현은 삭제보다 분류와 주석으로 관리한다.
멘토링 기준점은 current-status.md, architecture.md, automation-scope.md, mentoring-brief.md로 통일한다.
```
