# 12 AI Multi-Region Data Path: Hub 원본과 Spoke 캐시

## 왜 이 구조를 시험했는가

[AWS의 SageMaker HyperPod·Qumulo Multi-Region 학습 글](https://aws.amazon.com/blogs/machine-learning/multi-region-training-with-amazon-sagemaker-hyperpod-and-qumulo/)(2026-09-25)은 GPU가 있는 Region과 원본 데이터가 있는 Region이 다를 때 생기는 지연과 복제 부담을 다룬다.

기사 구조를 그대로 배포하려면 AWS 두 Region, Qumulo와 HyperPod가 필요하다. 먼저 비용이 들지 않는 로컬 환경에서 **원본을 한 곳에 두고 필요한 파일만 캐시하면 첫 읽기와 반복 읽기가 어떻게 달라지는가?**를 확인했다.

이 랩은 AWS 구현이 아니라 실제 파일 복사와 해시 검증을 사용하는 **로컬 검증**이다.

## 기사에서 가져온 구조와 내 실험

```text
기사 구조
Qumulo Hub ── Region 간 경로 ──> Qumulo Spoke Cache ── NFS ──> HyperPod

로컬 실험
Hub directory ── 60 ms/파일 지연 ──> Spoke cache directory ──> Reader
```

기사의 Hub·Spoke 관계를 로컬 디렉터리 두 개로 줄였다. Cold Epoch에는 Spoke에 없는 파일을 Hub에서 복사하고, Warm Epoch에는 같은 파일을 캐시에서 읽는다. 모든 파일은 SHA-256으로 원본과 일치하는지 확인한다.

60 ms는 실제 WAN 측정값이 아니라 Cold Fetch마다 넣은 **지연 모델**이다. 이 결과를 AWS Region 간 성능이나 Qumulo 성능으로 해석하지 않는다.

## 실행

```powershell
./run.ps1
```

[cache_path.py](cache_path.py)는 512 KiB 합성 Shard 8개, 총 4 MiB를 임시 Hub에 만든다. 실행이 끝나면 Hub와 Cache 디렉터리를 삭제하고 정제된 JSON만 남긴다.

## 직접 확인한 결과

2026-10-06 재실행의 [JSON 증적](evidence/2026-10-06.json):

| 단계 | Cache Hit | Cache Miss | Hub 요청 | 무결성 실패 | 복구 | 해시 확인 |
|---|---:|---:|---:|---:|---:|---:|
| Cold Epoch | 0 | 8 | 8 | 0 | 0 | 8/8 |
| Warm Epoch | 8 | 0 | 0 | 0 | 0 | 8/8 |
| 손상 복구 | 7 | 0 | 1 | 1 | 1 | 8/8 |
| 복구 후 재확인 | 8 | 0 | 0 | 0 | 0 | 8/8 |

Cold Epoch는 파일마다 모델링한 지연과 Hub 복사를 거쳤고, Warm Epoch는 Hub를 다시 호출하지 않았다. Warm Epoch가 Cold Epoch보다 빨랐으며 이 차이는 실제 WAN·NFS 처리량이 아니라 로컬 캐시와 주입한 지연의 결과다.

실패 경로에서는 캐시의 첫 Shard를 고의로 바꿨다. 읽기 전에 SHA-256 불일치를 찾았고, 그 파일만 Hub에서 다시 가져왔다. 같은 Epoch의 8개 파일이 모두 원본 해시와 일치했으며, 바로 다음 Epoch에서는 8개 전부 Cache Hit로 돌아와 Hub 요청이 0건이었다.

이전 [2026-09-29 증적](evidence/2026-09-29.json)은 손상 감지만 확인한 최초 실행 기록으로 남겼다.

## 기사 수치와 내 결과 구분

AWS 글은 별도 환경에서 Cold Cache Warm-up, 94~96% Cache Hit Rate와 115~116 samples/sec를 설명한다. 이 수치는 AWS와 Qumulo의 기사 결과이며 내 측정값이 아니다.

내가 확인한 것은 다음 범위다.

- Cold 읽기에서 Hub 요청과 Cache Miss가 발생하는 흐름
- Warm 읽기에서 Hub 요청 없이 Cache Hit가 발생하는 흐름
- 원본과 캐시의 파일 해시 일치
- 캐시 훼손을 해시로 감지하는 실패 경로
- 손상된 파일 하나만 Hub에서 다시 가져오는 복구 경로
- 복구 후 전체 Cache Hit와 Hub 요청 0건으로 돌아오는 재검증

## 확인하지 않은 범위

- AWS Region, VPC Peering, Route Table, Security Group
- Qumulo Hub·Spoke, Cloud Data Fabric, NVMe Cache
- NFS TCP 2049와 SageMaker HyperPod
- 실제 WAN RTT·처리량, Prefetch, GPU Utilization과 비용
- 동시 Reader, 부분 쓰기, 복구 중 Hub 장애

다음 단계는 비용 한도를 정한 AWS 테스트 계정에서 작은 Dataset과 CPU Reader로 VPC 경로와 NFS를 먼저 확인한 뒤, 별도 승인을 거쳐 Qumulo·HyperPod 검증으로 확장하는 것이다.
