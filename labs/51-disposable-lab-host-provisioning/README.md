# Lab 51: Disposable Lab VM and Storage Provisioning

**Status:** `SOURCE_EXTRACTED / NOT_REVALIDATED`. Five original host-level PowerShell/Bash provisioning scripts preserved as inert `.reference.txt` examples. **Do not execute on a personal or workplace host without review.**

## Role
Create repeatable disposable targets for OpenStack/AIO, Ansible Control, k3s and supply chain runners, subject to explicit safety gates.

## Included references
- `Add-CinderDiskToOpenStackAio`: storage attachment
- `New-AnsibleControlVm`: Ansible VM
- `New-IdpSupplyChainRunnerVm`: runner VM
- `New-MiniOnaK3sVm`: k3s VM
- `Initialize-ZtVis002ExternalInputs`: monitoring bootstrap prerequisites

## Revalidation
1. Audit all drives, format/partition, VM create/remove, ports and credential handling.
2. Replace fixed paths, hostnames and bridge assumptions; require named disposable VMs, no production access.
3. Require verified snapshots, approval, rollback and dry-run.
4. Test isolation and restore before declaring this executable. No source scripts were run.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops@fd5b2286a68da180fd51ecb247516c960cc7d4ef`.
