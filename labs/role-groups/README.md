# 운영 랩 실행 가이드

[포트폴리오](../../README.md)의 7개 랩에서 실험을 주제별로 탐색할 수 있습니다. 각 랩의 `experiments/`에 구성·코드·과거 증적을 보관합니다.

## 일괄 실행

Linux에서 Python 3.11 이상으로 저장소 루트에서 실행합니다.

```sh
python3 tools/run_role.py all
```

결과는 `.runtime/role-labs/<UTC>/`에 저장됩니다. [대표 사례 실행 기록](evidence/2026-11-12.json)

## 검증 범위

- **로컬 검증**은 해당 실험 README에 명시한 로컬 실행 환경에서 확인한 결과입니다.
- **기존 로컬 검증 기록**은 개별 실험의 과거 실행 환경과 입력에 해당합니다.
- **이관 자료 · 개별 재검증 전**은 선별한 코드나 설계입니다. 공통 실행에서 사용한 일부 입력은 공통 실행 기록의 범위로 확인할 수 있습니다.
- **랩 간 실험**으로 가상 IDC 패브릭에 [경로 검증](01-network-fabric/idc/architecture.md), [관측](05-observability-sre/idc/README.md), [변경·원복](06-change-automation/idc/README.md), [장애 재현](07-recovery-dr/idc/validation.md)을 연결했습니다.

## 관련 문서

[역할 구성](../../docs/role-consolidation-plan.md) · [프로젝트 연결 지도](../../docs/project-map.md) · [이관 대장](../../docs/migration-register.md) · [카탈로그 데이터](manifest.json)

[브리핑](../../docs/briefings/README.md) · [뉴스와 실습 매핑](../../docs/news-to-labs.md) · [커리어 로드맵](../../docs/career-roadmap.md)
