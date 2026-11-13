# 네트워크 변경 검증

`change-validate`는 Leaf1의 정해진 후보를 Ansible로 적용합니다. Python은 장비 4대의 구성 백업과 함께 인터페이스, IPv4·EVPN BGP, VTEP와 TENANT 경로, ICMP, L2/L3 HTTP를 전후로 비교합니다.

## 변경 실행

전용 Debian VM에 `sudo apt-get install -y ansible-core`로 Ansible Core를 설치하고 `sudo python3 -m ansible.cli.playbook --version`으로 확인합니다. 저장소 루트에서 실행합니다.

```sh
sudo python3 tools/idc.py change-validate apply description --id description-01
sudo python3 tools/idc.py change-validate restore \
  --run-dir .runtime/idc/operations/changes/description-01
```

| 후보 | 적용 항목 | 기대 결과 |
|---|---|---|
| `description` | Leaf1 eth1의 Description | 구성 변경과 정상 상태 확인 |
| `harmless` | 미광고 시험용 /32 거부 | 정책 변경과 경로·서비스 유지 |
| `break-vtep` | Leaf2 원격 VTEP /32 거부 | 링크와 IPv4 BGP 유지, 필수 경로·서비스 실패 |

정상 변경은 `PASS`, 기준선·변경 위치에 문제가 있으면 `BLOCKED`, 실행·사후 검증 실패는 `FAIL`입니다. 후자의 두 결과는 종료 코드 1을 반환합니다. 관제가 실행 중이면 실패 요약이 Loki에 전송됩니다.

실행별 `.runtime/idc/operations/changes/<실행 ID>/`에 `before/`, `after/`, 스냅샷 JSON, `config.diff`, Ansible 로그와 `REPORT.md`를 기록합니다. [Ansible 플레이북](../../../06-change-automation/idc/apply-change.yml)

## 수동 복구

1. 실패 보고서, 설정 diff와 `before/`의 백업을 확인합니다. 실패한 변경은 작업자가 복구할 때까지 남아 있습니다.
2. 같은 랩에서 `restore --run-dir <실행 폴더>`를 실행합니다. 검증된 해당 후보의 변경만 역명령으로 제거합니다. 현재 구성이 달라졌다면 보고서의 백업과 구성을 대조합니다.
3. `RECOVERY.md`의 역명령을 직접 실행한 경우 `verify-recovery --run-dir <실행 폴더>`로 확인합니다. 두 방식 모두 원본 구성 4개와 정상 상태를 `recovery-result.json` 및 `RECOVERY-RESULT.md`에 기록합니다.
