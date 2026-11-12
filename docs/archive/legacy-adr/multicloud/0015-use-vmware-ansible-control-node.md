# ADR 0015: Use a dedicated VMware Ansible control node

- Status: Accepted
- Date: 2026-08-20
- Scope: P2-VIS-001 local control-plane preparation

## Context

The laboratory runs EVE-NG and OpenStack AIO on VMware Workstation and depends
on direct hardware virtualization. Enabling the Windows hypervisor for WSL2
would place VMware behind the Windows hypervisor and constrain the nested
virtualization required by the laboratory. A temporary WSL1 control-node
candidate proved Ansible syntax compatibility, but the operator selected a
dedicated VM and prohibited WSL as the active project control node.

## Decision

Use one dedicated Ubuntu 24.04 VMware Workstation VM as the local Ansible
control node. The reviewed configuration is bounded to two vCPUs, 4096 MB of
memory, a 30 GB thin disk, VMnet8 NAT for package access, and VMnet1 host-only
for laboratory reachability. Bridged networking, public listeners, shared
folders, password authentication, and root SSH are prohibited.

The VM is created from Canonical's released Ubuntu 24.04 VMware image after
checking SHA-256
`b9dc4dea4bdb09c1e08e40cce34fbd3d8fe252ff71bd9be979ef8b15256d80e8`.
Cloud-init creates a non-administrative SSH-key-only user with a bounded local
sudo command list, installs Ansible Core, applies a default-deny inbound
firewall, and permits SSH only from the two private VMware subnets. Private
keys, DHCP addresses, MAC addresses, VMX files, disks, and raw runtime output
remain outside Git.

WSL distributions are not control-node authorities and remain stopped. Their
deletion requires a separate explicit decision because they may contain local
data unrelated to this package.

## Consequences

- VMware retains direct hardware virtualization for EVE-NG and OpenStack AIO.
- The Ansible control node has stable isolation and both NAT and host-only
  reachability without a bridged or public interface.
- Terraform remains installed on the Windows workstation; no OpenStack plan or
  apply is authorized by this decision.
- The control VM is local infrastructure, not central visibility deployment or
  package runtime acceptance.
- Final VM removal is the rollback action and is not tested while the control
  node is required. A failed first-boot candidate was stopped and removed from
  the exact reviewed VM path before successful recreation.

## Validation

The accepted VM passed cloud-init completion, public-key SSH, local Ansible
ping, deployment and rollback syntax checks, root/keyless/general-sudo denial,
private firewall checks, dual-NIC checks, and a full stop/start persistence
cycle. Sanitized results are recorded in
`docs/evidence/zero-trust/zt-vis-002-control-node.sanitized.json`.
