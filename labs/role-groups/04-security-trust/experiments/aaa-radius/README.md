# 06 AAA / RADIUS: 승인·거부 정책 확인

## 이걸 해본 이유

[Cisco ISE RADIUS 서비스 거부 권고(2026-09-16)](https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-ise-RADIUS-dos-wR3hYPMw)를 보고, 취약점 재현보다 먼저 RADIUS의 기본 판정을 직접 확인하기로 했다. **등록된 계정만 통과하고 잘못된 비밀번호와 미등록 계정은 거부되는가?**가 이번 질문이다. Cisco ISE와 권고의 서비스 거부 문제는 시험하지 않았다.

FreeRADIUS 3.2.10 컨테이너와 `radtest`를 같은 네트워크 네임스페이스에서 실행했다. 우선 서버 판정만 봤고 스위치나 VPN 로그인까지 연결하지는 않았다.

## 확인하려던 것

등록된 관리 계정의 올바른 비밀번호만 RADIUS 인증을 통과하는가? 틀린 비밀번호나 미등록 계정은 거부되는가?

## 실습 구성

- [`run-lab.sh`](run-lab.sh)가 실행 때 무작위 테스트 비밀번호와 RADIUS 공유 비밀을 생성한다.
- 임시 `clients.conf`에는 `127.0.0.1` 클라이언트만 지정한다.
- 임시 `authorize`에는 합성 `lab-admin` 계정만 포함한다.
- 컨테이너는 `--network none`으로 실행하며 포트를 호스트에 게시하지 않는다.
- 실행 종료 시 컨테이너와 임시 설정을 삭제한다. 설정의 비밀번호·공유 비밀은 Git 증적에 포함하지 않는다.

공식 이미지 `freeradius/freeradius-server:3.2.10-alpine`를 `sha256:91acbee4a1f532e3a266ae3d7f153a5cf21f5faa9bc14116d5d1fe2c2a746c27`로 고정했다.

## 실행

WSL2 Ubuntu에서 Docker Engine이 실행 중이어야 한다.

```bash
bash labs/role-groups/04-security-trust/experiments/aaa-radius/run-lab.sh
```

## 직접 확인한 결과

[2026-09-22 정제 결과](evidence/2026-09-22.txt):

| 요청 | 기대 | 실제 |
|---|---|---|
| 등록된 계정·올바른 비밀번호 | Access-Accept | Access-Accept |
| 등록된 계정·틀린 비밀번호 | Access-Reject | Access-Reject |
| 미등록 계정 | Access-Reject | Access-Reject |

실제 네트워크 장비의 관리 접근 제어, RADIUS 클라이언트 IP 제한, TLS 터널, 계정 잠금, MFA, 회계(Accounting) 기록은 검증하지 않았다. 이 결과는 서버 측 인증 판정만 보여준다. 서브 프로젝트에서 AAA를 붙일 때는 NAS 장비와 실제 관리 경로에서 재검증해야 한다.

## 참고한 문서

- [FreeRADIUS Basic Configuration HOWTO](https://wiki.freeradius.org/guide/Basic-configuration-HOWTO)
- [FreeRADIUS radtest 매뉴얼](https://www.freeradius.org/radiusd/man/radtest.html)
- [공식 FreeRADIUS 컨테이너 이미지](https://hub.docker.com/r/freeradius/freeradius-server/tags)
