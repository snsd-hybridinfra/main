# Kubernetes ServiceAccount 최소 권한 Lab

## 이걸 해본 이유

[Unit 42의 Kubernetes Operator 연구(2026-09-29)](https://unit42.paloaltonetworks.com/agentic-ai-kubernetes-operator-risks/)를 읽고, Operator의 ServiceAccount가 편의 때문에 넓은 ClusterRole을 받으면 침해 범위도 그 권한만큼 커진다는 점을 확인했다. 기사에 나온 제품이나 취약점을 재현하는 대신 **“운영 자동화 계정에 필요한 조회만 주고 Secret, 삭제, 다른 Namespace 접근을 실제로 막을 수 있는가?”**를 작은 클러스터에서 시험했다.

## 내가 구성한 범위

- 상태: **로컬 런타임 검증**
- 환경: Docker Desktop, kind v0.33.0, Kubernetes v1.36.4, kubectl v1.36.1
- 주체: `rbac-lab` Namespace의 `operator-reader` ServiceAccount
- 허용: 같은 Namespace의 Pod와 Deployment `get/list/watch`
- 거부 확인: Secret 조회, Pod 삭제, 다른 Namespace Pod 조회, ClusterRole 조회

기사의 OperTraitor, IBM Turbonomic, Datadog Operator를 실행한 것은 아니다. 실제 Operator가 아니라 내가 만든 ServiceAccount·Role·RoleBinding으로 최소 권한 경계를 확인했다.

10월 4일 브리핑에서 다룬 [Dell CSM 보안 권고 DSA-2026-448](https://www.dell.com/support/kbdoc/en-us/000515771/dsa-2026-448-security-update-for-dell-container-storage-modules-multiple-vulnerabilities)(2026-10-01)는 Storage Operator와 Authorization 계층이 Cluster Node·Secret·Storage 관리자 자격증명까지 영향을 줄 수 있음을 보여 준다. 이 권고는 기존 최소 권한 질문과 연결했지만 Dell CSM은 배포하지 않았다.

[AWS 보안 공지 2026-156-AWS, CVE-2026-119115](https://aws.amazon.com/security/security-bulletins/2026-156-aws/)(2026-10-29 09:30 PDT)는 AWS Private CA Connector for Kubernetes 1.10.1 미만에서 Namespace Issuer만 승인된 사용자가 조건에 따라 Cluster Issuer로 인증서를 발급받을 수 있었음을 설명한다. 기존 RBAC 런타임 결과는 그대로 두고, Issuer의 이름뿐 아니라 `kind`와 Namespace가 모두 맞아야 허용하는 작은 정책 판정을 추가했다.

## 권한 구조

```text
operator-reader ServiceAccount
              │ RoleBinding
              ▼
workload-observer Role (rbac-lab Namespace)
              ├─ Pod get/list/watch
              └─ Deployment get/list/watch

Secret / delete / other-team / ClusterRole
              └─ 권한 없음
```

[적용한 Manifest](manifests/rbac-lab.yaml)는 `Role`을 사용한다. Cluster 전체를 열어야 하는 `ClusterRoleBinding`은 만들지 않았다.

## 실행 방법

kind 실행 파일이 PATH에 있으면:

```powershell
cd F:\main\labs\role-groups\04-security-trust\experiments\kubernetes-rbac
.\run.ps1
```

별도 위치에 있으면:

```powershell
.\run.ps1 -KindPath "$env:TEMP\codex-tools\kind-v0.33.0.exe"
```

스크립트는 Digest로 고정한 kind Node Image로 임시 클러스터를 만들고 Manifest를 적용한 뒤 `kubectl auth can-i --as=system:serviceaccount:rbac-lab:operator-reader`를 실행한다. 검증이 끝나면 클러스터와 임시 kubeconfig를 지운다. 조사 목적으로 남길 때만 `-KeepCluster`를 사용한다.

Issuer 경계의 합성 정책 판정은 Cluster 없이 실행한다.

```powershell
python .\validate_issuer_boundary.py --input .\issuer-boundary-cases.json --evidence .\evidence\2026-11-14-issuer-boundary.json
```

## 직접 돌려본 결과

[2026-09-30 실행 증적](evidence/2026-09-30.json):

| 확인 | 기대 | 실제 |
|---|---|---|
| 같은 Namespace Pod 조회 | 허용 | `yes` |
| 같은 Namespace Deployment 목록 | 허용 | `yes` |
| Secret 조회 | 거부 | `no` |
| Pod 삭제 | 거부 | `no` |
| `other-team` Namespace Pod 목록 | 거부 | `no` |
| ClusterRole 조회 | 거부 | `no` |

6개가 모두 기대와 일치했다. “조회가 된다”만 확인하지 않고, 자동화 계정이 Secret과 삭제 권한을 얻지 않았고 Namespace 밖으로 나가지 못하는 것도 같이 확인했다.

## Issuer 이름·종류·Namespace를 함께 본 결과

[2026-11-14 Issuer 경계 판정 증적](evidence/2026-11-14-issuer-boundary.json)에서는 정확한 `AWSPCAIssuer/team-issuer` 한 건만 허용했다. 같은 이름의 `AWSPCAClusterIssuer`, 승인되지 않은 Cluster Issuer, `kind` 누락, 일반 `Issuer`, 다른 Namespace 요청 5건은 거부됐다.

이 결과는 내가 만든 합성 Approval Policy의 6/6 판정이다. AWS Private CA Connector, cert-manager, 실제 CertificateRequest, 하위 CA 발급, 1.10.1 Upgrade와 인증서 갱신은 실행하지 않았다. 기존 2026-09-30 증적만 kind Runtime에서 실행한 RBAC 검증이다.

## 남은 점

- 실제 Operator, CRD, Controller Image, Helm Chart, Dell CSM과 AWS Private CA Connector는 배포하지 않았다.
- Admission Policy, NetworkPolicy, Audit Log, ServiceAccount Token 회전은 확인하지 않았다.
- `kubectl --as`를 사용할 수 있는 로컬 관리자 자격으로 권한을 질의했다. 운영 클러스터 사용자의 권한 모델을 검증한 결과는 아니다.
- 이 결과는 임시 kind 클러스터의 로컬 런타임 검증이다. `snsd-multicloud-ops`의 k3s PaaS에 적용되었다는 뜻은 아니다.

## 다음에 이어서 할 일

1. 실제 Operator Manifest를 받아 wildcard와 Secret 접근을 배포 전에 검사한다.
2. 허용된 동작과 거부된 동작을 Kubernetes Audit Log에서 대조한다.
3. `snsd-multicloud-ops`에 적용하려면 해당 프로젝트의 권위 문서와 k3s 런타임에서 별도 검증한다.
