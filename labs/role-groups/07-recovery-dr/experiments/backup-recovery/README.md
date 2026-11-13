# 05 백업·복구: 합성 서비스의 RTO/RPO 측정

## 이걸 해본 이유

[AWS의 DR 계획 글(2026-09-17)](https://aws.amazon.com/blogs/compute/planning-for-disaster-recovery-using-aws-local-zones-and-aws-outposts-racks/)을 읽고 RTO와 RPO를 문서에만 적지 말고 직접 재 보기로 했다. **서비스를 지우고 최근 백업으로 복구하면 몇 초가 걸리고 몇 건이 사라질까?**를 작은 SQLite 서비스로 확인했다. AWS Local Zones나 Outposts는 사용하지 않았다.

2026-10-08 [Yandex 데이터센터 피격 보도](https://www.reuters.com/world/drones-hit-yandex-data-centre-first-major-attack-russian-data-hub-2026-10-08/)에서 물리 시설 피해와 전력 문제가 일부 클라우드 운영 중단으로 이어진 사례를 확인했다. 새 랩을 만들지 않고 기존 복구 흐름을 `site-a` 장애 뒤 `site-b`의 새 엔드포인트로 복원하는 형태로 넓혔다. 실제 Yandex 환경이나 데이터센터를 재현한 것은 아니다.

Python 표준 라이브러리로 루프백 HTTP 서비스와 임시 SQLite DB를 만들고 복구 과정을 실제로 실행했다. 여기서 나온 시간은 이 노트북에서 한 번 실행한 값이다.

## 미리 정한 기대값

합성 서비스를 중단하고 주 DB를 잃었을 때 최근 스냅샷으로 다른 로컬 사이트 모델에 복구하는 데 얼마나 걸리며, 스냅샷 이후 기록은 얼마나 사라지는가?

- `RTO`: 장애 시작 직전부터 복원된 서비스의 `/health` 응답까지 걸린 시간.
- 관측 `RPO`: 마지막 백업 시각부터 장애 시각까지의 간격. 실제 손실 건수도 별도로 기록한다.
- 예상: 백업 전 3건은 복원, 백업 후 2건은 손실. 기존 엔드포인트는 계속 중단 상태이고 새 복구 엔드포인트가 응답한다.

## 어떻게 고장 내고 복구했나

- `service.py`: `127.0.0.1`의 `/events` POST와 `/health` GET만 제공.
- `run-lab.py`: 임시 `site-a`에서 DB 생성 → 3건 입력 → 두 사이트 밖의 `isolated-backup`에 스냅샷 → 2건 추가 → 프로세스 중단·주 DB 제거 → 잘못된 백업 파일 복원 실패 확인 → 임시 `site-b`에 유효한 스냅샷 복원 → 다른 포트로 서비스 기동·응답 확인.
- 저장소 밖 임시 DB와 디렉터리만 사용하고 종료 시 삭제한다. 두 포트는 로컬에서 임시로 할당한다.

```powershell
python F:\main\labs\05-backup-recovery\run-lab.py --evidence F:\main\labs\05-backup-recovery\evidence\2026-10-09.json
```

## 직접 측정한 결과

[2026-10-09 정제 실행 결과](evidence/2026-10-09.json):

| 지표 | 결과 |
|---|---:|
| 장애 전 이벤트 | 5건 |
| 복원 후 이벤트 | 3건 |
| 손실 | 2건 |
| 백업→장애 간격 | 0.045초 |
| 장애→다른 엔드포인트 응답(RTO) | 1.633초 |
| `site-a` 기존 엔드포인트 중단 유지 | 확인 |
| `site-b` 복구 엔드포인트 정상 | 확인 |
| 없는 백업 파일 복원 시도 | 거부 확인 |

백업→장애 시간은 일부러 짧게 만든 실습 구간이다. 이 수치와 2건 손실은 해당 한 번의 실행에서만 측정되었다. `site-a`와 `site-b`는 같은 노트북의 서로 다른 임시 디렉터리와 포트일 뿐 실제 장애 도메인이 아니다. 물리 데이터센터, 전력, 회선, DNS·트래픽 매니저, 비동기 복제, 애플리케이션 일관성, 오프사이트 백업은 검증하지 않았다. 같은 코드를 다시 실행하면 OS 부하에 따라 RTO가 달라진다. 이전 [2026-09-22 증적](evidence/2026-09-22.json)은 단일 엔드포인트 복원 기준선으로 남겼다.

## 다음에 프로젝트에서 확인할 것

서브 프로젝트의 운영 증적으로 옮기려면 실제 대상 서비스의 데이터 일관성 검증, 주기별 복구 훈련, 격리된 백업, 복원 권한, 여러 번 측정한 시간 분포가 필요하다. 이 실습 결과를 그 환경의 RTO/RPO로 쓰지 않는다.

## 참고

- [Python sqlite3 Connection.backup 문서](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup)
