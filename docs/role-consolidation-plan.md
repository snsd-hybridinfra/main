# 운영 랩 구조

`snsd-hybridinfra/main`의 랩은 [포트폴리오](../README.md)에 있는 7개 운영 영역으로 구성합니다. 각 랩의 README에서 공통 실행 명령과 개별 실험을 확인할 수 있습니다. 각 실험은 담당 랩의 `experiments/<실험명>/`에 둡니다.

- [카탈로그 데이터](../labs/role-groups/manifest.json)는 실험의 경로와 검증 기록 상태를 관리합니다.
- [이관 대장](migration-register.md)은 과거 번호와 원본 커밋을 보존합니다.
- [공통 실행 계약](lab-interface-contract.md)은 결과 위치와 IDC 랩 간 연동을 설명합니다.

`python3 tools/check_catalog.py`로 실험의 배치와 README 링크를 확인합니다. `python3 tools/run_role.py all`로 랩별 로컬 검증을 실행합니다. 외부 런타임과 계정이 필요한 실험은 개별 실행 절차를 따릅니다.
