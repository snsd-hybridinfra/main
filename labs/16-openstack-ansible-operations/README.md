# Lab 16: OpenStack Provisioning and Ansible Day-2 Operations

**Status:** `MIGRATED / NOT_REVALIDATED`. This is a sanitized, selectively extracted educational lab, not a complete replay of the prior team project.

## Question
Can OpenStack instances and volumes be provisioned through Ansible, then checked for service health, configuration consistency, and backup/restore readiness?

## Extracted components
- `ansible/provision.yml`, `ansible/vars/provisioning.yml`: OpenStack security group, VM and backup volume provisioning baseline
- `ansible/site.yml`: configuration and service-state orchestration for web, proxy, database, monitoring and backup
- `ansible/wait-ssh.yml`, `ansible/validate.yml`, `ansible/requirements.yml`: access/readiness checks
- `inventory.example.ini`: non-routable RFC 5737 documentation addresses, **not** a usable live inventory

The source's team meeting notes, personal work logs, screenshots, raw host inventory and automatic recovery scripts were **not** imported. Some source health scripts included automatic restarts/recovery and local SSH key paths; reimplement any desired behavior only after a separate failure-safe design review.

## Safety adjustments
- Uses a neutral `lab-openstack` Cloud name and example resource identifiers; `clouds.yaml` stays local.
- SSH access defaults to an unset `LAB_MANAGEMENT_CIDR` and provisioning fails until a trusted management source is supplied. An open internet SSH CIDR is rejected.
- Removed a `failed_when: false` that could conceal security-group rule creation errors.
- No actual cloud connection, backup or restore was run during the migration.

## Revalidation sequence
1. On a disposable OpenStack test tenant, supply `clouds.yaml`, image/flavor/network/key names, and trusted SSH CIDR.
2. Run static syntax checks and `ansible-galaxy collection install -r ansible/requirements.yml`.
3. Execute provisioning, check idempotence and failure behavior, then run `wait-ssh.yml`, `site.yml`, `validate.yml`.
4. Independently design a Restic backup and a **non-destructive restore test**; collect redacted evidence, recovery times and limitations.
5. Do not mark this lab validated until normal, denial, failure and recovery evidence is stored.

## Provenance and attribution
Select reusable code from the multi-author **Team Dandelion** repository `snsd-hybridinfra/dandelion-cloud-automation`, source commit `22a21c02973e696a9a07c91da3bc2ea033881ea6`. The original project, contributor history, screenshots and materials are **not** reproduced in full; preserve an independent Git mirror before deleting the source. Original teammate contributions must not be presented as solo work.

## Future combinations
Combine this provisioning/Day-2 lab with the network policy, observability, and recovery labs only after independent validation.


## Added Team Dandelion reference
`reference/ansible/ansible.cfg.reference.txt` preserves the old Ansible config as inert text. The original disabled SSH host-key checking and **must not be reused as a secure default**.
