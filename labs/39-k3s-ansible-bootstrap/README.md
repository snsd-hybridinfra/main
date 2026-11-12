# Lab 39: k3s Single-Node Bootstrap via Ansible

**Status:** `SOURCE_EXTRACTED / NOT_REVALIDATED`. All eight files from the source `applications/internal-iaas-portal/ansible/` subtree were extracted.

## Question
Can a single-node k3s host be bootstrapped idempotently and securely with Ansible, then validated and rolled back without touching production infrastructure?

## Source content
- `source/playbooks/configure-k3s.yaml`
- `source/roles/k3s_single_node/`: tasks, templates, handlers and defaults
- `source/ansible.cfg`

## Tests required
1. Check Ansible syntax and collection dependencies in a container or disposable VM.
2. Audit downloaded installer hashes, service user privileges, systemd unit behavior, registry and networking defaults.
3. Apply only to a dedicated fake inventory in a disposable VM. Validate node Ready and denied workload network paths.
4. Rerun for idempotence, simulate a failed bootstrap and document a reversible teardown.
5. Never run an inherited `configure-k3s` playbook directly on a workplace host or existing cluster.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` at `fd5b2286a68da180fd51ecb247516c960cc7d4ef`.
