# ZT-NET-001 Restricted Router Validation and Network Policy Evidence

## Purpose and status

ZT-NET-001 provides a deterministic, read-only validation path from the local
workstation to SNSD-R1 and one explicitly approved persistent directional ACL.
The package is IMPLEMENTED and VALIDATED for this bounded scope. Final live
execution returned 39 PASS, 0 WARN, and 0 FAIL. Current maturity remains
UNASSESSED; the maximum proposed target is INITIAL.

The named ACL is bound inbound on the DMZ subinterface, denies DMZ-originated
traffic to the Kubernetes subnet, permits the remaining expected DMZ traffic,
and denies unmatched or spoofed input. Running and startup persistence,
allow/deny behavior, counters, and both fixed OpenStack paths passed. The
classification is `BOUNDED_INTERZONE_ACL_VALIDATED`, not complete
micro-segmentation.

## Capability mappings

The bounded package maps to ZT-3.1.1 macro segmentation, ZT-3.4.1 data-flow
mapping, ZT-4.1.1 access control, ZT-4.3.1 network segmentation and group
movement, ZT-7.1 relevant activity recording, and ZT-8.2 critical-process
automation. These mappings do not establish capability-wide implementation or
maturity.

## Transport selection

Direct Cisco SSH was rejected because no existing secure non-interactive,
restricted privilege path was available without router configuration changes.
The selected path uses a separate EVE-NG account and dedicated key outside Git.

~~~mermaid
flowchart LR
  A["Local Codex"] --> B["Dedicated SSH alias"]
  B --> C["Forced-command EVE account"]
  C --> D["Root-owned fixed validator"]
  D --> E["SNSD-R1 console"]
~~~

The dispatcher accepts only validate-routing. It denies an empty command,
arbitrary commands, configuration requests, and caller-controlled ping targets.
The sudoers rule grants only the fixed root-owned validator.

## Router command allowlist

The validator uses session-only pagination control and fixed read-only commands
for clock, version, hostname, interfaces, routes, routing protocols, NAT,
access lists, and filtered running-configuration sections. Two fixed reachability
targets are rendered into the root-owned remote validator during installation.
The caller cannot supply commands or target addresses.

## Validation interpretation

- Identity: expected hostname, IOS family, clock, and uptime passed.
- Interfaces: WAN, trunk, and VLAN 20/30/40/50/60/70 subinterfaces passed.
- Routing: six connected networks and the default route passed.
- NAT: inside/outside roles, overload rule, ACL reference, statistics, and
  active translations passed.
- ACL: NAT ACL 10 remains readable; the package-owned directional ACL is bound
  inbound and persists in startup configuration.
- Segmentation: BOUNDED_INTERZONE_ACL_VALIDATED; broader multi-zone policy
  coverage is not claimed.
- Provider path: fixed router-external and Floating IP targets returned complete
  reachability from the router.

~~~mermaid
flowchart LR
  R["SNSD-R1"] --> V["VLAN 70"]
  V --> P["OpenStack provider interface"]
  P --> X["br-ex"]
  X --> N["Neutron router"]
  N --> F["Floating IP"]
  F --> T["Tenant instance"]
~~~

Only the router-observable part is directly proven here. Tenant egress remains
cross-referenced to the restricted OpenStack validation record.

## Evidence flow

~~~mermaid
flowchart LR
  V["Fixed validator"] --> R["Ignored raw runtime"]
  R --> S["Sanitizer"]
  S --> E["Reviewed sanitized evidence"]
  E --> M["Machine-readable record"]
~~~

Raw output remains below .runtime/zero-trust/router/ and is ignored by Git. The
committed record omits runtime addresses, console ports, MAC addresses, hardware
serials, credentials, and proprietary image details.

## Limitations and remaining boundary

The legacy IOS platform is a bounded lab component. This package does not
establish software-defined networking, dynamic policy, continuous adaptive
access, traffic encryption, full resilience, or enterprise-wide Zero Trust.
Any broader policy coverage still requires a separately approved design,
change, rollback plan, and post-change live evidence.

Rollback is documented in
[zt-net-001-rollback.md](zt-net-001-rollback.md).
