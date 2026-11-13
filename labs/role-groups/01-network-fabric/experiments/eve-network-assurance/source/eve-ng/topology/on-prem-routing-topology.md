# EVE-NG On-Prem Routing Topology

This document is a repository-side, non-production routing model. It contains no live EVE-NG export, real addressing, device credentials, or organization-specific network data.

## Zones

| Zone | Placeholder CIDR | Purpose |
|---|---|---|
| Management Zone | `<management-cidr>` | Administrative access and control-plane operations |
| Bastion Zone | `<bastion-cidr>` | Controlled administrative transit through `bastion-host-01` |
| Transit Zone | `<transit-cidr>` | Inter-router routing exchange |
| Internal Server Zone | `<internal-server-cidr>` | Protected internal service workloads |
| Monitoring Zone | `<monitoring-cidr>` | Monitoring and observability services |

## Placeholder Devices

| Device | Role | Connected Zones |
|---|---|---|
| `mgmt-router-01` | Management routing boundary | Management Zone, Transit Zone |
| `transit-router-01` | Central routing exchange | Transit Zone and all routed zone paths |
| `internal-router-01` | Internal server routing boundary | Internal Server Zone, Transit Zone |
| `monitoring-router-01` | Monitoring routing boundary | Monitoring Zone, Transit Zone |
| `bastion-host-01` | Controlled administrative hop | Bastion Zone |

## Logical Routing Flow

```text
Management Zone (<management-cidr>)
  -> mgmt-router-01
  -> Transit Zone (<transit-cidr>)
  -> transit-router-01
     -> Bastion Zone (<bastion-cidr>) -> bastion-host-01
     -> Internal Server Zone (<internal-server-cidr>) -> internal-router-01
     -> Monitoring Zone (<monitoring-cidr>) -> monitoring-router-01
```

## Validation Boundary

retired-numbered-case validates this topology document and the matching example router configurations as repository artifacts. It does not authenticate to EVE-NG, connect to network devices, test live reachability, or validate cloud connectivity.
