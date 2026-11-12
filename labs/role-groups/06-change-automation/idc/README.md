# IDC Network Change Automation

가상 FRR의 설정을 Ansible로 백업하고, Leaf1의 수신 정책 후보를 Python으로 검증합니다. 실패 판정에는 VTEP 커널 FIB와 HTTP 프로브를 사용합니다. 원복 후 기준선과 설정을 다시 대조합니다. [작업 기록 양식](change-template.md)

## 백업과 설정 비교

[패브릭 기준선](../../01-network-fabric/idc/README.md)이 통과한 VM에서 Ansible Core를 준비합니다. 아래 명령은 `localhost`의 FRR VTY 4개를 읽습니다. sudo가 암호를 요구하면 `-K`를 사용합니다.

```sh
lab=labs/role-groups/06-change-automation/idc
ansible-playbook -i "$lab/inventory.ini" "$lab/backup.yml" -e snapshot=before
sudo python3 tools/idc.py change harmless
sudo python3 tools/idc.py change break-vtep
ansible-playbook -i "$lab/inventory.ini" "$lab/backup.yml" -e snapshot=after
sudo diff -ru .runtime/idc/backups/before .runtime/idc/backups/after
git diff -- labs/role-groups/01-network-fabric/idc/topology.json labs/role-groups/01-network-fabric/idc/configs
```

| 후보 | 검증 | 결과 상태 |
|---|---|---|
| `harmless` | 미광고 프리픽스 거부, 기준선 통과, 원복 후 설정·상태 일치 | `VERIFIED_ROLLED_BACK` |
| `break-vtep` | Leaf1에서 원격 VTEP /32 수신 차단, FIB·HTTP 실패 감지, 원복 후 설정·상태 일치 | `REJECTED_ROLLED_BACK` |

각 실행은 `.runtime/idc/changes/<실행 ID>/`에 `before.conf`, `applied.conf`, `restored.conf`, `change.diff`, `result.json`을 남깁니다. 검증·원복 중 예외도 기록하며, 기대한 상태 또는 원복 검증을 만족하지 않으면 종료 코드 1을 반환합니다. 작업 이벤트와 장애 알림은 [관제 랩](../../05-observability-sre/idc/README.md)에서 확인합니다.

토폴로지와 생성 설정은 Git의 변경 이력을 사용합니다. 실습 중 저장한 실행 구성과 원시 결과는 로컬 `.runtime/`에 보관합니다. 구성 변경은 `topology.json`과 렌더러를 먼저 수정한 뒤 `python3 tools/idc.py render` 및 `render --check`를 실행하고 diff를 검토합니다.

## 원복 확인

자동 원복 결과가 `ROLLBACK_FAILED`인 경우 `result.json`의 오류와 `change.diff`에서 적용 범위를 확인합니다. 이 전용 VM은 `sudo python3 tools/idc.py fabric down`과 `fabric up`으로 버전 관리된 기준 설정에서 다시 시작할 수 있습니다. 초기화 전에 필요한 증적을 보존하고, `sudo python3 tools/idc.py verify --wait 60`으로 상태를 확인합니다.
