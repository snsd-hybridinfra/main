# 네트워크·인프라 운영 포트폴리오

금융권 IDC 네트워크 운영 경험을 바탕으로 경로 검증, 장애 대응, 변경 원복을 가상 환경에서 재현합니다.

## IDC Network Operations & Resilience Lab

Spine 2대·Leaf 2대·Host 2대로 eBGP와 EVPN/VXLAN 패브릭을 구성하고, 격리된 FRRouting 환경에서 장애 5종을 검증했습니다.

**대표 사례 · 라우팅 정책 장애**

링크와 IPv4 BGP 이웃이 정상인 상태에서 수신 정책으로 원격 VTEP 경로가 사라졌습니다. 포워딩 테이블(FIB)과 설정 변경을 대조해 원인을 확인했고, 원복 명령 후 HTTP가 **약 0.62초** 만에 회복됐습니다.

- **장애 상관분석** · 포트와 BGP 이벤트를 링크별 사건으로 묶고 최근 변경을 함께 확인합니다.
- **변경 검증** · Ansible 적용 전후의 경로·서비스를 비교하고, 실패 시 수동 복구 절차를 제공합니다.
- **인벤토리** · NetBox에 장비·포트·케이블·회선을 등록하고 반복 적용을 확인했습니다.

[설계와 토폴로지](labs/role-groups/01-network-fabric/idc/architecture.md) · [실측 보고서](labs/role-groups/01-network-fabric/idc/docs/results.md) · [실습 따라 하기](labs/role-groups/01-network-fabric/idc/README.md)

## 더 보기

[전체 실습 카탈로그 · 7개 역할 랩과 51개 번호 랩](labs/role-groups/README.md)
