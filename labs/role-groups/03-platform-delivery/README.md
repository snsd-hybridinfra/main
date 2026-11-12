# Platform Engineering & Application Delivery

개발자 요청이 어떤 실행 프로파일과 의존성으로 이어지는지 확인합니다.

## 실행

저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py 03-platform-delivery
```

Lab 27의 요청 해석기와 Lab 29의 카탈로그를 연결합니다. 개발 VM 요청은 로컬 모듈로 해석되고, 개발 API 요청은 필수 어댑터 및 의존성이 준비될 때까지 차단됩니다. 두 요청의 digest와 배포 권한 상태를 `blueprints.json`에서 확인합니다.

실습 범위는 카탈로그와 배포 조건 검증입니다.

## 번호 랩

| ID | 실습과 자료 | 번호 랩의 기록 |
|---|---|---|
| 25 | [25-container-supply-chain](../../25-container-supply-chain/README.md) | 이관 참고 |
| 27 | [27-self-service-request-api](../../27-self-service-request-api/README.md) | 이관 참고 |
| 28 | [28-approval-grant-lifecycle](../../28-approval-grant-lifecycle/README.md) | 이관 참고 |
| 29 | [29-terraform-runner-blueprints](../../29-terraform-runner-blueprints/README.md) | 이관 참고 |
| 30 | [30-agent-data-contracts](../../30-agent-data-contracts/README.md) | 이관 참고 |
| 31 | [31-kubernetes-gitops](../../31-kubernetes-gitops/README.md) | 이관 참고 |
| 34 | [34-postgres-schema-migrations](../../34-postgres-schema-migrations/README.md) | 이관 참고 |
| 35 | [35-portal-ui-contracts](../../35-portal-ui-contracts/README.md) | 이관 참고 |
| 49 | [49-edge-security-service-contracts](../../49-edge-security-service-contracts/README.md) | 이관 참고 |

[역할 랩 인덱스](../README.md) · [대표 사례 검증 결과](../evidence/2026-11-12.json)
